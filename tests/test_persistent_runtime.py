#!/usr/bin/env python3
"""Persistent runtime tests for dRecall session continuity."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.runtime.runtime_loader import RuntimeLoader
from core.runtime.session_manager import SessionManager
from core.schemas import RecallItem


def test_session_manager_persists_snapshot(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    recall_item = RecallItem(
        id="session-item",
        title="Session Item",
        content="Session persistence content.",
        tags=["session", "runtime"],
        subject="Operational",
        revision_metadata={
            "state": "ACTIVE",
            "next_review_at": now.isoformat(),
        },
        created_at=now,
        updated_at=now,
    )

    runtime_state = RuntimeLoader(snapshot_path=tmp_path / "runtime_snapshot.json").load_runtime(load_from_notion=False)
    session_manager = SessionManager(runtime_state=runtime_state, snapshot_path=tmp_path / "runtime_snapshot.json")
    session_manager.record_item(recall_item)

    persisted = json.loads((tmp_path / "runtime_snapshot.json").read_text(encoding="utf-8"))
    assert persisted["items"]
    assert persisted["items"][0]["id"] == "session-item"
    assert persisted["sync_metadata"]["last_saved_at"]

    # rehydrate from file and ensure continuity
    loader = RuntimeLoader(snapshot_path=tmp_path / "runtime_snapshot.json", notion_fetcher=None)
    reloaded_state = loader.load_runtime(load_from_notion=False)
    assert len(reloaded_state.items) == 1
    assert reloaded_state.items[0].title == "Session Item"
    assert reloaded_state.summary()["total_items"] == 1


def test_runtime_state_indexes_tags_and_subjects(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    item = RecallItem(
        id="index-item",
        title="Index Test",
        content="Indexing content.",
        tags=["runtime", "index"],
        subject="Testing",
        revision_metadata={"state": "ACTIVE", "next_review_at": now.isoformat()},
        created_at=now,
        updated_at=now,
    )

    runtime_state = RuntimeLoader(snapshot_path=tmp_path / "runtime_snapshot.json").load_runtime(load_from_notion=False)
    session_manager = SessionManager(runtime_state=runtime_state, snapshot_path=tmp_path / "runtime_snapshot.json")
    session_manager.record_item(item)

    assert runtime_state.tags["runtime"][0].id == "index-item"
    assert runtime_state.subjects["testing"][0].title == "Index Test"
    assert runtime_state.states["ACTIVE"][0].id == "index-item"
