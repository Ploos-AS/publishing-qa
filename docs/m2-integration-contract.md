# M2.17 integration contract

M2.17 freezes the integration contract between deterministic QA, independent review, evidence, and the release gate.

## Artifact chain

The supported release chain is:

```text
Markdown source
  -> publishing-qa deterministic report
  -> independent review-run artifact
  -> optional source-bound evidence
  -> ploos-qa release
  -> pipeline report
```

Deterministic QA and review packaging use the same canonical source-document packaging and `source_digest` definition. Review metadata such as language labels does not change source identity.

If evidence is supplied, every evidence item must carry the same `source_digest` as the review run. Missing or mismatching evidence identity fails closed. Human approval is source-bound when required.

Publication artifacts are checked after configured build hooks so a trusted build hook may generate required EPUB, PDF, HTML, or other outputs before artifact validation.

## CLI exit contract

Both deterministic and release command paths use:

- `0`: valid QA execution and PASS
- `1`: valid QA execution but QA/release policy FAIL
- `2`: invalid input, configuration, schema, YAML/JSON, or artifact contract

Expected input errors are reported without an internal traceback.

## Configuration

`publishing-qa.yml` is schema validated. Evidence producers and bindings also receive semantic validation, including producer-ID uniqueness, support polarity, and references to known producers.

## Schema publication

Schemas used at runtime are packaged with the Python distribution. CI compares release-facing packaged schemas with their public copies under `schema/` to prevent drift.

## Regression guarantee

The M2.17 integration test executes the real deterministic CLI, constructs a real review-run through the orchestrator, and feeds both artifacts to the real release CLI. Identical source identity must PASS. A stale deterministic artifact after source mutation must FAIL with a source-identity mismatch.

This contract is the baseline for M2.18 live provider qualification and later publishing-repository pilots.
