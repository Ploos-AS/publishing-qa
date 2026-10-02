# M2.10 — End-to-end PPQAS pipeline

The pipeline produces one release-oriented QA report from the outputs of the preceding stages.

Flow:

```text
deterministic QA + publication build
              |
independent required/supplemental reviews
              |
normalization -> consensus -> verification/judge
              |
provider qualification
              |
human approval
              |
PPQAS release gate
              |
         PASS / FAIL
```

The pipeline report retains the component reports instead of reducing them to a score. This keeps the final decision auditable.

Ordinary CI can exercise the complete pipeline with deterministic fixtures and fake provider adapters. Live provider qualification remains opt-in.

M2.10 is orchestration, not a replacement for the individual stages. Evidence collection/verification may enrich consensus records before the judge/release gate in a production run.
