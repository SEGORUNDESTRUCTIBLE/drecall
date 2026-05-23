"""Terminal ingestion workflow for dRecall (Phase 8B).

Provides a synchronous, terminal-only end-to-end ingestion and review loop that
demonstrates the full pipeline without introducing async/embedding
complexity. Components are dependency-injected and loosely coupled.
"""

from __future__ import annotations

import os
import sys
import logging
from typing import List, Dict, Any

from core.ingestion_engine import IngestionEngine, MockProvider
from core.normalizers import Normalizer
from core.retrieval import RetrievalEngine
from core.runtime import RuntimeLoader, SessionManager
from core.validators import Validator
from core.revision_engine import RevisionEngine
from core.schemas import RecallItem
from config.settings import get_settings

try:
    from notion.notion_sink import NotionSink
except Exception:
    NotionSink = None
from notion.notion_manager import NotionManager

from duplicate.backends.hybrid_duplicate_detector import HybridDuplicateDetector


LOG = logging.getLogger("drecall.main")
debug_enabled = os.getenv("DRECALL_DEBUG", "").lower() in ("1", "true", "yes")
logging.basicConfig(level=logging.DEBUG if debug_enabled else logging.INFO, format="[%(levelname)s] %(message)s")
if debug_enabled:
    LOG.info("Debug logging enabled via DRECALL_DEBUG")


def select_datasource(default: str = None, datasource_map: Dict[str, Any] = None) -> str:
    datasource_map = datasource_map or {}
    keys = list(datasource_map.keys())
    if not keys:
        return default
    if default and default in keys:
        return default

    print("Available datasources:")
    for i, k in enumerate(keys, start=1):
        print(f" {i}. {k}")


def resolve_datasource_alias(alias: str, env_status: Any) -> Optional[str]:
    # The application uses logical datasource aliases for selection.
    # Resolve the alias to a concrete Notion database UUID from env config.
    if alias != "notion_default":
        return alias
    return env_status.database_id or env_status.datasource_id

    choice = input(f"Select datasource [1-{len(keys)}] or press Enter for {keys[0]}: ")
    try:
        if choice.strip() == "":
            return keys[0]
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except Exception:
        pass
    return keys[0]


def multiline_input(prompt: str = ">>> ") -> str:
    print(prompt + " (press ENTER twice to submit, type EXIT to quit)")
    lines: List[str] = []
    empty_count = 0
    while True:
        try:
            line = input()
        except EOFError:
            return ""
        if line.strip().lower() == "exit":
            return "__EXIT__"
        if line.strip() == "":
            empty_count += 1
        else:
            empty_count = 0
            lines.append(line)
        if empty_count >= 2:
            break
    return "\n".join(lines).strip()


def select_workflow() -> str:
    print("Workflow modes:")
    print(" 1. Ingest new recall note")
    print(" 2. Search memory")
    print(" 3. Review due recall items")
    print(" 4. Review weak memory")
    print(" 5. Recent items")
    print(" 6. Failed items")
    print(" 7. Memory health")
    print(" 8. Export snapshot")
    print(" 9. Exit")
    print(" T. Test Notion persistence")
    print(" V. Validate runtime lifecycle")
    choice = input("Select mode [1-9] (default 1): ")
    if choice.strip() == "2":
        return "search"
    if choice.strip() == "3":
        return "review_due"
    if choice.strip() == "4":
        return "review_weak"
    if choice.strip() == "5":
        return "recent"
    if choice.strip() == "6":
        return "failed"
    if choice.strip() == "7":
        return "health"
    if choice.strip() == "8":
        return "export"
    if choice.strip().upper() == "T":
        return "test_persistence"
    if choice.strip().upper() == "V":
        return "validate_runtime"
    if choice.strip() == "9":
        return "exit"
    return "ingest"


def render_item_snippet(item: RecallItem) -> str:
    content = item.content or ""
    excerpt = content.strip().splitlines()[0] if content.strip() else "(no content)"
    return f"{item.title} — {excerpt[:120]}"


def prompt_review_outcome() -> str:
    print("Review outcome options:")
    print(" 1. Correct")
    print(" 2. Partial")
    print(" 3. Forgotten")
    choice = input("Select outcome [1-3] or Enter to skip: ").strip()
    return {
        "1": "correct",
        "2": "partial",
        "3": "forgotten",
    }.get(choice, "")


