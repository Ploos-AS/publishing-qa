# M2.16 Audit and privacy contract

Publishing QA audit records are designed for reproducibility without copying source manuscripts into the audit artifact.

## Default audit

The default review audit records reviewer/provider identity, whether the reviewer is required, request metadata, source digest, document path/language/UTF-8 byte size, model identity, finding count, normalized findings, and success/failure state.

It does **not** store document contents or provider response notes. Reviewer exceptions are sanitized and bounded before they are written to the audit. Credential-like values such as bearer tokens, API keys, tokens, secrets, and passwords are redacted.

The source itself is identified by the SHA-256 `source_digest`. M2.15 release gates bind deterministic QA, review, evidence, human approval, and the final report to that source identity.

## Sensitive debug mode

`run_reviews(..., audit_full_content=True)` is an explicit diagnostic opt-in. It stores the complete structured review request and response, including document content and provider notes.

**Warning:** full-content audit artifacts may contain unpublished manuscripts, course material, confidential context, provider output, or other sensitive information. They must not be enabled in normal CI, published as build artifacts, or retained longer than necessary.

Full-content mode does not disable exception sanitization.

## Security boundary

Redaction is defense in depth, not a secret-management system. Credentials must still be supplied through an appropriate secret store and must never be embedded in source documents, prompts, configuration, or repository files.

The privacy-safe default is part of the QA contract and is covered by regression tests.
