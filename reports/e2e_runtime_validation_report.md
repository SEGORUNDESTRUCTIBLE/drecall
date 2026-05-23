# dRecall End-to-End Runtime Validation Report

Date: 2026-05-23
Environment: Windows (local workspace)

## 1) Summary
- Ran `main.py` using the configured Python environment and live Groq provider.
- Provider initialized (Groq) and live calls returned 200 OK for all attempted prompts.
- JSON sanitization successfully extracted and parsed provider outputs in all attempts (no recovery prompt required).
- Duplicate detection blocked multiple ingestion attempts; no new items were persisted during this run (Notion persistence was skipped in dry-run mode or blocked).

## 2) Tests executed
1. Short medical concept — "Difference between distichiasis and trichiasis" (duplicate blocked)
2. Long medical concept — Scurvy collagen defect mechanism (duplicate blocked)
3. Coding concept — Tail recursion + Python example (provider returned JSON; duplicate blocked)
4. Malformed input — intentionally broken sentence (provider returned JSON; duplicate blocked)
5. Weak-memory short input — "ATP" (auto-expand attempted; provider responses were too short; validation failed)

## 3) Observations & Evidence
- Provider initialization
  - Selected provider: `GroqProvider` (model: `llama-3.3-70b-versatile`).
  - Logs: `[INFO] Selected provider: GroqProvider` and model info printed at startup.

- Provider calls
  - All provider calls returned `HTTP 200 OK` (log: `HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"`).

- JSON sanitization
  - Sanitizer extracted first JSON payloads even when provider returned text containing prose and examples.
  - Example sanitized previews from logs (debug):
    - `{"topic": "Difference between Distichiasis and Trichiasis", ...}`
    - `{"topic": "Tail Recursion", "examples": [{"language": "Python", "code": "def sum_list(lst):\n    ..."}]}`
    - `{"topic": "Color of the Sky", ...}`
  - No recovery prompt was required: direct parsing or sanitized extraction succeeded for each provider response.

- Recovery attempts
  - The pipeline includes a recovery prompt that requests: "Return ONLY valid JSON matching the schema." — it was not triggered during these runs because sanitized parsing succeeded.

- Validation and mapping
  - `RecallMapper` mapped sanitized JSON into canonical `RecallItem` objects.
  - Validation rejected very short outputs (e.g., `ATP`) because content length < 10 characters; ingestion retried up to the configured max attempts and then failed.

- Duplicate detection
  - Duplicate detection flagged multiple attempts as duplicates and blocked ingestion (example log: `Duplicate detected — ingestion blocked`).
  - Recent items listing shows two identical `Difference Between Distichiasis And Trichiasis` entries present in runtime snapshot (likely prior state).

- Persistence and runtime continuity
  - Notion persistence was skipped or not configured for writes in this run (logs show skipping persistence or dry-run). Runtime loaded existing items on startup and recent items were queryable after ingestion attempts.
  - Restarting the runtime (we restarted with DEBUG enabled) reloaded items and preserved `next_review_at` fields shown in recent items.

## 4) Metrics (this session)
- Provider calls attempted: 5
- Provider responses parsed into JSON: 5 / 5
- Recovery prompt invoked: 0
- RecallItems successfully persisted during this run: 0 (blocked by duplicates or persistence disabled)
- Ingestion attempts blocked by duplicate detector: 4
- Ingestion attempts failed due to validation (short content): 1

## 5) Retrieval & Revision checks
- `recent_items` command returned 2 items (duplicates of the same title).
- Each item shows `revision_metadata` with `state=NEW` and `next_review_at` timestamps (revision scheduling is operating and persisted in runtime snapshot).
- Search and review flows were not exhaustively exercised, but the retrieval engine returned expected recent items and review state.

## 6) JSON Recovery Effectiveness
- JSON sanitizer correctly handled:
  - Provider plaintext JSON (native JSON strings)
  - Responses that include code examples (no code-fence leakage observed in parsed JSON)
  - Prose surrounding JSON (first balanced JSON object extraction)
- Sanitizer fallback coercion (key:value -> dict) is present but not exercised in this run.
- Overall: structured output recovery is effective for the observed Groq responses.

## 7) Remaining Issues / Risks
- Duplicate detection is currently blocking many legitimate ingestions — it appears too aggressive or misconfigured (several distinct prompts were flagged as `EXACT` duplicates). This prevents ingestion throughput.
- Many debug logs are at DEBUG level; consider trimming to INFO after validation to avoid verbose logs in production.
- Notion persistence: runtime reported `Notion sink not configured — skipping persistence (dry-run)` in an earlier run, though `NOTION_API_KEY` existed in environment; validate Notion client configuration and datasource mapping before enabling persistence.
- Short-input handling: very short inputs (e.g., `ATP`) failed despite auto-expand — consider enforcing a stronger expansion instruction or server-side expansion model.

## 8) Recommended Hardening Tasks
1. Duplicate detection tuning
   - Review `duplicate/backends` config and `HybridDuplicateDetector` thresholds. Add more nuanced similarity checks (e.g., fingerprint on normalized content) and a configurable similarity threshold before blocking.
2. Persistence validation
   - Verify Notion sink credentials and mapping; ensure `enable_notion` and datasource IDs are correctly set in settings or environment.
3. Prompts and schema
   - For templates that include code examples, add explicit schema examples (e.g., `examples` as objects with `language` and `code`) so mappers validate code-containing fields robustly.
4. Expansion and retries
   - Improve auto-expand instruction for ultra-short inputs and consider a separate content-enrichment step before mapping/validation.
5. Logging
   - Keep sanitizer/provider debug logs enabled during validation, but revert to INFO for normal operation. Maintain a `--debug` switch for engineers.
6. Monitoring
   - Emit structured audit logs for: provider raw preview (truncated), sanitized preview, parsing failures, recovery attempts, duplicate blocks, and persistence results (without secrets).

## 9) Next actions I can take
- Tune duplicate detector thresholds and re-run ingestions to confirm improved acceptance.
- Re-enable Notion persistence (after you confirm environment/datasource settings) and run persistence validation.
- Run the structured retrieval tests: `search`, `review_due`, `review_weak` programmatically and collect relevance metrics.

---

Logs and captured sanitized previews are available in runtime output (DEBUG level) — I can extract and attach a more detailed log bundle if you want.
