"""Terminal ingestion workflow for dRecall (Phase 7D).

Provides a synchronous, terminal-only end-to-end ingestion loop that
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
from core.validators import Validator
from core.revision_engine import RevisionEngine
from core.schemas import RecallItem
from config.settings import get_settings

try:
    from notion.notion_sink import NotionSink
except Exception:
    NotionSink = None

from duplicate.backends.hybrid_duplicate_detector import HybridDuplicateDetector


LOG = logging.getLogger("drecall.main")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


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


def main() -> None:
    # Startup banner
    os.system("cls" if os.name == "nt" else "clear")
    print("=== dRecall Terminal Ingestion (Phase 7D) ===\n")

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

    ingestion = IngestionEngine(provider=provider)
    normalizer = Normalizer()
    validator = Validator()
    revision_engine = RevisionEngine()

    # Initialize Notion sink if available and environment provides token
    notion_client = None
    notion_sink = None
    datasource_map = {}
    if NotionSink is not None:
        try:
            # optional: create a Notion client if env is configured
            from notion_client import Client as NotionClient  # type: ignore

            token = os.environ.get("NOTION_TOKEN")
            if token:
                notion_client = NotionClient(auth=token)
                datasource_map = {"notion_default": {}}
                notion_sink = NotionSink(client=notion_client, datasource_map=datasource_map)
            else:
                # Allow operating without a configured Notion client
                notion_sink = NotionSink(client=None, datasource_map=datasource_map)
        except Exception:
            notion_sink = NotionSink(client=None, datasource_map=datasource_map)

    # Duplicate detector
    detector = HybridDuplicateDetector()

    # In-memory existing items (runtime cache) to support pre-ingest checks
    existing_items: List[Dict[str, Any]] = []

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

    # Main loop
    while True:
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
            item_dict = recall_item.to_dict()
            item_dict["datasource_id"] = selected_datasource

            # Duplicate detection (pre-ingest)
            LOG.info("Running duplicate detection")
            dup_result = detector.find_duplicates(candidate=item_dict, existing=existing_items)
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
                # schedule revision hook locally
                LOG.info("Queuing for revision (local)")
                # simple in-memory revision queue placeholder
                # revision_engine.expand_item would be scheduled here in production
                existing_items.append({"id": None, "title": recall_item.title, "content": recall_item.content, "datasource_id": selected_datasource})
                continue

            LOG.info("Persisting to Notion sink")
            try:
                persist_res = notion_sink.create(item_dict)
                print(f"Persisted: page_id={persist_res.id}")
                # update runtime existing items
                existing_items.append({"id": persist_res.id, "title": recall_item.title, "content": recall_item.content, "datasource_id": selected_datasource})
                # schedule revision (placeholder)
                LOG.info("Scheduling revision hook for item %s", persist_res.id)
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
"""Main entry point for drecall application.

Orchestrates the initialization, configuration, and execution of the drecall system.
Demonstrates provider initialization and basic validation.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from core.schemas import RecallItem
from providers import BaseProvider, GroqProvider, GeminiProvider

# Configure logging from settings once available
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def initialize_providers(settings) -> dict[str, BaseProvider]:
    """Initialize configured AI providers.
    
    Args:
        settings: Application settings.
        
    Returns:
        Dictionary of initialized provider instances.
    """
    providers = {}
    
    # Initialize Groq if enabled and configured
    if settings.is_provider_enabled("groq"):
        try:
            groq = GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                timeout=settings.request_timeout,
            )
            providers["groq"] = groq
            logger.info(f"Initialized Groq provider (model: {settings.groq_model})")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq provider: {e}")
    
    # Initialize Gemini if enabled and configured
    if settings.is_provider_enabled("gemini"):
        try:
            gemini = GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                timeout=settings.request_timeout,
            )
            providers["gemini"] = gemini
            logger.info(f"Initialized Gemini provider (model: {settings.gemini_model})")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini provider: {e}")
    
    if not providers:
        logger.warning("No AI providers initialized! Check configuration and API keys.")
    
    return providers


def validate_providers(providers: dict[str, BaseProvider]) -> bool:
    """Validate all initialized providers.
    
    Args:
        providers: Dictionary of provider instances.
        
    Returns:
        True if all providers are valid, False otherwise.
    """
    logger.info("Validating providers...")
    all_valid = True
    
    for name, provider in providers.items():
        try:
            if provider.validate_credentials():
                info = provider.get_model_info()
                logger.info(f"✓ {name} provider validated (model: {info['model']})")
            else:
                logger.error(f"✗ {name} provider credentials invalid")
                all_valid = False
        except Exception as e:
            logger.error(f"✗ {name} provider validation failed: {e}")
            all_valid = False
    
    return all_valid


def main() -> int:
    """Main application entry point.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        settings.validate_configuration()

        logger.info(f"=" * 60)
        logger.info(f"Starting {settings.app_name} v{settings.version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Active providers: {settings.get_active_providers()}")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"=" * 60)
        
        # Initialize providers
        providers = initialize_providers(settings)
        
        if not providers:
            logger.error("No providers available. Configure API keys in .env")
            return 1
        
        # Validate providers
        # Note: This will attempt actual API calls if providers are configured
        if not validate_providers(providers):
            logger.warning("Some providers failed validation (check API keys)")
        
        # Demonstrate RecallItem schema
        demo_item = RecallItem(
            title="Python List Comprehensions",
            content="A list comprehension provides a concise way to create lists...",
            source="coding_notes",
            template_type="coding",
            tags=["python", "programming", "syntax"],
        )
        logger.info(f"Created sample RecallItem: {demo_item}")
        logger.debug(f"RecallItem data: {demo_item.to_dict()}")
        
        logger.info(f"=" * 60)
        logger.info("✓ dRecall initialized successfully!")
        logger.info("Ready for data ingestion and processing.")
        logger.info(f"=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=settings.debug)
        return 1


if __name__ == "__main__":
    sys.exit(main())
