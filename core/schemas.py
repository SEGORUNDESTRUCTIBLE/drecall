"""Pydantic schemas for data validation and serialization.

Defines the core data models used throughout the application.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RecallItem(BaseModel):
    """Main data model for a recall item (note/memory).
    
    Represents a single piece of information to be processed,
    stored, and retrieved through the drecall system.
    """
    
    id: Optional[str] = Field(None, description="Unique identifier")
    title: str = Field(..., description="Title of the recall item")
    content: str = Field(..., description="Main content/text")
    
    # Metadata
    source: Optional[str] = Field(None, description="Source of the item")
    template_type: str = Field("custom", description="Template type used")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    
    # Processing
    processed: bool = Field(False, description="Whether item has been processed")
    enhanced: bool = Field(False, description="Whether item has been enhanced")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Notion integration
    notion_page_id: Optional[str] = Field(None, description="Notion page ID if synced")
    
    # Custom metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata storage",
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Machine Learning Basics",
                "content": "A machine learning model learns patterns from data...",
                "source": "personal_notes",
                "template_type": "coding",
                "tags": ["ml", "ai", "learning"],
            }
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation of the recall item.
        """
        return self.model_dump(mode="json")
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"RecallItem(id={self.id}, title={self.title})"


class ProcessingResult(BaseModel):
    """Result of processing a recall item."""
    
    item_id: str = Field(..., description="ID of processed item")
    success: bool = Field(..., description="Whether processing succeeded")
    message: str = Field(..., description="Status message")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    """Unified response format from all AI providers.
    
    Standardizes outputs from different providers (Groq, Gemini, etc.)
    so the rest of the system doesn't need to know which provider was used.
    
    This schema is essential to provider-agnostic architecture.
    """
    
    provider: str = Field(..., description="Provider name (groq, gemini, etc)")
    model: str = Field(..., description="Model name/version used")
    text: str = Field(..., description="Generated text response")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed (if available)")
    latency_ms: float = Field(..., description="Request latency in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")
    
    def __repr__(self) -> str:
        """Return string representation."""
        status = "success" if not self.error else "failed"
        return f"ProviderResponse(provider={self.provider}, model={self.model}, status={status}, latency={self.latency_ms}ms)"
