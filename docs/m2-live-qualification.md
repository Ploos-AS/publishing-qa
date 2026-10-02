# M2.8 — Live provider qualification

Live qualification is deliberately separate from ordinary CI.

A qualification run sends a tiny fixed review request through the real provider adapter and verifies that the provider returns schema-compatible structured output.

The result records provider, configured model, qualification state, structured-output capability, latency and a sanitized error. API keys are never included.

All required providers must qualify for a full four-reviewer release run. Supplemental providers may fail without blocking unless promoted to required.

Live qualification should be manually dispatched or run in a protected release environment with provider secrets. Pull requests and ordinary commits use mock transport tests only and incur no inference cost.
