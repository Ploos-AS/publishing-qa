from __future__ import annotations

import time
from typing import Any

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
        elapsed_ms = round((time.monotonic() - started) * 1000)
        return {
            "provider": provider,
            "model": model,
            "qualified": isinstance(response.findings, tuple),
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
            "error": f"{type(exc).__name__}: {exc}",
        }


def qualification_complete(results: list[dict[str, Any]], required: list[str]) -> bool:
    passed = {r["provider"] for r in results if r.get("qualified")}
    return all(provider in passed for provider in required)
