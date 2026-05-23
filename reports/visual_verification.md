# Visual Verification & Cognitive Usability Report
Date: 2026-05-23T07:22:58.535816Z

Total pages inspected: 11
Duplicate titles detected: 0

## Page-level sample (all pages)
- ID: 369d5193-1010-81ea-95ef-ea80ad2fc186
  - Title: Malformed Noisy — The input content appears to be
  - First paragraph (excerpt): The input content appears to be incomplete JSON with random symbols and a URL.
  - Readable for study: True, avg words/sentence: 14.0
  - Auto-enriched title: True, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-814b-8e39-ccbe921e4b67
  - Title: Duplicate Candidate — Explain the difference between HTTP and
  - First paragraph (excerpt): Explain the difference between HTTP and HTTPS
  - Readable for study: True, avg words/sentence: 7.0
  - Auto-enriched title: True, awkward_tail: True
  - Diagnostic note present: False

- ID: 369d5193-1010-815c-b4d7-d1688dbdc15e
  - Title: Weak-memory Concept
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: False, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-818c-be21-f228b14d021b
  - Title: Long Input — This is a long test input
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: True, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-81a7-91fc-cee5539de337
  - Title: Short Input — Osmosis
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: True, awkward_tail: True
  - Diagnostic note present: False

- ID: 369d5193-1010-81fd-90e4-f806dedbf898
  - Title: Coding Concept — Python list comprehensions provide a powerful
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: True, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-81b5-9358-c60342fdf45c
  - Title: Medical Concept — The pathophysiology of pernicious anemia explained
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: True, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-81f9-8cda-d0290baa591f
  - Title: Live flow test eeef5899-5dee-4dcf-8226-5d921b94ee2e
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: False, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-8140-a546-ccb517a4a10c
  - Title: Test create — hello
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: True, awkward_tail: True
  - Diagnostic note present: False

- ID: 369d5193-1010-814d-aed3-c3dd89c605a9
  - Title: dRecall DB Persistence Test
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: False, awkward_tail: False
  - Diagnostic note present: False

- ID: 369d5193-1010-81aa-9e19-f70aaae68142
  - Title: dRecall DataSource Persistence Test
  - First paragraph (excerpt): 
  - Readable for study: False, avg words/sentence: 0.0
  - Auto-enriched title: False, awkward_tail: False
  - Diagnostic note present: False

## Summary Assessments
- Pages meeting minimal study-readability heuristics: 2/11
- Pages with appended diagnostic notes: 0
- Pages with auto-enriched titles: 7
- Pages with awkward auto-expansions: 3

## Recommendations (manual UX improvements)
- Manually review pages with awkward auto-expansions and adjust title tail for clarity.
- Add minimal visible properties for review context: `next_review_at`, `state`, and `last_reviewed_at` where possible.
- For very short pages, expand the first paragraph into a concise 1-2 sentence summary before finalizing persistence.
- Use a dedicated `dedup_key` property to avoid title-based dedup confusion.