# M2.1 — Review orchestration

The orchestrator executes independent first-pass reviewers and produces an auditable review run.

## Required vs supplemental

A failed required reviewer makes the review run incomplete. A failed supplemental reviewer is recorded but does not by itself block completion.

## Isolation

Each reviewer receives a newly constructed request and its own context copy. First-pass requests never contain another reviewer's findings or response.

## Audit trail

For each reviewer the run records:

- reviewer/provider identity
- required/supplemental status
- exact structured request
- success/failure status
- raw structured response on success
- normalized findings
- error type/message on failure

This raw layer is input to later deduplication, verification and judge stages. It is not itself a release verdict.

## Reproducibility

Provider and model identity are retained in responses. Future work will add prompt/contract version, source digest, timestamps and token/cost metadata without making those provider-specific fields part of the core finding schema.
