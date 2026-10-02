# M1 — Deterministic QA

M1 introduces a provider-independent command-line QA engine.

## Current checks

- QA configuration can be parsed
- supported QA version
- primary language and language list
- Markdown UTF-8 validity
- missing local Markdown targets
- missing local image assets
- empty image alt text
- tab characters in Markdown
- every emitted finding validates against the common finding schema

## Exit policy

The CLI exits non-zero when BLOCKER, CRITICAL or HIGH findings exist.

MEDIUM, LOW and INFO findings remain visible in the JSON report but do not fail the default gate.

## Usage

```sh
python -m pip install -e .
publishing-qa .
```

The report is written to `qa-report.json`.

M1 is deliberately deterministic. AI-provider integration belongs to a later milestone.
