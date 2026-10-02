from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .normalize import normalize_and_validate
from .review import AdapterRegistry, ReviewDocument, ReviewRequest
from .package import source_digest


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
):
    adapter_options = adapter_options or {}
    context = context or {}
    normalized = []
    audit = []
    required_failures = []

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
        entry = {
            "reviewer_id": reviewer_id,
            "provider": provider,
            "required": required,
            "request": asdict(request),
        }
        try:
            adapter = registry.create(provider, **adapter_options.get(provider, {}))
            response = adapter.review(request)
            items = normalize_and_validate(response.findings, reviewer_id, schema_path)
            normalized.extend(items)
            entry["status"] = "success"
            entry["response"] = asdict(response)
            entry["normalized_findings"] = items
        except Exception as exc:
            entry["status"] = "failed"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            if required:
                required_failures.append(reviewer_id)
        audit.append(entry)

    return {
        "format_version": 1,
        "project": project,
        "source_digest": source_digest(documents),
        "findings": normalized,
        "reviewers": audit,
        "required_failures": required_failures,
        "complete": not required_failures,
    }
