# M2.12 — Artifact validation

Release inputs are treated as contracts, not trusted dictionaries.

Before the release pipeline runs, `ploos-qa release` validates:

- deterministic-stage report
- review-run report
- every provider-qualification result
- optional consensus evidence map

The final pipeline report is validated before it is written.

Malformed input raises an artifact-validation error and no release report is emitted. A policy decision of `FAIL`, by contrast, is a valid report and is written before the CLI returns exit status 1.

Runtime schemas live inside the Python package and are included as package data. The installed CLI therefore does not depend on a checkout-level `schema/` directory.

This separates three outcomes:

- exit 0: valid report, release PASS
- exit 1: valid report, release FAIL
- exit 2 / invocation or validation failure handling: the release decision could not be evaluated safely
