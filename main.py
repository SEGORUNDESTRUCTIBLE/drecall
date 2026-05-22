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

from config import get_settings
from core.schemas import RecallItem
from providers import BaseProvider, GroqProvider, GeminiProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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
        # Load settings
        settings = get_settings()
        
        logger.info(f"=" * 60)
        logger.info(f"Starting {settings.app_name} v{settings.version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Active providers: {settings.get_active_providers()}")
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
        logger.error(f"Fatal error: {e}", exc_info=settings.debug if 'settings' in locals() else True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
