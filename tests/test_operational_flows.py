#!/usr/bin/env python3
"""Operational behavior tests for dRecall retrieval and persistence integration."""

from __future__ import annotations

from core.retrieval import RetrievalEngine
from core.schemas import RecallItem


class DummySink:
    def __init__(self) -> None:
        self.queries = []

    def query_similar(self, text: str, limit: int = 10):
        self.queries.append((text, limit))
        return [{"id": "page_1", "score": 0.93}]


def make_item(title: str, subject: str) -> RecallItem:
    return RecallItem(
        id=title.lower().replace(" ", "_"),
        title=title,
        content="Example content.",
        tags=["example"],
        subject=subject,
        revision_metadata={"state": "ACTIVE", "next_review_at": "2099-01-01T00:00:00+00:00", "recall_strength": 0.95},
    )


def test_persistence_search_delegates_to_sink() -> None:
    sink = DummySink()
    engine = RetrievalEngine(persistence_sink=sink)
    results = engine.persistence_search("example query", limit=2)

    assert len(results) == 1
    assert results[0]["id"] == "page_1"
    assert sink.queries == [("example query", 2)]


def test_export_snapshot_without_revision_metadata(tmp_path) -> None:
    engine = RetrievalEngine()
    item = make_item("Operational Export", "Ops")
    path = tmp_path / "export.json"

    exported_path = engine.export_items([item], str(path), include_revision=False)
    assert exported_path == str(path)
    assert path.exists()
    payload = path.read_text(encoding="utf-8")
    assert "revision_metadata" not in payload
    assert "Operational Export" in payload


def test_filter_by_subject_and_tag() -> None:
    engine = RetrievalEngine()
    items = [
        make_item("Cardio Item", "Cardiology"),
        make_item("Neuro Item", "Neurology"),
    ]

    subject_results = engine.filter_by_subject(items, "cardio")
    assert len(subject_results) == 1
    assert subject_results[0].title == "Cardio Item"

    tag_results = engine.filter_by_tag(items, "example")
    assert len(tag_results) == 2
