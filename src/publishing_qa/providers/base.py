from __future__ import annotations

import json
from typing import Any, Protocol

from ..review import ReviewRequest, ReviewResponse


class ProviderTransport(Protocol):
    def generate_json(self, *, model: str, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        ...


def build_review_prompt(request: ReviewRequest) -> str:
    docs = []
    for doc in request.documents:
        docs.append(f"<document path={json.dumps(doc.path)} language={json.dumps(doc.language)}>\n{doc.content}\n</document>")
    return "\n\n".join([
        f"Project: {request.project}",
        f"Reviewer: {request.reviewer_id}",
        "Roles: " + ", ".join(request.roles),
        request.instructions,
        "Review independently. Return only findings supported by the supplied material. "
        "Do not infer that another reviewer agrees. Facts and code claims should request verification.",
        *docs,
    ])


class JSONReviewerAdapter:
    provider = "generic"

    def __init__(self, *, transport: ProviderTransport, model: str, output_schema: dict[str, Any]):
        self.transport = transport
        self.model = model
        self.output_schema = output_schema

    def review(self, request: ReviewRequest) -> ReviewResponse:
        payload = self.transport.generate_json(
            model=self.model,
            system="You are an independent publishing quality reviewer. Follow the requested roles and JSON schema.",
            prompt=build_review_prompt(request),
            schema=self.output_schema,
        )
        findings = payload.get("findings")
        if not isinstance(findings, list):
            raise ValueError("Provider response must contain a findings array")
        return ReviewResponse(
            reviewer_id=request.reviewer_id,
            provider=self.provider,
            model=self.model,
            findings=tuple(findings),
            notes=str(payload.get("notes", "")),
        )
