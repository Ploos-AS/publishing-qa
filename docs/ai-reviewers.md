# AI reviewer model

Ploos Publishing QA uses a stable required editorial board plus optional supplemental reviewers.

## Required board

The default board has four independent reviewers:

- OpenAI — technical review and QA lead
- Anthropic — pedagogy and manuscript review
- Google — fact checking and consistency
- Mistral — independent and language-oriented review

Four independent providers give useful diversity without making every review unnecessarily expensive or slow.

## Supplemental reviewers

The architecture is intentionally not limited to four providers. A project may add zero or more supplemental reviewers.

Useful supplemental roles include:

- domain expert
- Norwegian language specialist
- accessibility specialist
- security reviewer
- code specialist
- local/offline model
- adversarial or red-team reviewer
- additional independent fact checker

A supplemental reviewer does not become a release dependency unless the project explicitly promotes it to `required`.

## Capability-based design

Provider names identify adapters; roles define why a reviewer is present. This allows models and vendors to change without rewriting the QA standard.

## Independence

All first-pass required and supplemental reviewers receive the same source package and review contract, but not each other's findings.

## Consensus

More reviewers do not make a claim true. Findings are normalized and deduplicated after independent review. Technical and factual claims still require verification.

## Cost control

Recommended modes:

- PR: required reviewers on affected content; supplemental reviewers selectively
- release candidate: all required reviewers; selected specialists
- major release: all required reviewers plus configured supplemental reviewers
