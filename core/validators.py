"""Data validation utilities.

Provides validation for recall items and user inputs.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from .schemas import RecallItem


class Validator:
    """Validator for recall items and input data.
    
    Performs comprehensive validation including schema validation,
    content validation, and business logic validation.
    """

    @staticmethod
    def validate_recall_item(item: RecallItem) -> Tuple[bool, List[str]]:
        """Validate a recall item.
        
        Args:
            item: RecallItem to validate.
            
        Returns:
            Tuple of (is_valid, error_messages).
        """
        errors: List[str] = []

        if not item.title or not item.title.strip():
            errors.append("Title must be a non-empty string.")
        elif len(item.title.strip()) > 200:
            errors.append("Title must be shorter than 200 characters.")

        if not item.content or not item.content.strip():
            errors.append("Content must be a non-empty string.")
        elif len(item.content.strip()) < 10:
            errors.append("Content must be at least 10 characters long.")

        if not isinstance(item.tags, list):
            errors.append("Tags must be a list.")
        else:
            invalid_tags = [tag for tag in item.tags if not isinstance(tag, str) or not tag.strip()]
            if invalid_tags:
                errors.append("All tags must be non-empty strings.")

        if not isinstance(item.metadata, dict):
            errors.append("Metadata must be a dictionary.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_content(content: str) -> Tuple[bool, Optional[str]]:
        """Validate content text.
        
        Args:
            content: Content text to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not content or not isinstance(content, str) or not content.strip():
            return False, "Content must be a non-empty string."
        if len(content.strip()) < 10:
            return False, "Content must be at least 10 characters long."
        return True, None

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate custom metadata.
        
        Args:
            metadata: Metadata dictionary to validate.
            
        Returns:
            Tuple of (is_valid, error_messages).
        """
        errors: List[str] = []
        if not isinstance(metadata, dict):
            return False, ["Metadata must be a dictionary."]

        for key, value in metadata.items():
            if not isinstance(key, str):
                errors.append("Metadata keys must be strings.")
                break
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                errors.append(f"Metadata value for '{key}' is not JSON serializable.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_provider_response(raw_response: str) -> Tuple[bool, Optional[Any], Optional[str]]:
        """Validate the raw provider response payload.
        
        Args:
            raw_response: Raw response string from the provider.
            
        Returns:
            Tuple of (is_valid, parsed_value, error_message).
        """
        if not isinstance(raw_response, str) or not raw_response.strip():
            return False, None, "Provider response must be a non-empty string."

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            return False, None, f"Provider response is not valid JSON: {exc}"

        is_valid, errors = Validator.validate_structured_json(data)
        if not is_valid:
            return False, None, "; ".join(errors)

        return True, data, None

    @staticmethod
    def validate_structured_json(data: Any) -> Tuple[bool, List[str]]:
        """Validate parsed structured JSON.
        
        Args:
            data: Parsed JSON object.
            
        Returns:
            Tuple of (is_valid, errors).
        """
        errors: List[str] = []
        if not isinstance(data, (dict, list)):
            errors.append("Structured output must be a JSON object or array.")
            return False, errors

        if isinstance(data, dict) and not data:
            errors.append("Structured JSON object must not be empty.")
        if isinstance(data, list) and not data:
            errors.append("Structured JSON array must not be empty.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
        """Validate that required fields exist in a structured payload."""
        errors: List[str] = []
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        return len(errors) == 0, errors
