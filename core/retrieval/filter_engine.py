"""Filtering utilities for recall and memory state retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from core.schemas import RecallItem


class FilterEngine:
    """Filter engine for due items, weak memories, duplicates, and failed items."""

    WEAK_STATES = {"WEAK", "FORGOTTEN"}
    FAILED_OUTCOMES = {"forgotten", "partial"}

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    def due_items(self, items: Iterable[RecallItem], as_of: Optional[datetime] = None) -> List[RecallItem]:
        now = as_of or datetime.now(timezone.utc)
        due: List[RecallItem] = []
        for item in items:
            next_review = self._parse_datetime(item.revision_metadata.get("next_review_at"))
            if next_review is None or next_review <= now:
                due.append(item)
        return due

    def weak_items(self, items: Iterable[RecallItem], threshold: float = 0.5) -> List[RecallItem]:
        weak: List[RecallItem] = []
        for item in items:
            metadata = item.revision_metadata or {}
            score = float(metadata.get("recall_strength", 0.0))
            if metadata.get("state", "NEW").upper() in self.WEAK_STATES or score < threshold:
                weak.append(item)
        return weak

    def failed_items(self, items: Iterable[RecallItem]) -> List[RecallItem]:
        failed: List[RecallItem] = []
        for item in items:
            events = item.revision_metadata.get("review_events", []) if item.revision_metadata else []
            if any(event.get("outcome") in self.FAILED_OUTCOMES for event in events):
                failed.append(item)
        return failed

    def duplicate_groups(self, items: Iterable[RecallItem]) -> List[List[RecallItem]]:
        groups: Dict[str, List[RecallItem]] = {}
        for item in items:
            fingerprint = item.duplicate_fingerprint or ""
            if not fingerprint:
                continue
            groups.setdefault(fingerprint, []).append(item)
        return [group for group in groups.values() if len(group) > 1]

    def filter_by_subject(self, items: Iterable[RecallItem], subject: str) -> List[RecallItem]:
        normalized = subject.strip().lower()
        return [item for item in items if normalized in (item.subject or "").lower()]

    def filter_by_tag(self, items: Iterable[RecallItem], tag: str) -> List[RecallItem]:
        normalized = tag.strip().lower()
        return [item for item in items if any(normalized == t.strip().lower() for t in item.tags)]

    def recent_items(self, items: Iterable[RecallItem], limit: int = 20) -> List[RecallItem]:
        return sorted(items, key=lambda item: item.updated_at, reverse=True)[:limit]
