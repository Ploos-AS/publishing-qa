# Release gates

## Gate 1 — deterministic QA

Must run before AI review where applicable:

- source validation
- links
- images/assets
- metadata
- code compilation/execution
- tests
- exercise/solution integrity
- publication builds
- accessibility checks

## Gate 2 — AI review

Required review dimensions:

- technical
- pedagogical
- editorial
- exercises
- translation parity
- accessibility
- references

## Gate 3 — verification

Findings that assert technical or factual errors should be verified using, in order of preference:

1. primary datasheet/manual/specification
2. vendor or project documentation
3. authoritative reference
4. secondary source

## Gate 4 — release

Default policy:

- BLOCKER: 0
- CRITICAL: 0
- HIGH: 0
- deterministic QA: PASS
- build: PASS
- required review dimensions: COMPLETE
- human approval: REQUIRED

No aggregate numeric quality score is required. The release report should show dimensions and unresolved findings explicitly.
