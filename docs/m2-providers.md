# M2.6 — Provider adapters

PloosQA keeps provider APIs behind a transport boundary.

## Built-in editorial board

Adapters are defined for:

- OpenAI
- Anthropic
- Google Gemini
- Mistral

The adapters share the same `ReviewRequest` / `ReviewResponse` contract. Supplemental providers can implement the same interface.

## Structured output

Provider transports must request JSON/structured output and return a decoded object. PloosQA then normalizes and validates every finding against its own schema; provider-side schema enforcement is an additional guard, not the source of truth.

## Credentials

Built-in environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `MISTRAL_API_KEY`

Credentials must never be stored in `publishing-qa.yml`, prompts, reports or audit artifacts.

## Model selection

Model IDs are configuration, not hard-coded policy. PPQAS defines reviewer roles; projects/CI select an available model for each provider. This prevents model churn from changing the standard.

## API evolution

Provider SDK/HTTP details belong in transports. Core orchestration, consensus, verification and evidence binding remain stable when an API changes.
