# M2.11 — Release CLI

M2.11 exposes the end-to-end PPQAS release decision as a command-line entry point.

```text
ploos-qa-release \
  --config publishing-qa.yml \
  --deterministic deterministic-report.json \
  --reviews review-run.json \
  --qualifications provider-qualifications.json \
  --evidence evidence-by-consensus.json \
  --human-approved \
  --output qa-report.json
```

Exit status is `0` only when the release decision is `PASS`. A policy `FAIL` returns `1` but still writes the complete report, so CI retains the audit trail.

`--human-approved` is deliberately explicit. The CLI never infers human approval from AI agreement.

Live provider calls are not implicit in this command. Qualification and review artifacts are inputs, keeping cost-bearing network activity separately controlled.
