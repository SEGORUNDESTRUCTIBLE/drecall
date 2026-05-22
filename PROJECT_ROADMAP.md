# dRecall Project Roadmap

## Vision

dRecall is evolving into a universal recall platform for scalable lifelong learning. The architecture is designed to support:
- modular provider abstraction
- production-grade onboarding and ingestion workflows
- resilient revision and enhancement pipelines
- extensible plugin/provider ecosystems
- user-friendly GUI and deployment readiness

This roadmap defines the path from the current stable infrastructure to a public-ready, universal recall platform.

---

## Completed Phases

### Phase 1: Core Schema + Provider Abstraction
- Established `core/schemas.py` with `RecallItem` and validation models.
- Added `providers/base_provider.py` abstract interface.
- Implemented provider test coverage for clean, provider-agnostic design.

### Phase 2: Provider System and Settings Stabilization
- Added `providers/groq_provider.py` and `providers/gemini_provider.py`.
- Implemented robust `config/settings.py` using Pydantic v2 and centralized `.env` config.
- Introduced `get_settings()` / `reset_settings()` singleton pattern.
- Validated provider registration, configuration, and interface compliance.

### Phase 3: Prompt Builder + Template Workflow
- Built prompt builder architecture and workflow-oriented templates.
- Added generic template discovery and metadata validation.
- Designed schema-driven prompt construction for reusable workflows.

### Phase 4: Dry-run Ingestion Pipeline
- Implemented ingest flow core skeleton and validation scaffolding.
- Added normalization and metadata sanitization modules.
- Demonstrated end-to-end dry-run ingestion without live write operations.

### Phase 5: Notion Onboarding + Datasource Inspector
- Added `notion/datasource_inspector.py` and guided onboarding helpers.
- Implemented safe Notion datasource discovery, inspection, validation, and creation.
- Created offline tests for Notion onboarding logic.

### Phase 6: Continuous Integration and Stability
- Added GitHub Actions workflow for Python 3.12 test automation.
- Ensured CI passes with no live secrets required.
- Maintained safe skipping of live provider and Notion integration tests.
- Updated `.gitignore` and README guidance for CI readiness.

---

## Current Infrastructure (Stable Foundation)

### Core Architecture
- Modular domain-agnostic core modules.
- Pydantic v2 validation for all settings and schemas.
- Provider abstraction preserved and stable.
- Settings singleton centralizes configuration.
- Directory management and environment resolution automated.

### Notion + Onboarding
- Datasource inspection and schema validation available.
- Onboarding helper functions support token validation and `.env` persistence.
- Live logic is gated and test-safe.

### Testing and CI
- Local full suite validation: `46 passed, 4 skipped`.
- CI workflow targets Ubuntu + Python 3.12.
- Live tests remain skipped without sandbox credentials.

### Package Readiness
- Requirements and environment guidance established.
- Python 3.12 compatibility prioritized.
- `README.md` includes CI badge placeholder and run instructions.

---

## Next Priorities

### 1. Full Ingestion Pipeline Productionization
- Complete `core/ingestion_engine.py` with live provider integration.
- Add `duplicate_detector.py` and robust deduplication.
- Ensure content mapping is accurate across provider formats.
- Add persistence support for both Notion datasources and databases.

### 2. Revision Engine and Enhancement Flow
- Build `revision_engine.py` for AI-assisted content improvement.
- Connect revision output back to RecallItem metadata.
- Add delta tracking and versioning support.
- Support iterative item enhancement for long-term learning.

### 3. Onboarding Experience
- Extend onboarding wizard with interactive CLI flows.
- Add guided prompts for credential setup and sandbox safety.
- Provide `setup/notion_setup.py` as a reusable onboarding module.
- Validate edge cases and configuration migration.

### 4. Packaging and Distribution
- Add packaging artifacts for wheel/SDist.
- Standardize metadata, dependencies, and entry points.
- Prepare a publishable package for internal testing.
- Document install and upgrade paths.

