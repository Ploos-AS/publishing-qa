from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .providers.base import JSONReviewerAdapter
from .providers.builtin import AnthropicAdapter, GoogleAdapter, MistralAdapter, OpenAIAdapter
from .providers.transports import AnthropicTransport, GeminiTransport, MistralTransport, OpenAITransport
from .qualification import qualify_provider
from .validation import load_schema, validate

PROVIDERS = {
    "openai": (OpenAIAdapter, OpenAITransport, "OPENAI_MODEL"),
    "anthropic": (AnthropicAdapter, AnthropicTransport, "ANTHROPIC_MODEL"),
    "google": (GoogleAdapter, GeminiTransport, "GEMINI_MODEL"),
    "mistral": (MistralAdapter, MistralTransport, "MISTRAL_MODEL"),
}


def main() -> None:
    parser = argparse.ArgumentParser(prog="ploos-qa-qualify")
    parser.add_argument("--provider", action="append", choices=sorted(PROVIDERS), dest="providers")
    parser.add_argument("--output", default="provider-qualification.json")
    args = parser.parse_args()

    selected = args.providers or list(PROVIDERS)
    finding_schema = load_schema(Path(__file__).resolve().parent / "schemas" / "finding.schema.json")
    qualification_schema = load_schema(Path(__file__).resolve().parent / "schemas" / "provider-qualification.schema.json")
    results = []

    for provider in selected:
        adapter_cls, transport_cls, model_env = PROVIDERS[provider]
        model = os.environ.get(model_env, "").strip()
        if not model:
            result = {
                "provider": provider, "model": "", "qualified": False,
                "structured_output": False, "latency_ms": 0,
                "error": f"missing required model environment variable: {model_env}",
            }
        else:
            try:
                adapter = adapter_cls(transport=transport_cls(), model=model, output_schema=finding_schema)
                result = qualify_provider(provider=provider, adapter=adapter, model=model)
            except Exception as exc:
                result = {
                    "provider": provider, "model": model, "qualified": False,
                    "structured_output": False, "latency_ms": 0,
                    "error": f"{type(exc).__name__}: provider setup failed",
                }
        validate(result, qualification_schema, f"{provider} qualification")
        results.append(result)

    Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    sys.exit(0 if all(item["qualified"] for item in results) else 1)


if __name__ == "__main__":
    main()
