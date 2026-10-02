from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .normalize import normalize_and_validate
from .review import AdapterRegistry, ReviewDocument, ReviewRequest
from .package import source_digest
from .qualification import _safe_error


def reviewer_specs(config: dict[str, Any]):
    reviewers = config.get("ai", {}).get("reviewers", {})
    if isinstance(reviewers, list):  # compatibility with early M1 config
        return [(dict(id=item, roles=["independent"]), True) for item in reviewers]
    required = [(item, True) for item in reviewers.get("required", [])]
    supplemental = [(item, False) for item in reviewers.get("supplemental", [])]
    return required + supplemental


def run_reviews(
    *,
    project: str,
    config: dict[str, Any],
    documents: tuple[ReviewDocument, ...],
    registry: AdapterRegistry,
    schema_path: Path,
    adapter_options: dict[str, dict[str, Any]] | None = None,
    instructions: str = "",
    context: dict[str, Any] | None = None,
    audit_full_content: bool = False,
):
    adapter_options = adapter_options or {}
    context = context or {}
    normalized = []
    audit = []
    required_failures = []
    digest = source_digest(documents)

    for spec, required in reviewer_specs(config):
        reviewer_id = spec["id"]
        provider = spec.get("provider", reviewer_id)
        request = ReviewRequest(
            project=project,
            reviewer_id=reviewer_id,
            roles=tuple(spec.get("roles", ["independent"])),
            documents=documents,
            instructions=instructions,
            context=dict(context),
        )
        request_audit = {
            "project": request.project,
            "reviewer_id": request.reviewer_id,
            "roles": list(request.roles),
            "instructions": request.instructions,
            "context": dict(request.context),
            "source_digest": digest,
            "documents": [
                {"path": d.path, "language": d.language, "size_bytes": len(d.content.encode("utf-8"))}
                for d in request.documents
            ],
        }
        if audit_full_content:
            request_audit = asdict(request)
            request_audit["source_digest"] = digest
        entry = {
            "reviewer_id": reviewer_id,
            "provider": provider,
            "required": required,
            "request": request_audit,
        }
        try:
            adapter = registry.create(provider, **adapter_options.get(provider, {}))
            response = adapter.review(request)
            items = normalize_and_validate(response.findings, reviewer_id, schema_path)
            normalized.extend(items)
            entry["status"] = "success"
            entry["response"] = (
                asdict(response) if audit_full_content else {
                    "reviewer_id": response.reviewer_id,
                    "provider": response.provider,
                    "model": response.model,
                    "finding_count": len(response.findings),
                    "notes_present": bool(response.notes),
                }
            )
            entry["normalized_findings"] = items
        except Exception as exc:
            entry["status"] = "failed"
            entry["error"] = _safe_error(exc)
            if required:
                required_failures.append(reviewer_id)
        audit.append(entry)

    return {
        "format_version": 1,
        "project": project,
        "source_digest": digest,
        "findings": normalized,
        "reviewers": audit,
        "required_failures": required_failures,
        "complete": not required_failures,
    }
