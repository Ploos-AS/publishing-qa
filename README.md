# Ploos Publishing QA

Shared quality-control framework for Ploos AS courses and books.

## Goals

- deterministic checks before AI review
- independent multi-model review
- standardised findings and severities
- pedagogical, technical, editorial and translation-parity QA
- release gates with human approval
- reusable CI for all publishing repositories

## M0 scope

This repository defines the first common QA contract:

- `publishing-qa.yml` reference configuration
- JSON Schema for machine-readable review findings
- reviewer role definitions
- release-gate policy
- GitHub Actions baseline validation

AI provider integrations are intentionally separated from the core contract so repositories can use OpenAI, Anthropic, Google and Mistral independently.

## Pipeline

```text
source
  -> deterministic QA
  -> build/test
  -> independent AI reviewers
  -> normalize/deduplicate
  -> verification
  -> release gate
  -> human approval
```

## Principles

1. AI is a reviewer, not the source of truth.
2. Anything deterministic should be tested deterministically.
3. First-pass reviewers must work independently.
4. Agreement between models is evidence, not proof.
5. Technical claims should prefer primary-source verification.
6. Releases remain subject to human approval.


## Audit privacy

Review audit is privacy-safe by default: source content and provider notes are not retained in the audit artifact, failures are sanitized, and source identity is represented by a digest. Full-content audit is an explicit sensitive debug opt-in. See `docs/m2-audit-privacy.md`.

## M2 integration contract

M2.17 freezes source identity, artifact ordering, schema synchronization, evidence/config validation, and CLI exit semantics across deterministic QA and the release gate. The real end-to-end regression requires identical source artifacts to pass and stale source artifacts to fail closed. See `docs/m2-integration-contract.md`.


## Live provider qualification

M2.18 adds opt-in qualification of the real OpenAI, Anthropic, Google Gemini and Mistral adapters. Live inference is never part of push or pull-request CI. It must be started manually through the protected `live-provider-qualification` GitHub Environment, with explicit provider/model selection.

A release qualification artifact records the exact provider and model that passed. Changing the model requires a new qualification; a successful mock or offline CI run is not a substitute for live qualification.

See `docs/m2-live-qualification.md` for secrets, model inputs, artifacts and operational procedure.


## M2 freeze

M2 is feature-frozen. The engine baseline, invariants and M3 boundary are recorded in `docs/m2-freeze.md`. Future M2 changes are limited to defects, security fixes, provider API compatibility fixes and documentation corrections. New publishing capabilities move to M3.
