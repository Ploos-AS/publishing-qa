# M2 — AI review contract

M2 separates the QA standard from provider SDKs.

## Flow

1. PloosQA assembles a `ReviewRequest`.
2. Each first-pass reviewer receives its own request independently.
3. A provider adapter returns a `ReviewResponse`.
4. Findings are normalized into the common finding schema.
5. Invalid findings are rejected before judge/consensus processing.

## Provider independence

The core package does not import OpenAI, Anthropic, Google or Mistral SDKs. Provider integrations are adapters. This keeps the QA contract stable when APIs, SDKs and model names change.

## Review package

A request contains:

- project identity
- reviewer identity
- assigned roles/capabilities
- selected source documents
- language metadata
- common instructions
- structured context

First-pass requests never contain findings from other reviewers.

## Output

Every provider ultimately produces the same normalized finding structure. Provider-native severities/categories may be mapped to PPQAS vocabulary before schema validation.
