# Persistence Integrity Assessment

Scope: Notion sandbox (data source + database)

Findings:
- Title mapping: `Name` detected and used; titles are correct.
- Content blocks: paragraph blocks use `paragraph.rich_text` and were stored correctly.
- Metadata: minimal revision metadata persisted in runtime; Notion pages store only visible properties (title) — additional runtime metadata is persisted in runtime snapshot, not as page properties.
- Duplicates: idempotency relies on `search()` and title-based dedup keys. Search returns workspace-wide results; dedup checking now restricts to title-prefixed keys to limit false positives.

Risks:
- Databases with sparse property schemas will reject writes for unmapped fields; the sink now skips unmapped fields to avoid errors.
- Relying on Notion `search()` for dedup is imperfect; large workspaces may return noisy hits.

Recommendations:
- Continue using datasource-aware `fields` mappings in `datasource_map` to persist non-title metadata (e.g., `tags -> Tags`).
- Consider an explicit property for `dedup_key` in sandbox database schema for robust idempotency.

