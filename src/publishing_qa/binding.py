from __future__ import annotations

import fnmatch
from typing import Any


def binding_matches(binding: dict[str, Any], finding: dict[str, Any]) -> bool:
    match = binding.get("match", {})
    if "finding_id" in match and finding.get("finding_id") != match["finding_id"]:
        return False
    if "category" in match and finding.get("category") not in _as_list(match["category"]):
        return False
    if "file" in match:
        path = finding.get("file") or ""
        if not any(fnmatch.fnmatch(path, pattern) for pattern in _as_list(match["file"])):
            return False
    if "claim_id" in match and finding.get("claim_id") != match["claim_id"]:
        return False
    return bool(match)


def _as_list(value):
    return value if isinstance(value, list) else [value]


def select_producers(finding: dict[str, Any], bindings: list[dict[str, Any]]) -> list[str]:
    selected = []
    for binding in bindings:
        if binding_matches(binding, finding):
            selected.extend(_as_list(binding.get("producers", [])))
    return list(dict.fromkeys(selected))


def validate_bindings(bindings: list[dict[str, Any]], producer_ids: set[str]) -> list[str]:
    errors = []
    for index, binding in enumerate(bindings):
        match = binding.get("match")
        producers = _as_list(binding.get("producers", []))
        if not isinstance(match, dict) or not match:
            errors.append(f"binding[{index}] must have a non-empty match")
        if not producers:
            errors.append(f"binding[{index}] must reference at least one producer")
        for producer in producers:
            if producer not in producer_ids:
                errors.append(f"binding[{index}] references unknown producer: {producer}")
    return errors
