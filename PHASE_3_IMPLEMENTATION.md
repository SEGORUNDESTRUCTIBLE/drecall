# Phase 3 Implementation: Autonomous Structured Ingestion MVP

## Goal
Build an MVP for dRecall that accepts any medical text and performs:
- domain detection
- content classification
- medical template selection
- structured AI generation
- canonical schema transformation
- metadata extraction and scheduling
- Notion database schema inspection
- safe missing-field creation
- Notion persistence of structured revision notes

---

## Files Added / Updated

### Core Modules
- `core/domain_detector.py`
- `core/content_classifier.py`
- `core/template_selector.py`
- `core/canonical_schema.py`
- `core/metadata_extractor.py`
- `core/adaptive_pipeline.py`
- `core/__init__.py`

### Notion Intelligence
- `notion/notion_schema_mapper.py`
- `notion/workspace_inspector.py`

### Templates
- `templates/medical/concept.yaml`
- `templates/medical/ophthalmology.yaml`
- updated `templates/medical/mcq.yaml`
- updated `templates/medical/histopath.yaml`
- updated `templates/medical/radiology.yaml`
- updated `templates/medical/ecg.yaml`
- updated `templates/medical/mistake.yaml`

### Tests
- `tests/test_autonomous_ingestion.py`

---

## Architectural Overview

1. **Domain Detection**
   - `DomainDetector` uses lightweight medical keyword heuristics.
   - Detects: `mcq`, `concept`, `mistake`, `histopathology`, `radiology`, `ecg`, `ophthalmology`, `screenshot`, `pyq`.
   - Returns canonical output with `domain`, `content_type`, `subtype`, and `confidence`.

2. **Content Classification**
   - `ContentClassifier` maps detected type to revision intent and template hint.
   - Provides tag metadata and confidence scoring.

3. **Template Selection**
   - `TemplateSelector` loads medical YAML template definitions.
   - Chooses best template based on content type and supported input types.
   - YAML templates define: prompt, required fields, revision sections, metadata rules, image requirements, and scheduling defaults.

4. **Canonical Schema**
   - `CanonicalRevisionPayload` defines the structured output contract.
   - Supports: `title`, `content`, `memory_hook`, `trap`, `retest_question`, `core_concept`, `exam_pearl`, `one_liner`, `image_required`, `pyq`, `weak_topic`, `revision_metadata`, `tags`, `subject`, `subtopic`, `options`, `answer`, `explanation`.
   - `from_provider_output()` canonicalizes raw provider JSON into a stable object.

5. **Metadata Extraction**
   - `MetadataExtractor` enriches the canonical payload with inferred `subject`, `subtopic`, tags, and revision schedule defaults.
   - Emits a `revision_metadata` structure for adaptive schooling.

6. **Notion Workspace Intelligence**
   - `NotionSchemaMapper` inspects Notion properties and matches them against canonical fields.
   - `WorkspaceInspector` ranks candidate databases and selects the best schema fit.
   - Missing fields are detected and can be created safely through Notion API updates.

7. **Adaptive Pipeline**
   - `AdaptivePipeline` orchestrates the full flow from raw text to persistence.
   - Supports provider abstraction through `ProviderAdapter`.
   - Preserves a clean separation: input intelligence, canonicalization, metadata enrichment, workspace selection, persistence.

---

## Dependency Graph

- `core/adaptive_pipeline.py`
  - depends on `core/domain_detector.py`
  - depends on `core/content_classifier.py`
  - depends on `core/template_selector.py`
  - depends on `core/canonical_schema.py`
  - depends on `core/metadata_extractor.py`
  - depends on `notion/workspace_inspector.py`
  - depends on `notion/notion_schema_mapper.py`
  - depends on `notion/notion_sink.py`

- `core/template_selector.py`
  - depends on YAML definitions in `templates/medical/*.yaml`

- `notion/workspace_inspector.py`
  - depends on `notion/notion_schema_mapper.py`

---

## Recommended Dataclasses / Pydantic Models

- `DomainDetectionResult`
- `ContentClassificationResult`
- `TemplateDefinition`
- `TemplateChoice`
- `CanonicalRevisionPayload`
- `MetadataExtractionResult`
- `WorkspaceInspectionResult`
- `AdaptivePipelineResult`

---

## Implementation Order

1. Build domain detector heuristics.
2. Create content classifier mapping to revision intent.
3. Define template catalog and load YAML metadata.
4. Build canonical schema model and provider output normalization.
5. Add metadata extraction and schedule defaults.
6. Implement Notion schema inspection and compatibility scoring.
7. Wire the end-to-end adaptive pipeline orchestration.
8. Add unit tests for each stage and an end-to-end dry-run scenario.

---

## Tests Required for Each Module

- `DomainDetector`:
  - correct type detection for MCQs, ECGs, radiology, histopathology, mistakes, concept notes.
  - fallback behavior for generic input.

- `ContentClassifier`:
  - intent mapping from content type.
  - confidence scaling for keyword patterns.

- `TemplateSelector`:
  - YAML template discovery.
  - best template selection for known content types.

- `CanonicalRevisionPayload`:
  - provider payload normalization.
  - missing field fallback and validation.

- `MetadataExtractor`:
  - subject inference.
  - schedule metadata generation.

- `NotionSchemaMapper`:
  - mapping and missing field detection.
  - type compatibility scoring.

- `WorkspaceInspector`:
  - database discovery fallback.
  - best match selection.

- `AdaptivePipeline`:
  - end-to-end dry-run processing without persistence.
  - candidate Notion selection and optional persistence integration.

---

## Architectural Risks

- Heuristic rules may misclassify ambiguous medical content.
- Custom YAML parsing is intentionally lightweight and should be replaced by a full parser if templates grow more complex.
- Notion property creation via API can fail if the database is read-only or has naming collisions.
- Provider JSON output remains a fragile surface; stronger schema enforcement will be needed for production.
- Template selection based only on content type may underfit mixed content like MCQ-with-interpretation.

---

## Minimal Working Ingestion Demo Path

1. Instantiate a `DummyProvider` or real provider implementing `ProviderAdapter`.
2. Create `AdaptivePipeline(provider=provider, notion_client=None)`.
3. Call `process_text(raw_medical_text, source="demo")`.
4. Validate the returned `AdaptivePipelineResult.canonical_payload` and `metadata_extraction`.
5. Add `NotionSink` and a valid `notion_client` for persistence once the schema match is satisfactory.

---

## Next Step
Integrate a real AI provider and replace the lightweight YAML parser with a production-grade template catalog loader. Move from heuristic classification to a small supervised model or retrieval-augmented prompt templates for quality improvement.
