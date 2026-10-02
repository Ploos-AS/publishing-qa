from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from .normalize import normalize_and_validate

from .review import ReviewDocument, ReviewRequest


def qualify_provider(*, provider: str, adapter, model: str) -> dict[str, Any]:
    request = ReviewRequest(
        project="publishing-qa-provider-qualification",
        reviewer_id=f"qualification-{provider}",
        roles=("technical",),
        documents=(ReviewDocument("qualification.md", "# Qualification\n\n2 + 2 = 4.\n", "en"),),
        instructions="Return zero findings if the supplied statement is correct.",
    )
    started = time.monotonic()
    try:
        response = adapter.review(request)
        schema_path = Path(__file__).resolve().parents[2] / "schema" / "finding.schema.json"
        normalized = normalize_and_validate(response.findings, request.reviewer_id, schema_path)
        elapsed_ms = round((time.monotonic() - started) * 1000)
        return {
            "provider": provider,
            "model": model,
            "qualified": isinstance(response.findings, tuple) and isinstance(normalized, list),
            "structured_output": True,
            "latency_ms": elapsed_ms,
            "error": None,
        }
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        return {
            "provider": provider,
            "model": model,
            "qualified": False,
            "structured_output": False,
            "latency_ms": elapsed_ms,
            "error": _safe_error(exc),
        }


def qualification_complete(results: list[dict[str, Any]], required: list[str]) -> bool:
    passed = {r["provider"] for r in results if r.get("qualified")}
    return all(provider in passed for provider in required)


_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|authorization|bearer|token|secret|password)\\s*[:=]\\s*[^\\s,;]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
)


def _safe_error(exc: Exception) -> str:
    message = str(exc).replace("\n", " ").replace("\r", " ")
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub("[REDACTED]", message)
    message = message[:240]
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__
