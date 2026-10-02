from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ReviewDocument:
    path: str
    content: str
    language: str | None = None


@dataclass(frozen=True)
class ReviewRequest:
    project: str
    reviewer_id: str
    roles: tuple[str, ...]
    documents: tuple[ReviewDocument, ...]
    instructions: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewResponse:
    reviewer_id: str
    provider: str
    model: str
    findings: tuple[dict[str, Any], ...]
    notes: str = ""


class ReviewerAdapter(Protocol):
    provider: str

    def review(self, request: ReviewRequest) -> ReviewResponse:
        """Run one independent first-pass review."""
        ...


class AdapterRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Any] = {}

    def register(self, provider: str, factory: Any) -> None:
        if provider in self._factories:
            raise ValueError(f"Adapter already registered: {provider}")
        self._factories[provider] = factory

    def create(self, provider: str, **kwargs: Any) -> ReviewerAdapter:
        try:
            factory = self._factories[provider]
        except KeyError as exc:
            raise KeyError(f"No reviewer adapter registered for: {provider}") from exc
        return factory(**kwargs)

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))
