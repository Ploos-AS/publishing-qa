# M2.3 — Verification and evidence

Verification is separate from reviewer agreement.

## Evidence classes

High-strength evidence:

- primary source
- formal standard/specification
- executable test
- compiler result

Strong contextual evidence:

- simulator result
- emulator result
- authoritative manual

Supporting evidence:

- human review
- secondary source

The hierarchy is deliberately conservative. A secondary source can increase confidence but cannot by itself turn a technical/factual AI finding into `confirmed`.

## Outcomes

- `confirmed`: strong confirming evidence
- `likely`: supporting but insufficient evidence
- `disputed`: meaningful evidence exists on both sides
- `false_positive`: strong evidence disputes the finding
- `needs_human_review`: evidence is absent or insufficient

## Provenance

Evidence records identify their type and reference and may include:

- SHA-256 source/output digest
- explanatory detail
- UTC collection timestamp

This makes a release QA report auditable after the fact.

## Important limitation

PloosQA records evidence supplied by deterministic tooling, trusted source retrieval or human verification. Merely labelling an AI statement as a "primary source" is not verification. Provider adapters and future source-verification integrations must preserve source identity and provenance.
