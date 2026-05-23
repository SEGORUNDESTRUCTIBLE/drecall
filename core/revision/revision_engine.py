"""Adaptive revision lifecycle engine.

Coordinates revision scheduling, review updates, and deterministic
memory lifecycle transitions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, List, Optional

from core.schemas import RecallItem
from .revision_scheduler import RevisionScheduler


class RevisionEngine:
    """Revision engine that drives scheduling and review workflows."""

    def __init__(
        self,
        algorithm_name: str = "adaptive",
        persistence_sink: Optional[Any] = None,
        now_func: Optional[Any] = None,
    ) -> None:
        self.scheduler = RevisionScheduler(
            algorithm_name=algorithm_name,
            persistence_sink=persistence_sink,
            now_func=now_func,
        )

    def schedule_item(self, item: RecallItem) -> RecallItem:
        return self.scheduler.initialize_item(item)

    def review_item(
        self,
        item: RecallItem,
        outcome: str,
        confidence: float = 0.8,
        review_timestamp: Optional[datetime] = None,
    ) -> RecallItem:
        return self.scheduler.apply_review(item, outcome=outcome, confidence=confidence, review_timestamp=review_timestamp)

    def get_due_items(self, items: Iterable[RecallItem], as_of: Optional[datetime] = None) -> List[RecallItem]:
        return self.scheduler.get_due_items(items, as_of=as_of)

    def summarize_item(self, item: RecallItem) -> str:
        metadata = item.revision_metadata or {}
        state = metadata.get("state", "NEW")
        interval = metadata.get("interval_days", 0)
        next_review = metadata.get("next_review_at")
        strength = metadata.get("recall_strength", 0.0)
        confidence = metadata.get("confidence", 0.0)
        return (
            f"Review summary for '{item.title}': state={state}, interval={interval}d, "
            f"next_review_at={next_review}, recall_strength={strength}, confidence={confidence}"
        )
