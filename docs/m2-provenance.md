# M2.4 — Automated evidence provenance

PloosQA can collect evidence from trusted project commands and generated artifacts.

## Command evidence

A configured command records:

- exact command
- working directory
- exit code
- timeout state
- SHA-256 of stdout
- SHA-256 of stderr
- SHA-256 of the complete command transcript
- UTC collection time

A successful trusted command may support a finding. A failed command disputes the proposition it was configured to test. A timeout is contextual evidence only.

Typical evidence producers:

- compiler
- unit/integration test
- simulator
- emulator
- publication build/validator

## Artifact evidence

Generated artifacts can be hashed and recorded so a QA report refers to the exact PDF, EPUB, HTML bundle or test output that was inspected.

## Trust boundary

Commands are configuration supplied by the repository and execute with CI privileges. They must only run for trusted repository revisions. Pull requests from untrusted contributors require the CI platform's normal secret and permission protections.

PloosQA does not infer what an arbitrary command proves. The project configuration must explicitly bind an evidence producer to a claim/check. This prevents a successful unrelated command from being treated as verification.
