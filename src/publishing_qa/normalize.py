from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ALIASES = {
    "warning": "medium",
    "error": "high",
    "fatal": "critical",
    "documentation": "language",
    "editorial": "language",
    "factual": "fact",
}


def normalize_finding(raw: dict[str, Any], reviewer_id: str, index: int) -> dict[str, Any]:
    severity = str(raw.get("severity", "medium")).lower()
    category = str(raw.get("category", "consistency")).lower()
    severity = ALIASES.get(severity, severity)
    category = ALIASES.get(category, category)

    return {
        "finding_id": raw.get("finding_id") or f"{reviewer_id.upper()}-{index:04d}",
        "severity": severity,
        "category": category,
        "file": raw.get("file"),
        "line": raw.get("line"),
        "claim": raw.get("claim"),
        "claim_id": raw.get("claim_id"),
        "problem": str(raw.get("problem", "")).strip(),
        "suggested_fix": raw.get("suggested_fix"),
        "confidence": float(raw.get("confidence", 0.5)),
        "requires_verification": bool(raw.get("requires_verification", category in {"fact", "code"})),
        "verification_status": raw.get("verification_status", "unverified"),
        "reviewer": reviewer_id,
    }


def normalize_and_validate(findings, reviewer_id: str, schema_path: Path):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    result = []
    for index, raw in enumerate(findings, 1):
        item = normalize_finding(raw, reviewer_id, index)
        errors = sorted(validator.iter_errors(item), key=lambda e: list(e.path))
        if errors:
            raise ValueError(f"Invalid finding from {reviewer_id}: {errors[0].message}")
        result.append(item)
    return result
