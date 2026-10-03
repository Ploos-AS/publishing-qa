# M2 freeze — publishing QA engine

M2 is the frozen baseline for the Ploos Publishing QA engine.

## Status

Implementation complete. Ordinary repository CI is green at the M2 freeze point.

Live provider qualification is an operational prerequisite for using a specific provider/model pair in a production release. It is not performed by ordinary CI and is not required to consider the M2 implementation complete.

## Frozen capabilities

M2 provides:

- deterministic source and publication checks;
- canonical source packaging and source digests;
- independent multi-provider reviewer orchestration;
- normalized, schema-validated findings;
- conservative consensus grouping;
- explicit evidence and provenance;
- evidence-to-finding binding;
- judge dispositions;
- source-bound human approval;
- fail-closed source identity;
- release gates and machine-readable reports;
- OpenAI, Anthropic, Google Gemini and Mistral provider adapters;
- privacy-safe audit metadata by default;
- explicit CLI exit contracts;
- synchronized packaged/public schemas;
- manual, protected live provider qualification.

## Invariants

1. AI agreement is not proof.
2. Findings that require verification cannot become confirmed merely through reviewer consensus.
3. Deterministic checks run before AI review.
4. Required reviewer failure makes the review board incomplete.
5. Evidence used for a release must match the reviewed source digest.
6. Human approval must match the reviewed source digest.
7. Stale or mismatched source artifacts fail closed.
8. Live inference never runs on push or pull request.
9. A live qualification applies only to the recorded provider/model pair.
10. Secrets are never release artifacts.

## M2 release boundary

The M2 engine is now feature-frozen except for defects, security fixes, provider API compatibility fixes and documentation corrections.

New publishing capabilities belong to M3 or later.

## M3 entry criterion

The first M3 work is a real pilot integration in a Ploos publishing repository. The pilot should consume the frozen M2 contracts rather than adding project-specific behavior to the engine.

EduNumbers is the initial pilot candidate.
