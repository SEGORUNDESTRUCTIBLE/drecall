"""Text normalization utilities.

Provides text preprocessing and normalization for consistent processing.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Union


class Normalizer:
    """Text normalizer for preprocessing content.
    
    Handles text normalization including whitespace handling,
    character encoding, and formatting standardization.
    """

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text content.
        
        Args:
            text: Text to normalize.
            
        Returns:
            Normalized text.
        """
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned

    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize title text.
        
        Args:
            title: Title to normalize.
            
        Returns:
            Normalized title.
        """
        normalized = Normalizer.normalize_text(title)
        if not normalized:
            return normalized
        normalized = re.sub(r"[_]+", " ", normalized)
        words = [word if word.isupper() else word.capitalize() for word in normalized.split()]
        return " ".join(words)

    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        """Normalize tag list.
        
        Args:
            tags: List of tags.
            
        Returns:
            List of normalized tags.
        """
        normalized = [tag.strip().lower() for tag in tags if isinstance(tag, str) and tag.strip()]
        return sorted(dict.fromkeys(normalized))

    @staticmethod
    def normalize_subject(subject: Any) -> Optional[str]:
        if subject is None:
            return None
        if isinstance(subject, str):
            return Normalizer.normalize_text(subject).title()
        return str(subject)

    @staticmethod
    def normalize_system(system: Any) -> Optional[str]:
        if system is None:
            return None
        if isinstance(system, str):
            return Normalizer.normalize_text(system).upper()
        return str(system)

    @staticmethod
    def normalize_error_type(error_type: Any) -> Optional[str]:
        if error_type is None:
            return None
        if isinstance(error_type, str):
            normalized = Normalizer.normalize_text(error_type)
            return normalized[0].upper() + normalized[1:] if normalized else normalized
        return str(error_type)

    @staticmethod
    def normalize_pattern_type(pattern_type: Any) -> Optional[str]:
        if pattern_type is None:
            return None
        if isinstance(pattern_type, str):
            return Normalizer.normalize_text(pattern_type).title()
        return str(pattern_type)

    @staticmethod
    def normalize_difficulty(difficulty: Any) -> Optional[str]:
        if difficulty is None:
            return None
        if isinstance(difficulty, str):
            value = difficulty.strip().lower()
            if value in {"low", "medium", "high"}:
                return value
            return value
        return str(difficulty)

    @staticmethod
    def normalize_priority(priority: Any) -> Optional[str]:
        if priority is None:
            return None
        if isinstance(priority, str):
            value = priority.strip().lower()
            if value in {"low", "medium", "high", "urgent"}:
                return value
            return value
        return str(priority)

    @staticmethod
    def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata values and enforce consistent structure."""
        def sanitize(value: Any) -> Any:
            if value is None:
                return value
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, dict):
                return {str(k): sanitize(v) for k, v in value.items()}
            if isinstance(value, list):
                return [sanitize(v) for v in value]
            try:
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                return str(value)

        return {str(key): sanitize(val) for key, val in metadata.items()}
