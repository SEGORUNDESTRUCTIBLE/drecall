"""Revision lifecycle facade.

Delegates to the revision package and preserves the existing
`core.revision_engine.RevisionEngine` import path.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, List, Optional

from .schemas import RecallItem
from .revision.revision_engine import RevisionEngine as RevisionLifecycleEngine


class RevisionEngine:
    """Facade for the adaptive revision lifecycle engine."""

    def __init__(
        self,
        algorithm_name: str = "adaptive",
        persistence_sink: Optional[Any] = None,
        now_func: Optional[Any] = None,
    ) -> None:
        self.engine = RevisionLifecycleEngine(
            algorithm_name=algorithm_name,
            persistence_sink=persistence_sink,
            now_func=now_func,
        )

    def schedule_item(self, item: RecallItem) -> RecallItem:
        return self.engine.schedule_item(item)

    def review_item(
        self,
        item: RecallItem,
        outcome: str,
        confidence: float = 0.8,
        review_timestamp: Optional[datetime] = None,
    ) -> RecallItem:
        return self.engine.review_item(
            item,
            outcome=outcome,
            confidence=confidence,
            review_timestamp=review_timestamp,
        )

    def get_due_items(self, items: Iterable[RecallItem], as_of: Optional[datetime] = None) -> List[RecallItem]:
        return self.engine.get_due_items(items, as_of=as_of)

    def summarize_item(self, item: RecallItem) -> str:
        return self.engine.summarize_item(item)

    def enhance_content(self, item: RecallItem) -> str:
        return self.engine.summarize_item(item)

    def expand_item(self, item: RecallItem) -> RecallItem:
        return item

    def generate_summary(self, item: RecallItem) -> str:
        return self.engine.summarize_item(item)

    def revise_batch(self, items: List[RecallItem]) -> List[RecallItem]:
        return [self.engine.schedule_item(item) for item in items]
