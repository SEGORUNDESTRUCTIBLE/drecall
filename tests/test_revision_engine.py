#!/usr/bin/env python3
"""Integration tests for the revision engine facade."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.revision_engine import RevisionEngine
from core.schemas import RecallItem


def test_revision_engine_schedules_new_item() -> None:
    engine = RevisionEngine()
    item = RecallItem(title="Blade Runner", content="Memory recall test.", difficulty="medium", recall_priority="high")

    scheduled = engine.schedule_item(item)

    assert scheduled.revision_metadata["state"] == "NEW"
    assert scheduled.revision_metadata["interval_days"] == 1
    assert scheduled.revision_metadata["next_review_at"]


def test_revision_engine_reviews_due_item() -> None:
    engine = RevisionEngine()
    item = RecallItem(title="Physics", content="Practice recall for physics.")
    item = engine.schedule_item(item)

    reviewed = engine.review_item(item, outcome="partial", confidence=0.6)

    assert reviewed.revision_metadata["review_count"] == 1
    assert reviewed.revision_metadata["state"] in {"LEARNING", "REVIEW", "FORGOTTEN"}
    assert reviewed.revision_metadata["confidence"] == 0.6


def test_revision_engine_filters_due_items() -> None:
    now = datetime(2026, 5, 23, tzinfo=timezone.utc)
    engine = RevisionEngine(now_func=lambda: now)
    scheduled = engine.schedule_item(RecallItem(title="A", content="A note."))
    scheduled = engine.review_item(scheduled, outcome="correct", confidence=0.8)
    scheduled.revision_metadata["next_review_at"] = (now - timedelta(days=1)).isoformat()

    due_items = engine.get_due_items([scheduled], as_of=now)
    assert len(due_items) == 1
