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


## Operational acceptance

M2.18 code acceptance and provider acceptance are deliberately separate.

Code acceptance requires ordinary CI to pass the qualification CLI tests, workflow trigger/security tests, provider transport mocks, schema validation and package tests. These tests incur no provider cost.

Provider acceptance requires a manual live run for each provider/model pair intended for a release. A provider/model pair is accepted only when its artifact has `qualified: true` and `structured_output: true`. Qualification of one model does not qualify another model from the same provider.

Before a full four-reviewer production pilot:

1. configure the protected Environment and its required reviewers;
2. add the four API-key secrets;
3. choose explicit model names for the intended production review;
4. run qualification for each provider/model pair;
5. retain the resulting JSON artifact as release input/evidence;
6. do not proceed as fully qualified if any required provider fails.

No secret value should be placed in repository configuration, workflow inputs, logs, documentation or qualification artifacts.
