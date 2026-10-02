# M2.7 — Provider transports

PloosQA implements HTTP transports behind the provider-neutral adapter contract.

## Current transports

- OpenAI Responses API with JSON Schema structured output and `store: false`
- Anthropic Messages API with `output_config.format`
- Google Gemini Interactions API with JSON response format/schema
- Mistral Chat Completions with JSON Schema response format

Model IDs remain configuration.

## Reliability

The shared HTTP client provides bounded timeout and exponential retry for transient HTTP/network failures. It does not retry ordinary client errors.

## Privacy and audit

API keys are only sent in provider authentication headers and are never written to the review request, response audit structure or QA report.

Provider response bodies should not be copied wholesale into CI logs. PloosQA retains the structured review response required for the audit trail.

## Testing

Transport unit tests use fake HTTP clients. Normal CI therefore does not require provider credentials and does not incur inference cost.

Live provider qualification is a separate opt-in test stage and should use repository/environment secrets.
