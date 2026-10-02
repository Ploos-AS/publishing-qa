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