### 5. GUI Readiness
- Define GUI architecture and integration boundaries.
- Build a lightweight frontend shell or CLI-first UX.
- Ensure API compatibility for GUI-driven workflows.
- Keep GUI decoupled from core ingestion and provider layers.

### 6. Plugin and Provider Ecosystem
- Design plugin interfaces for new providers, sources, and sinks.
- Support provider discovery and registration.
- Build extension points for custom ingestion adapters.
- Plan plugin validation and sandbox execution.

---

## Future Architecture Goals

### Universal Recall Platform
- Support structured note ingestion, revision, search, and recall.
- Enable multi-provider execution with provider failover.
- Support hybrid storage: Notion, local files, vector database, and plugin sinks.
- Provide federated schema mapping for external knowledge sources.

### Production-grade Engineering
- Adopt CI/CD for regression prevention.
- Add linting, formatting, and static type checks.
- Implement runtime telemetry and observability.
- Harden error handling across provider and persistence boundaries.

### Extensibility and Scale
- Build plugin system for new providers and data sources.
- Support configurable workflows, user-defined templates, and custom schema maps.
- Enable runtime feature toggles: onboarding, ingestion, revision, export.
- Keep all modules loosely coupled and testable.

---

## Roadmap by Subsystem

### Onboarding Roadmap
- Current: safe Notion datasource inspector and `.env` persistence.
- Next: interactive CLI wizard, sandbox-first onboarding, automated validation.
- Future: GUI onboarding, OAuth-style provider connections, user environment guardrails.

### Ingestion Engine Roadmap
- Current: dry-run pipeline and provider-agnostic ingestion model.
- Next: real provider execution, duplicate detection, payload mapping, safe page creation.
- Future: multi-source ingestion, streaming ingestion, webhook-triggered imports.

### Revision Engine Roadmap
- Current: architecture placeholder and schema support.
- Next: AI-driven revision and enhancement workflows, delta modeling.
- Future: continuous learning loops, revision suggestions, automated refresher prompts.

### Packaging Roadmap
- Current: requirements, `.gitignore`, README, CI validation.
- Next: packaging metadata, `setup.cfg`/`pyproject.toml`, wheel builds.
- Future: PyPI release, versioned deploys, package upgrade checks.

### GUI Roadmap
- Current: CLI-first architecture with modular backend.
- Next: lightweight frontend shell, CLI + config compatibility.
- Future: web dashboard, embedded recall workspace, real-time provider status.

### Plugin / Provider Roadmap
- Current: two providers implemented and abstracted.
- Next: plugin model definition, provider registration APIs, metadata-driven provider discovery.
- Future: marketplace-style provider plugins, user-contributed adapters, provider sandboxing.

---

## Release Milestones

### M1 — Developer Beta
- Core schema validation
- Provider abstraction
- Settings and config stability
- Dry-run ingestion flow
- Local test suite and CI

### M2 — Integration Alpha
- Live provider integration support
- Notion ingestion support
- Onboarding wizard
- Revision engine skeleton
- Packaging readiness

### M3 — Public Beta
- GUI / dashboard prototype
- Plugin registration and provider extension
- Stable onboarding and live persistence
- Complete end-to-end ingestion → revision → storage flow
- Documentation and release packaging

### M4 — Public Release
- Production-grade universal recall platform
- Multiple persistence backends
- Scalable provider ecosystem
- Robust monitoring and regression-proof CI
- Public-facing install and upgrade paths

---

## Stability Principles

- Keep core modules decoupled from provider-specific logic.
- Preserve `config/settings.py` singleton semantics and Pydantic validation.
- Keep onboarding, ingestion, revision, GUI, and plugin layers modular.
- Avoid hardcoded tokens, secrets, or live integrations in core workflows.
- Validate architecture via CI and comprehensive regression testing.
- Build features incrementally with unit tests before live integration.

---

## Notes

- The roadmap is intentionally phased to support incremental delivery.
- Current foundation is stable for developer testing and further architecture work.
- Live integrations remain gated behind sandbox credentials and CI-safe skips.
- Future development should preserve the modular provider abstraction and settings-first architecture.
