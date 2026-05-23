# Persistence Usability Diagnostics

Date: 2026-05-23

Executive summary
- Inspected 11 persisted Notion pages created during the sandbox validation run.
- Persistence is operational and pages are readable, but there are UX friction points affecting cognitive usability.

Key quantitative findings
- Total persisted pages inspected: 11
- Pages with missing revision metadata: 11
- Pages flagged with JSON-like blobs in properties or blocks: 11 (likely from storing serialized metadata in properties)
- Unicode issues found: 0
- Pages with zero content blocks: 2

1) Page Quality Assessment
- Title quality: Most titles are short (1-4 words). 4 titles are long enough for clarity; several (e.g., "Short Input", "Long Input") are minimal and likely need enrichment to be useful as standalone study prompts.
- Readability: First paragraph excerpts are generally concise; for 6/11 pages the first paragraph meets minimal study-readability heuristics (avg words per sentence between 3 and 30 and length >30 chars).
- Formatting cleanliness: Paragraph blocks are plain text and use `paragraph.rich_text` correctly. A few pages contain very short snippets (single word) or are missing content blocks.
- Block hierarchy: All pages are flat (paragraph-only); no nested lists or structured sections found.
- Metadata visibility: Only the `Name` title property is in the database; other runtime metadata is not visible on the page (it lives in the runtime snapshot), which is acceptable but reduces transparency for reviewers.
- Review usability: Runtime review metadata exists in-memory but is not reflected as page properties. This makes Notion pages less useful when users land directly on the page.

2) Property Validation
- Title mapping stable: `Name` detected and used consistently.
- Subject mapping / Tags: No robust mapping found for tags/subjects; these are not present in page properties.
- Revision metadata preserved: Notion pages do not contain revision metadata; runtime snapshot contains it. All 11 pages had empty `revision_metadata` in the page inspection (runtime had revision metadata transiently during review operations).
- Timestamps: Page `created_time` and `last_edited_time` are present in Notion and are correct (not exhaustively listed here).
- Duplicate metadata: Dedup keys were not present as page properties; dedup detection relies on search and title matching which is fragile.
- Malformed values: No malformed Unicode or corrupted block text found; however, many properties contain serialized structures when inspected, creating noise.

3) Block Content Validation
- Paragraph blocks: Present on most pages and contain readable text.
- Rich_text structure: Proper `plain_text` values were present and extracted correctly.
- Multiline formatting: Minimal — blocks are mostly single-line paragraphs; no multi-paragraph structure or lists in persisted pages.
- Escaped characters & Unicode: No problematic escaped characters detected; Unicode handled correctly.
- Overall: Content looks like lightweight study notes but often too short or lacking structure for deeper study.

4) Cognitive Usability Review
- Can pages function as study memories? Yes, but only when the title + paragraph provide sufficient context. Several pages are too terse to be effective alone.
- Retrieval usefulness: Retrieval returned 1 relevant result per scenario; search-based retrieval is effective for controlled scenarios but may degrade in larger real workspaces.
- Metadata understandability: Low — because runtime metadata and revision state are not surfaced on the page, reviewers landing in Notion lack scheduling context.
- Weak-memory signals: Present in runtime, but not visible in Notion; thus Notion pages are not self-explanatory regarding review urgency or history.
- Review continuity: Since updates (e.g., title change) were written back to Notion during review, continuity is possible but relies on the runtime to re-sync review metadata.

5) Noise Detection
- Unnecessary metadata exposure: Many pages have properties that include serialized runtime data (truncated in inspection). This creates visual noise and reduces clarity.
- Serialized JSON blobs: Flags detected — prefer avoiding persisting raw JSON into Notion properties.
- Noisy fields: Dedup keys and runtime blobs should not be surfaced as properties.
- Low-value artifacts: Pages with zero blocks or single-word notes are low-value persisted assets.

6) Recommended Alpha Hardening Improvements (prioritized)
- Add an explicit `dedup_key` property to the datasource schema and map canonical dedup keys into it; avoid relying on search for dedup.
- Surface minimal revision metadata on the page (readable properties): `last_reviewed_at`, `next_review_at`, `state` to make pages self-explanatory in Notion.
- Avoid storing raw serialized JSON in page properties; instead persist only small, user-facing fields (tags, source, dedup_key) and leave runtime blobs to snapshots.
- Enrich short titles on ingest: when title length <3 words, generate a short descriptive title (e.g., include subject or first 8 words of content) to improve standalone readability.
- Ensure pages have at least one descriptive paragraph; skip persisting empty pages or add a minimal summary block if content is short.
- Add a lightweight verification that detects zero-block pages and warns/augments them before persisting.
- Maintain a `persistence_policy` config per datasource to control which fields are written as page properties vs. runtime-only.
- Improve dedup detection by using a dedicated property and an indexed query rather than workspace-wide search.

7) Deliverables generated
- reports/full_lifecycle_validation.md — lifecycle summary
- reports/persistence_assessment.md — persistence integrity assessment
- reports/runtime_continuity.md — snapshot/reload findings
- reports/alpha_risks_and_hardening.md — risks and action items
- reports/inspection_pages.json — raw per-page inspection data
- reports/inspection_summary.md — human-readable inspection summary
- reports/persistence_usability_diagnostics.md — this final diagnostics report

Next recommended step
- I can run an automated remediation pass to: (a) annotate pages with minimal revision properties, (b) enrich short titles, and (c) add a failing-warnings log for zero-block pages. Shall I proceed to implement that remediation script? If yes, pick which items to auto-modify (all sandbox pages or only pages flagged as low-value).
