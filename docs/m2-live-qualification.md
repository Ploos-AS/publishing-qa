# M2.8 — Live provider qualification

Live qualification is deliberately separate from ordinary CI.

A qualification run sends a tiny fixed review request through the real provider adapter and verifies that the provider returns schema-compatible structured output.

The result records provider, configured model, qualification state, structured-output capability, latency and a sanitized error. API keys are never included.

All required providers must qualify for a full four-reviewer release run. Supplemental providers may fail without blocking unless promoted to required.

Live qualification should be manually dispatched or run in a protected release environment with provider secrets. Pull requests and ordinary commits use mock transport tests only and incur no inference cost.


## M2.18 manual workflow

The repository provides `.github/workflows/live-qualification.yml`. It is intentionally triggered only by `workflow_dispatch`; push and pull-request CI never performs live inference.

Configure the protected GitHub Environment `live-provider-qualification` with only the provider secrets that may be used:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `MISTRAL_API_KEY`

Model names are explicit workflow inputs and become `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`, and `MISTRAL_MODEL`. The workflow does not silently choose a billable model.

The `providers` input accepts `all` or a comma-separated subset. This allows one provider to be qualified without exposing or charging the others.

Every run attempts to upload `provider-qualification.json`, including failed qualifications. The command exits successfully only when every selected provider qualifies. Provider errors stored in the artifact are sanitized by the qualification layer.

Recommended repository protection is to require approval for the `live-provider-qualification` Environment. This makes live inference a deliberate human action in addition to the manual workflow trigger.
