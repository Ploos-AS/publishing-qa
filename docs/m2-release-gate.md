# M2.9 — PPQAS release gate

The release gate combines the independent QA stages into one explicit decision.

## Gates

A normal Ploos course/book release evaluates:

1. deterministic QA
2. publication build
3. completion of every required AI reviewer
4. live qualification of every required provider
5. severity thresholds after consensus/verification/judging
6. human approval

There is no synthetic 0–100 quality score. The result is `PASS` or `FAIL`, with each gate and blocking reason recorded.

A finding classified as `false_positive` does not consume a severity threshold. Confirmed, likely, disputed and unresolved human-review findings remain visible to the gate.

## Human authority

When `require_human_approval` is enabled, AI agreement cannot release a book by itself. Human approval is an independent required gate.

## Configuration

Existing release settings are authoritative:

```yaml
release:
  max_blocker: 0
  max_critical: 0
  max_high: 0
  require_deterministic_tests: true
  require_build: true
  require_human_approval: true
```

The output is machine-readable and intended for CI, release evidence bundles and later signed attestations.
