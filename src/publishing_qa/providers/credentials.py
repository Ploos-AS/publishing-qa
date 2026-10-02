from __future__ import annotations

import os


ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}


def credential_for(provider: str, environ=None) -> str:
    environ = os.environ if environ is None else environ
    try:
        name = ENV_KEYS[provider]
    except KeyError as exc:
        raise KeyError(f"No built-in credential mapping for provider: {provider}") from exc
    value = environ.get(name)
    if not value:
        raise RuntimeError(f"Missing credential environment variable: {name}")
    return value
