from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from .evidence import verification_from_evidence


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return set(re.findall(r"[a-z0-9_]+", value.lower()))


def similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    if a.get("category") != b.get("category"):
        return 0.0
    if a.get("file") and b.get("file") and a["file"] != b["file"]:
        return 0.0
    ta = _tokens(a.get("problem")) | _tokens(a.get("claim"))
    tb = _tokens(b.get("problem")) | _tokens(b.get("claim"))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def group_findings(findings: list[dict[str, Any]], threshold: float = 0.55):
    groups: list[list[dict[str, Any]]] = []
    for item in findings:
        placed = False
        for group in groups:
            if max(similarity(item, existing) for existing in group) >= threshold:
                group.append(item)
                placed = True
                break
        if not placed:
            groups.append([item])
    return groups


def summarize_groups(findings: list[dict[str, Any]], threshold: float = 0.55):
    summaries = []
    for index, group in enumerate(group_findings(findings, threshold), 1):
        reviewers = sorted({x.get("reviewer") for x in group if x.get("reviewer")})
        severities = [x["severity"] for x in group]
        summaries.append({
            "consensus_id": f"CON-{index:04d}",
            "category": group[0]["category"],
            "file": group[0].get("file"),
            "reviewers": reviewers,
            "agreement_count": len(reviewers),
            "finding_ids": [x["finding_id"] for x in group],
            "reported_severities": severities,
            "requires_verification": any(x.get("requires_verification", False) for x in group),
            "verification_status": "unverified",
        })
    return summaries


def apply_verification(consensus: dict[str, Any], status: str | None = None, evidence: list[dict] | None = None):
    evidence = list(evidence or [])
    derived = verification_from_evidence(evidence, consensus.get("requires_verification", True))
    if status is not None and status != derived:
        raise ValueError(f"Requested status {status} conflicts with evidence-derived status {derived}")
    result = dict(consensus)
    result["verification_status"] = derived
    result["evidence"] = evidence
    return result
