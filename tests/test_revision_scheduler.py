#!/usr/bin/env python3
"""Unit tests for the dRecall revision scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.revision.revision_scheduler import RevisionScheduler
from core.schemas import RecallItem


def test_initialize_item_populates_revision_metadata() -> None:
    item = RecallItem(title="Test Note", content="A sample recall item for scheduling.", difficulty="high", recall_priority="urgent")
    scheduler = RevisionScheduler(now_func=lambda: datetime(2026, 5, 23, tzinfo=timezone.utc))

    scheduled = scheduler.initialize_item(item)

    assert scheduled.revision_metadata
    assert scheduled.revision_metadata["state"] == "NEW"
    assert scheduled.revision_metadata["interval_days"] == 1
    assert scheduled.revision_metadata["next_review_at"] == "2026-05-24T00:00:00+00:00"
    assert scheduled.revision_metadata["review_count"] == 0


def test_get_due_items_includes_unscheduled_and_expired_items() -> None:
    scheduler = RevisionScheduler(now_func=lambda: datetime(2026, 5, 23, tzinfo=timezone.utc))
    unscheduled = RecallItem(title="Fresh", content="Fresh item with no schedule.")
    due = RecallItem(title="Expired", content="Already due.", revision_metadata={"next_review_at": "2026-05-22T00:00:00+00:00"})
    future = RecallItem(title="Future", content="Not due yet.", revision_metadata={"next_review_at": "2026-05-25T00:00:00+00:00"})

    due_items = scheduler.get_due_items([unscheduled, due, future])

    assert len(due_items) == 2
    assert any(item.title == "Fresh" for item in due_items)
    assert any(item.title == "Expired" for item in due_items)


def test_apply_review_transitions_state_and_history() -> None:
    scheduler = RevisionScheduler(now_func=lambda: datetime(2026, 5, 23, tzinfo=timezone.utc))
    item = RecallItem(title="Review Me", content="Content for review.")
    item = scheduler.initialize_item(item)

    reviewed = scheduler.apply_review(item, outcome="correct", confidence=0.9)

    assert reviewed.revision_metadata["review_count"] == 1
    assert reviewed.revision_metadata["state"] in {"REVIEW", "STRONG"}
    assert reviewed.revision_metadata["confidence"] == 0.9
    assert reviewed.revision_metadata["review_events"]
    assert reviewed.revision_metadata["review_events"][-1]["outcome"] == "correct"


def test_apply_review_forgotten_resets_interval() -> None:
    scheduler = RevisionScheduler(now_func=lambda: datetime(2026, 5, 23, tzinfo=timezone.utc))
    item = RecallItem(title="Memory", content="Memory content.")
    item = scheduler.initialize_item(item)

    forgotten = scheduler.apply_review(item, outcome="forgotten", confidence=0.2)

    assert forgotten.revision_metadata["state"] == "FORGOTTEN"
    assert forgotten.revision_metadata["interval_days"] == 1
    assert forgotten.revision_metadata["recall_strength"] <= 0.2
