"""Revision scheduler for due item filtering and review updates."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .revision_algorithms import ReviewOutcome, RevisionSchedule
from .revision_registry import RevisionRegistry
from core.schemas import RecallItem


class RevisionScheduler:
    """Scheduler that manages item review lifecycle and due item selection."""

    def __init__(
        self,
        algorithm_name: str = "adaptive",
        persistence_sink: Optional[Any] = None,
        now_func: Optional[Any] = None,
    ) -> None:
        self.algorithm = RevisionRegistry.get_algorithm(algorithm_name)
        self.persistence_sink = persistence_sink
        self.now = now_func or (lambda: datetime.now(timezone.utc))

    def initialize_item(self, item: RecallItem) -> RecallItem:
        metadata = deepcopy(item.revision_metadata or {})
        if metadata.get("next_review_at"):
            return item

        schedule = self.algorithm.initial_schedule(self._build_schedule_context(item), now=self.now())
        metadata.update(self._schedule_to_dict(schedule))
        metadata.update(self._build_schedule_context(item))
        updated = item.model_copy(update={"revision_metadata": metadata})
        return updated

    def get_due_items(self, items: Iterable[RecallItem], as_of: Optional[datetime] = None) -> List[RecallItem]:
        now = as_of or self.now()
        due: List[RecallItem] = []
        for item in items:
            metadata = item.revision_metadata or {}
            next_review_at = self._parse_datetime(metadata.get("next_review_at"))
            if next_review_at is None or next_review_at <= now:
                due.append(item)
        return due

    def apply_review(
        self,
        item: RecallItem,
        outcome: str,
        confidence: float = 0.8,
        review_timestamp: Optional[datetime] = None,
    ) -> RecallItem:
        review_timestamp = review_timestamp or self.now()
        try:
            if outcome.upper() in ReviewOutcome.__members__:
                outcome_enum = ReviewOutcome[ outcome.upper() ]
            else:
                outcome_enum = ReviewOutcome(outcome)
        except ValueError:
            outcome_enum = ReviewOutcome.CORRECT
        updated_metadata = deepcopy(item.revision_metadata or {})
        updated_metadata["last_reviewed_at"] = review_timestamp.isoformat()
        updated_metadata["difficulty"] = item.difficulty or updated_metadata.get("difficulty", "medium")
        updated_metadata["recall_priority"] = item.recall_priority or updated_metadata.get("recall_priority", "medium")

        schedule = self.algorithm.calculate_next(updated_metadata, outcome_enum, confidence, now=review_timestamp)
        updated_metadata.update(self._schedule_to_dict(schedule))
        updated_metadata["review_events"] = updated_metadata.get("review_events", []) + [
            {
                "outcome": outcome_enum.value,
                "confidence": confidence,
                "reviewed_at": review_timestamp.isoformat(),
                "interval_days": schedule.interval_days,
                "state": schedule.state,
            }
        ]

        if item.duplicate_fingerprint:
            updated_metadata["duplicate_fingerprint"] = item.duplicate_fingerprint

        updated_item = item.model_copy(update={"revision_metadata": updated_metadata})
        self._persist_review(item, updated_item)
        return updated_item

    def _persist_review(self, original_item: RecallItem, updated_item: RecallItem) -> None:
        if self.persistence_sink is None or getattr(self.persistence_sink, "update", None) is None:
            return

        if not original_item.id:
            return

        try:
            self.persistence_sink.update(original_item.id, {"revision_metadata": updated_item.revision_metadata})
        except Exception:
            return

    def _schedule_to_dict(self, schedule: RevisionSchedule) -> Dict[str, Any]:
        return {
            "state": schedule.state,
            "interval_days": schedule.interval_days,
            "next_review_at": schedule.next_review_at.isoformat(),
            "last_reviewed_at": schedule.last_reviewed_at.isoformat() if schedule.last_reviewed_at else None,
            "confidence": schedule.confidence,
            "recall_strength": schedule.recall_strength,
            "ease_factor": schedule.ease_factor,
            "review_count": schedule.review_count,
            "consecutive_correct": schedule.consecutive_correct,
            "algorithm": schedule.algorithm,
        }

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None
        return None

    def _build_schedule_context(self, item: RecallItem) -> Dict[str, Any]:
        return {
            "difficulty": item.difficulty or "medium",
            "recall_priority": item.recall_priority or "medium",
            "duplicate_fingerprint": item.duplicate_fingerprint,
        }