def prompt_confidence() -> float:
    choice = input("Confidence level [1-5] (default 4): ").strip()
    try:
        value = int(choice)
        return max(1, min(5, value)) / 5.0
    except Exception:
        return 0.8


def print_items(items: List[RecallItem], max_items: int = 20) -> None:
    if not items:
        print("No matching items found.")
        return
    for index, item in enumerate(items[:max_items], start=1):
        metadata = item.revision_metadata or {}
        print(f"{index}. {render_item_snippet(item)}")
        print(f"   state={metadata.get('state', 'NEW')} subject={item.subject or 'N/A'} tags={item.tags} next={metadata.get('next_review_at')}")


def search_memory(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine) -> None:
    print("Search memory:")
    keyword = input("Keyword query (optional): ").strip() or None
    subject = input("Subject filter (optional): ").strip() or None
    tag_input = input("Tag filter(s) comma-separated (optional): ").strip()
    tags = [tag.strip() for tag in tag_input.split(",") if tag.strip()] if tag_input else None
    state = input("Revision state filter (optional): ").strip() or None

    results = retrieval_engine.search_items(
        existing_items,
        keyword=keyword,
        tags=tags,
        subject=subject,
        state=state,
    )
    print(f"Found {len(results)} matching item(s):")
    print_items(results)


def review_items(items: List[RecallItem], existing_items: List[RecallItem], revision_engine: RevisionEngine, title: str) -> None:
    if not items:
        print(f"No {title.lower()} items to review.")
        return
    print(f"{len(items)} {title.lower()} item(s):\n")
    for item in items:
        print(f"- {render_item_snippet(item)}")
        metadata = item.revision_metadata or {}
        print(f"   state={metadata.get('state', 'NEW')} next_review_at={metadata.get('next_review_at')} interval={metadata.get('interval_days', 0)}d")
        outcome = prompt_review_outcome()
        if not outcome:
            print("  Skipping item")
            continue
        confidence = prompt_confidence()
        reviewed = revision_engine.review_item(item, outcome=outcome, confidence=confidence)
        existing_items[:] = [reviewed if existing is item else existing for existing in existing_items]
        print(f"  Reviewed: state={reviewed.revision_metadata.get('state')} interval={reviewed.revision_metadata.get('interval_days')}d next={reviewed.revision_metadata.get('next_review_at')}")
        print()


def review_due_items(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine, revision_engine: RevisionEngine) -> None:
    due_items = retrieval_engine.review_due(existing_items)
    review_items(due_items, existing_items, revision_engine, "Due")


def review_weak_items(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine, revision_engine: RevisionEngine) -> None:
    weak_items = retrieval_engine.review_weak(existing_items)
    review_items(weak_items, existing_items, revision_engine, "Weak")


def recent_items(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine) -> None:
    recent = retrieval_engine.recent_items(existing_items)
    print(f"Most recent {len(recent)} item(s):")
    print_items(recent)


def failed_items(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine) -> None:
    failed = retrieval_engine.failed_items(existing_items)
    print(f"Failed or forgotten {len(failed)} item(s):")
    print_items(failed)


