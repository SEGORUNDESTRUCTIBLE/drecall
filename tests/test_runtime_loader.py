#!/usr/bin/env python3
"""Runtime loader tests for dRecall.

Validates startup bootstrapping from snapshots, corrupted snapshot handling,
Notion sync recovery, and runtime state indexing.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.runtime.runtime_loader import RuntimeLoader
from core.schemas import RecallItem


def make_snapshot_item(title: str, due_offset_days: int = -1) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": title.lower().replace(" ", "_"),
        "title": title,
        "content": "Persistent content.",
        "tags": ["runtime", "test"],
        "subject": "General",
        "revision_metadata": {
            "state": "ACTIVE",
            "next_review_at": (now + timedelta(days=due_offset_days)).isoformat(),
            "recall_strength": 0.8,
            "review_events": [{"outcome": "correct", "reviewed_at": now.isoformat()}],
        },
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


class FlakyNotionFetcher:
    def __init__(self, page_data: dict):
        self.page_data = page_data
        self.attempts = 0

    def fetch_pages(self, limit: int = 50, start_cursor: str = None):
        self.attempts += 1
        if self.attempts == 1:
            raise RuntimeError("transient network failure")
        return {"results": [self.page_data], "has_more": False}


def test_load_runtime_from_snapshot(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "runtime_snapshot.json"
    raw = {"items": [make_snapshot_item("Snapshot Item", due_offset_days=-2)]}
    snapshot_path.write_text(json.dumps(raw), encoding="utf-8")

    loader = RuntimeLoader(snapshot_path=snapshot_path, notion_fetcher=None)
    runtime_state = loader.load_runtime(load_from_notion=False)

    assert len(runtime_state.items) == 1
    assert runtime_state.summary()["due_items"] == 1
    assert runtime_state.summary()["weak_items"] == 0
    assert runtime_state.sync_metadata["loaded_from_snapshot"] is True
    assert runtime_state.sync_metadata["loaded_from_notion"] is False


def test_corrupted_snapshot_recovery(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "runtime_snapshot.json"
    snapshot_path.write_text("{ invalid json", encoding="utf-8")

    loader = RuntimeLoader(snapshot_path=snapshot_path, notion_fetcher=None)
    runtime_state = loader.load_runtime(load_from_notion=False)

    assert runtime_state.items == []
    assert runtime_state.sync_metadata["loaded_from_snapshot"] is False
    assert snapshot_path.with_suffix(snapshot_path.suffix + ".corrupt").exists()


def test_notion_sync_recovers_after_transient_error(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    page_data = {
        "id": "notion_page_1",
        "properties": {
            "Title": {"type": "title", "title": [{"plain_text": "Notion Loaded"}]},
            "Content": {"type": "rich_text", "rich_text": [{"plain_text": "Loaded from Notion."}]},
            "Tags": {"type": "multi_select", "multi_select": [{"name": "sync"}]},
            "Revision Metadata": {
                "type": "rich_text",
                "rich_text": [{"plain_text": json.dumps({"state": "WEAK", "next_review_at": (now - timedelta(days=1)).isoformat(), "review_events": [{"outcome": "partial", "reviewed_at": now.isoformat()}]})}]
            },
        },
        "created_time": now.isoformat(),
        "last_edited_time": now.isoformat(),
    }

    fetcher = FlakyNotionFetcher(page_data)
    loader = RuntimeLoader(snapshot_path=tmp_path / "runtime_snapshot.json", notion_fetcher=fetcher)
    runtime_state = loader.load_runtime(load_from_notion=True)

    assert len(runtime_state.items) == 1
    assert runtime_state.items[0].title == "Notion Loaded"
    assert runtime_state.summary()["loaded_from_notion"] is True
    assert fetcher.attempts >= 2
