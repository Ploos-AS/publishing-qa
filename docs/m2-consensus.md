# M2.2 — Consensus and verification

Consensus is an observation about reviewer agreement, not proof.

## Deduplication

Normalized findings are grouped conservatively using category, file and textual overlap. The grouping algorithm is intentionally replaceable; later versions may use embeddings or a judge model, but deterministic grouping remains available.

## Agreement

Each group records:

- contributing reviewers
- agreement count
- original finding IDs
- reported severities
- whether any finding requires verification

Even unanimous agreement leaves `verification_status: unverified`.

## Verification

Verification is a separate explicit operation. Supported states are:

- confirmed
- likely
- disputed
- false_positive
- needs_human_review

Evidence can then be attached. For factual and technical claims, primary-source or executable evidence is preferred.

## Judge rule

A future AI judge may organize evidence, detect contradictions and recommend a verification state, but it must not silently convert model agreement into factual confirmation.
