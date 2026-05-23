# Remaining Alpha Risks and Recommended Hardening Tasks

Top Risks:
- SDK compatibility: installed Notion SDK lacks some convenience methods; wrappers must remain robust and test-covered.
- Dedup false positives: workspace-wide search can surface unrelated pages.
- Schema mismatch: sandbox DBs may not have expected properties, causing write failures if unmapped fields are sent.

Recommended Tasks (priority):
1. Add explicit `dedup_key` property to datasource DB and map to canonical dedup keys.
2. Implement persistent write-queue with retry policies and exponential backoff (to tolerate transient Notion failures).
3. Snapshot hygiene: maintain timestamped backups and pre-commit JSON validation.
4. Logging: reduce noisy debug logs and add structured severity levels.
5. Add integration tests covering data_source vs database parent write paths.
6. Add periodic integrity check that validates persisted pages exist and contain required properties.

