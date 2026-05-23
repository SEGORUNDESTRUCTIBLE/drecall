"""Core processing engine for drecall.

Provides data processing, validation, normalization, and recall functionality.
All modules use the standardized RecallItem schema for data interchange.

Key modules:
- schemas: Pydantic models for data validation (RecallItem, ProviderResponse, etc.)
- validators: Input and content validation
- normalizers: Text preprocessing and normalization
- prompt_builder: AI prompt construction
- ingestion_engine: Data import from various sources
- revision_engine: AI-powered content enhancement
- duplicate_detector: Similarity detection and deduplication
"""

from .duplicate_detector import DuplicateDetector
from .ingestion_engine import IngestionEngine
from .normalizers import Normalizer
from .prompt_builder import PromptBuilder
from .revision_engine import RevisionEngine
from .retrieval import RetrievalEngine
from .runtime import RuntimeLoader, SessionManager, RuntimeState
from .schemas import ProcessingResult, ProviderResponse, RecallItem
from .validators import Validator

__all__ = [
    "RecallItem",
    "ProcessingResult",
    "ProviderResponse",
    "Validator",
    "Normalizer",
    "PromptBuilder",
    "IngestionEngine",
    "DuplicateDetector",
    "RevisionEngine",
    "RetrievalEngine",
    "RuntimeLoader",
    "SessionManager",
    "RuntimeState",
]
