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


VALID_SUPPORTS = {"confirm", "dispute", "context"}


def validate_producers(producers: list[dict[str, Any]]) -> list[str]:
    errors = []
    seen = set()
    for index, producer in enumerate(producers):
        producer_id = producer.get("id")
        if not producer_id:
            errors.append(f"producer[{index}] must have an id")
        elif producer_id in seen:
            errors.append(f"producer[{index}] duplicates producer id: {producer_id}")
        else:
            seen.add(producer_id)
        if not producer.get("type"):
            errors.append(f"producer[{index}] must have a type")
        if not producer.get("command"):
            errors.append(f"producer[{index}] must have a command")
        for field in ("supports_on_success", "supports_on_failure", "supports_on_timeout"):
            value = producer.get(field, "context" if field == "supports_on_timeout" else ("confirm" if field == "supports_on_success" else "dispute"))
            if value not in VALID_SUPPORTS:
                errors.append(f"producer[{index}].{field} must be one of: confirm, dispute, context")
    return errors