def memory_health(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine) -> None:
    metrics = retrieval_engine.memory_health(existing_items)
    print("Memory health metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


def export_snapshot(existing_items: List[RecallItem], retrieval_engine: RetrievalEngine) -> None:
    path = input("Export snapshot path (default ./drecall_snapshot.json): ").strip() or "./drecall_snapshot.json"
    output_path = retrieval_engine.snapshot_items(existing_items, path)
    print(f"Snapshot exported to {output_path}")


def run_test_persistence(notion_sink: Any, retrieval_engine: RetrievalEngine, existing_items: List[RecallItem]) -> None:
    print("Running persistence test (creates a temporary test page)...")
    if notion_sink is None or not notion_sink.client:
        print("Notion sink not configured. Enable Notion and provide credentials to run this test.")
        return

    # Build a small test recall item
    alias = next(iter(notion_sink.datasource_map.keys())) if notion_sink.datasource_map else None
    resolved_database_id = notion_sink.resolve_database_id(alias) if alias else None
    test_item = {
        "title": "dRecall Persistence Test",
        "content": "This is a temporary test created by dRecall to validate persistence.",
        "tags": ["drecall_test"],
        "datasource_id": alias,
    }

    ds = resolved_database_id
    if not ds:
        print("No datasource configured for Notion sink; aborting test")
        return

    # Safety: require explicit confirmation
    resp = input(f"Create a test page in datasource '{ds}'? Type YES to confirm: ")
    if resp.strip().upper() != "YES":
        print("Test aborted by user")
        return

    created = NotionManager.safe_create_test_page(notion_sink.client, ds, test_item)
    if not created:
        print("Test page creation failed — see logs")
        return

    page_id = created.get("id")
    print(f"Test page created: id={page_id}")
    # Attempt retrieval via sink
    try:
        retrieved = notion_sink.retrieve_page(page_id)
        print("Retrieved page successfully. Title preview:", retrieved.get("properties", {}).get("Title", {}))
    except Exception as exc:
        print("Failed to retrieve test page:", exc)
    print("Persistence test completed — you may delete the test page manually.")


def run_validate_runtime(
    ingestion: IngestionEngine,
    notion_sink: Any,
    existing_items: List[RecallItem],
    retrieval_engine: RetrievalEngine,
    revision_engine: RevisionEngine,
    runtime_loader: RuntimeLoader,
    session_manager: SessionManager,
) -> None:
    print("Running full lifecycle validation (ingest -> persist -> reload -> retrieve -> review)")
    samples = [
        ("Distichiasis vs Trichiasis", "Difference between distichiasis and trichiasis"),
        ("Scurvy mechanism", "Scurvy collagen defect mechanism: role of vitamin C in hydroxylation"),
        ("Tail recursion", "Tail recursion explanation and python example"),
    ]

    created_pages = []
    for title, text in samples:
        try:
            item = ingestion.ingest_text(
                text=text,
                title=title,
                source=next(iter(notion_sink.datasource_map.keys())) if notion_sink and notion_sink.datasource_map else None,
            )
        except Exception as exc:
            print(f"Ingestion failed for {title}: {exc}")
            continue

        if notion_sink and notion_sink.client:
            ds = next(iter(notion_sink.datasource_map.keys()))
            payload = item.to_dict()
            payload["datasource_id"] = ds
            try:
                res = notion_sink.create(payload)
                item = item.model_copy(update={"id": res.id})
                created_pages.append(res.id)
                print(f"Persisted {title} -> page {res.id}")
            except Exception as exc:
                print(f"Persistence failed for {title}: {exc}")
                continue

        existing_items.append(item)
        session_manager.record_item(item)

    print("Verifying local snapshot and retrieval continuity")
    try:
        reloaded_state = runtime_loader.load_runtime(load_from_notion=False, force_refresh=True)
        print(f"Reloaded {len(reloaded_state.items)} item(s) from local snapshot")
    except Exception as exc:
        print(f"Snapshot reload failed: {exc}")
        reloaded_state = None

    if retrieval_engine:
        recent = retrieval_engine.recent_items(existing_items)
        print(f"Recent items after lifecycle test: {len(recent)}")
        if reloaded_state is not None:
            reloaded_recent = retrieval_engine.recent_items(reloaded_state.items)
            print(f"Recent items after reload: {len(reloaded_recent)}")

    print("Lifecycle validation completed. Created pages:", created_pages)


def main() -> None:
    # Startup banner
    os.system("cls" if os.name == "nt" else "clear")
    print("=== dRecall Terminal Ingestion (Phase 8C) ===\n")

    # Initialize components
    LOG.info("Initializing components...")

    settings = get_settings()

    # Provider runtime selection
    provider = None
    provider_name = None
    dry_run = False
    # try preferred provider from settings
    preferred = settings.default_provider.value if hasattr(settings, 'default_provider') else None
    available = settings.get_active_providers()
    # map provider names to classes
    provider_name = preferred or (available[0] if available else None)
    try:
        if provider_name == "groq":
            from providers.groq_provider import GroqProvider

            provider = GroqProvider(api_key=settings.groq_api_key, model=settings.get_provider("groq"), timeout=settings.request_timeout, retries=settings.max_retries)
        elif provider_name == "gemini":
            from providers.gemini_provider import GeminiProvider

            provider = GeminiProvider(api_key=settings.gemini_api_key, model=settings.get_provider("gemini"), timeout=settings.request_timeout, retries=settings.max_retries)
    except Exception as e:
        LOG.warning("Failed to initialize preferred provider %s: %s", provider_name, e)
        provider = None

    if provider is None:
        # fallback to any available provider validated by credentials
        for p in ("groq", "gemini"):
            try:
                if settings.is_provider_enabled(p):
                    if p == "groq":
                        from providers.groq_provider import GroqProvider

                        candidate = GroqProvider(api_key=settings.groq_api_key, model=settings.get_provider("groq"), timeout=settings.request_timeout, retries=settings.max_retries)
                    else:
                        from providers.gemini_provider import GeminiProvider

                        candidate = GeminiProvider(api_key=settings.gemini_api_key, model=settings.get_provider("gemini"), timeout=settings.request_timeout, retries=settings.max_retries)
                    if candidate.validate_credentials():
                        provider = candidate
                        provider_name = p
                        break
            except Exception:
                continue

    if provider is None:
        LOG.warning("No working provider available; using MockProvider (dry-run)")
        provider = MockProvider()
        provider_name = "mock"
        dry_run = True

    LOG.info("Selected provider: %s", provider.__class__.__name__)
    ingestion = IngestionEngine(provider=provider)
    normalizer = Normalizer()
    validator = Validator()
    revision_engine = RevisionEngine()
    retrieval_engine = None

    # Initialize Notion sink if available and environment provides token
    notion_client = None
    notion_sink = None
    datasource_map = {}
    # Notion environment detection and safe initialization
    env_status = NotionManager.detect_env()
    alias_key = "notion_default"
    resolved_target_id = resolve_datasource_alias(alias_key, env_status)
    datasource_map = {}

    print("Persistence:", "ENABLED" if env_status.enabled else "DISABLED")
    print("Notion token:", "present" if env_status.token_present else "missing")
    print("Datasource alias:", alias_key)
    print("Resolved target ID:", resolved_target_id or "(missing)")
    print("Datasource resolution:", "VERIFIED" if resolved_target_id else "MISSING")

    if NotionSink is not None and env_status.enabled and not resolved_target_id:
        print("Notion persistence disabled: no database ID could be resolved for alias",
              alias_key)
        env_status.enabled = False

    # If token present but ENABLE_NOTION not set, offer to enable for this session
    if NotionSink is not None and not env_status.enabled and env_status.token_present:
        resp = input("Notion token detected but persistence disabled. Enable Notion for this session? Type YES to enable: ")
        if resp.strip().upper() == "YES":
            env_status.enabled = True

    if NotionSink is not None and env_status.enabled:
        notion_client = NotionManager.init_client()
        if notion_client:
            # Use a stable alias internally and resolve to a concrete database UUID.
            if resolved_target_id:
                info = None
                title_field = "Title"
                resolved_database_id = None
                datasource_entry: Dict[str, Any] = {"title": title_field}

                # Try interpreting the resolved id as a database first, then fall back to datasource.
                if env_status.database_id and resolved_target_id == env_status.database_id:
                    info = NotionManager.validate_database_access(notion_client, resolved_target_id)
                    if info.get("accessible"):
                        resolved_database_id = resolved_target_id
                        datasource_entry["database_id"] = resolved_database_id
                if not info or not info.get("accessible"):
                    if env_status.datasource_id:
                        if not info or resolved_target_id == env_status.datasource_id:
                            info = NotionManager.validate_datasource_access(notion_client, env_status.datasource_id)
                            if info.get("accessible"):
                                resolved_database_id = info.get("database_id")
                                datasource_entry["data_source_id"] = env_status.datasource_id
                                if resolved_database_id:
                                    datasource_entry["database_id"] = resolved_database_id

                if info and info.get("accessible"):
                    title = info.get("title")
                    title_field = NotionManager.inspect_schema(info.get("properties", {}))["mapping"].get("title") or "Title"
                    datasource_entry["title"] = title_field
                    datasource_map = {alias_key: datasource_entry}
                    sandbox_ok = NotionManager.is_sandbox_name(title)
                    print("Database access:", "VERIFIED")
                    print(f"Database title: {title}")
                    print(f"Schema properties: {len(info.get('properties', {}))}")
                    print(f"Mapped title field: {title_field}")
                    if not sandbox_ok:
                        resp = input("Warning: database name does not look like a sandbox. Type YES to proceed: ")
                        if resp.strip().upper() != "YES":
                            print("Notion persistence aborted by user (sandbox check)")
                            notion_client = None
                        else:
                            print("Proceeding with Notion persistence as requested")
                else:
                    print("Database access: FAILED —", info.get("error") if info else "unknown error")
                    notion_client = None
            else:
                notion_client = None

            notion_sink = NotionSink(client=notion_client, datasource_map=datasource_map)
        else:
            print("Notion client initialization failed — persistence disabled")
            notion_sink = NotionSink(client=None, datasource_map=datasource_map)
    else:
        # Not configured or disabled
        notion_sink = NotionSink(client=None, datasource_map=datasource_map) if NotionSink is not None else None

    # revision engine persistence support
    revision_engine = RevisionEngine(persistence_sink=notion_sink)
    retrieval_engine = RetrievalEngine(persistence_sink=notion_sink)

    runtime_loader = RuntimeLoader(persistence_sink=notion_sink)
    runtime_state = runtime_loader.load_runtime(load_from_notion=bool(settings.enable_notion))
    session_manager = SessionManager(runtime_state=runtime_state, snapshot_path=runtime_loader.snapshot_path)

    # Duplicate detector
    detector = HybridDuplicateDetector()

    # In-memory existing items (runtime cache) to support pre-ingest checks
    existing_items: List[RecallItem] = runtime_state.items

    # Datasource selection
    selected_datasource = select_datasource(default="notion_default", datasource_map=datasource_map)
    # Display runtime selection
    model_info = None
    try:
        model_info = provider.get_model_info() if provider and hasattr(provider, "get_model_info") else None
    except Exception:
        model_info = None

    print(f"Selected datasource: {selected_datasource}")
    print(f"Active provider: {provider_name}")
    if model_info:
        print(f"Active model: {model_info.get('model')}")
    print(f"Dry-run mode: {dry_run}\n")

    runtime_summary = runtime_state.summary()
    print("=== Runtime memory summary ===")
    print(f"Loaded items: {runtime_summary['total_items']}")
    print(f"Due review items: {runtime_summary['due_items']}")
    print(f"Weak memory items: {runtime_summary['weak_items']}")
    print(f"Unique tags: {runtime_summary['tag_count']}")
    print(f"Unique subjects: {runtime_summary['subject_count']}")
    print(f"Last sync: {runtime_summary['last_sync_at']}")
    print(f"Sync status: {runtime_summary['sync_status']}\n")

    # Main loop
    while True:
        workflow = select_workflow()
        if workflow == "exit":
            print("Exiting dRecall. Goodbye.")
            break
        if workflow == "search":
            search_memory(existing_items, retrieval_engine)
            continue
        if workflow == "review_due":
            review_due_items(existing_items, retrieval_engine, revision_engine)
            session_manager.record_items(existing_items)
            continue
        if workflow == "review_weak":
            review_weak_items(existing_items, retrieval_engine, revision_engine)
            session_manager.record_items(existing_items)
            continue
        if workflow == "recent":
            recent_items(existing_items, retrieval_engine)
            continue
        if workflow == "failed":
            failed_items(existing_items, retrieval_engine)
            continue
        if workflow == "health":
            memory_health(existing_items, retrieval_engine)
            continue
        if workflow == "export":
            export_snapshot(existing_items, retrieval_engine)
            continue
        if workflow == "test_persistence":
            run_test_persistence(notion_sink, retrieval_engine, existing_items)
            continue
        if workflow == "validate_runtime":
            run_validate_runtime(
                ingestion,
                notion_sink,
                existing_items,
                retrieval_engine,
                revision_engine,
                runtime_loader,
                session_manager,
            )
            continue

        user_input = multiline_input(prompt="Paste question / note")
        if user_input == "__EXIT__":
            print("Exiting ingestion loop. Goodbye.")
            break
        if not user_input:
            print("No input received. Try again.")
            continue

        LOG.info("Input received — starting ingestion pipeline")

        try:
            # Stage: normalize
            LOG.info("Normalizing input")
            normalized_text = normalizer.normalize_text(user_input)

            # Prevent ultra-short inputs: auto-expand minimal prompts
            instruction_override = None
            if len(normalized_text) < 20:
                LOG.info("Input very short; applying auto-expand instruction")
                instruction_override = (
                    "Expand the following into a concise structured recall note: "
                )

            # Build and run ingestion with retry and validation recovery
            LOG.info("Rendering prompt and calling provider")
            last_exc = None
            max_attempts = getattr(settings, "max_retries", 3)
            recall_item = None
            for attempt in range(1, max_attempts + 1):
                try:
                    recall_item = ingestion.ingest_text(text=normalized_text, title=None, source=selected_datasource, instruction=instruction_override)
                    break
                except Exception as exc:
                    last_exc = exc
                    LOG.warning("Provider/ingestion attempt %d failed: %s", attempt, exc)
                    # if final attempt, break
                    if attempt == max_attempts:
                        raise
                    # small backoff
                    import time

                    time.sleep(0.5 * attempt)

            if recall_item is None:
                raise RuntimeError(f"Failed to obtain structured output: {last_exc}")

            # Validate recall item
            LOG.info("Validating structured RecallItem")
            is_valid, errors = validator.validate_recall_item(recall_item)
            if not is_valid:
                LOG.error("Validation failed: %s", errors)
                # Recovery suggestion: try a more explicit instruction
                if instruction_override is None:
                    print("Validation failed — attempting recovery by requesting expanded output")
                    try:
                        recall_item = ingestion.ingest_text(text=normalized_text, title=None, source=selected_datasource, instruction="Please expand and return structured JSON with fields: title, content, tags")
                        is_valid, errors = validator.validate_recall_item(recall_item)
                        if not is_valid:
                            print("Recovery attempt failed — ingestion blocked")
                            continue
                    except Exception as e:
                        LOG.exception("Recovery ingestion failed: %s", e)
                        print("Recovery attempt failed — ingestion blocked")
                        continue
                else:
                    print("Validation failed — ingestion blocked")
                    continue

            # Prepare canonical dict for persistence (do NOT mutate original)
            scheduled_item = revision_engine.schedule_item(recall_item)
            item_dict = scheduled_item.to_dict()
            item_dict["datasource_id"] = selected_datasource

            # Duplicate detection (pre-ingest)
            LOG.info("Running duplicate detection")
            dup_result = detector.find_duplicates(candidate=item_dict, existing=[item.to_dict() for item in existing_items])
            # If duplicate backend recommends BLOCK, honor it
            from core.contracts.duplicate_contracts import RecommendedAction

            if dup_result.is_duplicate and dup_result.recommended_action == RecommendedAction.BLOCK:
                # defensive: recommended_action is Enum; compare via name
                print("Duplicate detected — ingestion blocked")
                for m in dup_result.matches:
                    print(f"- {m.title} (score={m.similarity}, type={m.type})")
                continue


            # Persistence
            if notion_sink is None or not notion_sink.client:
                LOG.info("Notion sink not configured — skipping persistence (dry-run)")
                print("Dry-run: ingestion complete (no persistence)")
                existing_items.append(scheduled_item)
                session_manager.record_item(scheduled_item)
                continue

            LOG.info("Persisting to Notion sink")
            try:
                persist_res = notion_sink.create(item_dict)
                print(f"Persisted: page_id={persist_res.id}")
                scheduled_item = scheduled_item.model_copy(update={"id": persist_res.id})
                existing_items.append(scheduled_item)
                session_manager.record_item(scheduled_item)
                LOG.info("Scheduled revision for persisted item %s", persist_res.id)
            except Exception as exc:
                LOG.exception("Persistence failed: %s", exc)
                print("Persistence failed — see logs")

        except KeyboardInterrupt:
            print("Interrupted — exiting")
            break
        except Exception as exc:
            LOG.exception("Unhandled pipeline error: %s", exc)
            print("Ingestion failed due to an internal error. See logs.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        LOG.exception("Fatal error in main: %s", e)
        sys.exit(1)
