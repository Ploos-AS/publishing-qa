from __future__ import annotations

from .base import JSONReviewerAdapter


class OpenAIAdapter(JSONReviewerAdapter):
    provider = "openai"


class AnthropicAdapter(JSONReviewerAdapter):
    provider = "anthropic"


class GoogleAdapter(JSONReviewerAdapter):
    provider = "google"


class MistralAdapter(JSONReviewerAdapter):
    provider = "mistral"


def register_builtin_providers(registry, transports, models, output_schema):
    classes = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "google": GoogleAdapter,
        "mistral": MistralAdapter,
    }
    for provider, cls in classes.items():
        if provider not in transports:
            continue
        registry.register(
            provider,
            lambda _cls=cls, _provider=provider, **kwargs: _cls(
                transport=transports[_provider],
                model=kwargs.get("model", models[_provider]),
                output_schema=output_schema,
            ),
        )
