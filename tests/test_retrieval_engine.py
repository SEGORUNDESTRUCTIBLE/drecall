#!/usr/bin/env python3
"""Retrieval engine tests for dRecall.

Validates keyword search, weak/due/failed filtering, export snapshots,
load snapshot, and memory health metrics.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from core.retrieval import RetrievalEngine
from core.schemas import RecallItem


def make_item(
    title: str,
    content: str,
    tags: List[str],
    subject: str,
    state: str,
    next_review_at: str,
    recall_strength: float,
    review_outcome: str,
) -> RecallItem:
    return RecallItem(
        id=title.lower().replace(" ", "_"),
        title=title,
        content=content,
        tags=tags,
        subject=subject,
        revision_metadata={
            "state": state,
            "next_review_at": next_review_at,
            "recall_strength": recall_strength,
            "review_events": [{"outcome": review_outcome}],
        },
        updated_at=datetime.now(timezone.utc),
    )


def test_search_engine_filters_and_state() -> None:
    engine = RetrievalEngine()
    items = [
        make_item(
            "Hypertension Basics",
            "High blood pressure management and lifestyle intervention.",
            ["cardiology", "hypertension"],
            "Cardiology",
            "ACTIVE",
            (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            0.8,
            "correct",
        ),
        make_item(
            "Diabetes Review",
            "Insulin dosing and patient education.",
            ["endocrinology", "diabetes"],
            "Endocrinology",
            "WEAK",
            (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            0.3,
            "forgotten",
        ),
    ]

    matches = engine.search_items(items, keyword="insulin")
    assert len(matches) == 1
    assert matches[0].title == "Diabetes Review"

    tag_matches = engine.search_items(items, tags=["cardiology"])
    assert len(tag_matches) == 1
    assert tag_matches[0].subject == "Cardiology"

    state_matches = engine.search_items(items, state="WEAK")
    assert len(state_matches) == 1
    assert state_matches[0].title == "Diabetes Review"

    subject_matches = engine.search_items(items, subject="cardio")
    assert len(subject_matches) == 1
    assert subject_matches[0].title == "Hypertension Basics"


def test_review_due_weak_and_failed_filters() -> None:
    engine = RetrievalEngine()
    now = datetime.now(timezone.utc)
    items = [
        make_item(
            "Soon Due",
            "Due item example.",
            ["test"],
            "General",
            "ACTIVE",
            (now - timedelta(minutes=5)).isoformat(),
            0.9,
            "correct",
        ),
        make_item(
            "Weak Memory",
            "Low strength memory.",
            ["test"],
            "General",
            "WEAK",
            (now + timedelta(days=2)).isoformat(),
            0.2,
            "partial",
        ),
    ]

    due = engine.review_due(items, as_of=now)
    assert len(due) == 1
    assert due[0].title == "Soon Due"

    weak = engine.review_weak(items)
    assert len(weak) == 1
    assert weak[0].title == "Weak Memory"

    failed = engine.failed_items(items)
    assert len(failed) == 1
    assert failed[0].title == "Weak Memory"

    # Mark one more failure and verify the count increases
    items[0].revision_metadata["review_events"].append({"outcome": "forgotten"})
    failed = engine.failed_items(items)
    assert len(failed) == 2


def test_snapshot_export_and_load_roundtrip(tmp_path: Path) -> None:
    engine = RetrievalEngine()
    items = [
        make_item(
            "Snapshot Test",
            "Ensure snapshot export works.",
            ["archive"],
            "Testing",
            "ACTIVE",
            datetime.now(timezone.utc).isoformat(),
            0.7,
            "correct",
        )
    ]

    snapshot_path = tmp_path / "snapshot.json"
    engine.snapshot_items(items, str(snapshot_path))

    assert snapshot_path.exists(), "Snapshot file should be written"
    loaded = engine.load_snapshot(str(snapshot_path))
    assert len(loaded) == 1
    assert loaded[0].title == "Snapshot Test"

    # validate JSON file structure
    raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    assert raw[0]["title"] == "Snapshot Test"


def test_memory_health_metrics() -> None:
    engine = RetrievalEngine()
    now = datetime.now(timezone.utc)
    items = [
        make_item(
            "Health One",
            "Quality content example.",
            ["health"],
            "General",
            "WEAK",
            (now - timedelta(days=1)).isoformat(),
            0.4,
            "forgotten",
        ),
        make_item(
            "Health Two",
            "Strong memory example.",
            ["health"],
            "General",
            "ACTIVE",
            (now + timedelta(days=3)).isoformat(),
            0.9,
            "correct",
        ),
    ]

    metrics = engine.memory_health(items)
    assert metrics["total_memory_items"] == 2
    assert metrics["weak_memory_density"] >= 0.5
    assert metrics["review_load"] >= 0.5
    assert metrics["failed_items"] == 1
    assert "last_updated" in metrics


def test_memory_health_state_counts() -> None:
    engine = RetrievalEngine()
    now = datetime.now(timezone.utc)
    items = [
        make_item(
            "State One",
            "State count example.",
            ["state"],
            "General",
            "ACTIVE",
            (now + timedelta(days=1)).isoformat(),
            0.8,
            "correct",
        ),
        make_item(
            "State Two",
            "State count example.",
            ["state"],
            "General",
            "WEAK",
            (now - timedelta(days=1)).isoformat(),
            0.3,
            "partial",
        ),
    ]

    metrics = engine.memory_health(items)
    assert metrics["state_counts"]["ACTIVE"] == 1
    assert metrics["state_counts"]["WEAK"] == 1
    assert metrics["total_memory_items"] == 2
