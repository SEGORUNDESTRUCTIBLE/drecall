"""Runtime memory state indexing and lightweight operational summaries."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from core.schemas import RecallItem
from core.retrieval.filter_engine import FilterEngine


@dataclass
class RuntimeState:
    items: List[RecallItem] = field(default_factory=list)
    items_by_id: Dict[str, RecallItem] = field(default_factory=dict)
    tags: Dict[str, List[RecallItem]] = field(default_factory=dict)
    subjects: Dict[str, List[RecallItem]] = field(default_factory=dict)
    states: Dict[str, List[RecallItem]] = field(default_factory=dict)
    due_items: List[RecallItem] = field(default_factory=list)
    weak_items: List[RecallItem] = field(default_factory=list)
    updated_at_sorted: List[RecallItem] = field(default_factory=list)
    sync_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_items(
        cls,
        items: Iterable[RecallItem],
        sync_metadata: Optional[Dict[str, Any]] = None,
    ) -> "RuntimeState":
        state = cls(items=list(items), sync_metadata=sync_metadata or {})
        state.reload_indexes(sync_metadata=sync_metadata)
        return state

    def reload_indexes(self, sync_metadata: Optional[Dict[str, Any]] = None) -> None:
        self.items_by_id = {}
        self.tags = defaultdict(list)
        self.subjects = defaultdict(list)
        self.states = defaultdict(list)
        self.updated_at_sorted = sorted(self.items, key=lambda item: item.updated_at, reverse=True)

        for index, item in enumerate(self.items):
            item_key = item.id or f"local-{index}"
            self.items_by_id[item_key] = item
            for tag in item.tags or []:
                self.tags[tag.strip().lower()].append(item)
            subject = (item.subject or "").strip().lower()
            if subject:
                self.subjects[subject].append(item)
            state = (item.revision_metadata or {}).get("state", "NEW")
            self.states[state.upper()].append(item)

        filter_engine = FilterEngine()
        self.due_items = filter_engine.due_items(self.items)
        self.weak_items = filter_engine.weak_items(self.items)

        if sync_metadata is not None:
            self.sync_metadata.update(sync_metadata)

    def add_or_replace_item(self, item: RecallItem) -> None:
        if item.id and item.id in self.items_by_id:
            self.items = [item if existing.id == item.id else existing for existing in self.items]
        else:
            self.items.append(item)
        self.reload_indexes(sync_metadata=self.sync_metadata)

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "items": [item.model_dump(mode="json") for item in self.items],
            "sync_metadata": self.sync_metadata,
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "total_items": len(self.items),
            "due_items": len(self.due_items),
            "weak_items": len(self.weak_items),
            "tag_count": len(self.tags),
            "subject_count": len(self.subjects),
            "state_counts": {state: len(values) for state, values in self.states.items()},
            "loaded_from_snapshot": self.sync_metadata.get("loaded_from_snapshot", False),
            "loaded_from_notion": self.sync_metadata.get("loaded_from_notion", False),
            "last_sync_at": self.sync_metadata.get("last_sync_at"),
            "sync_status": self.sync_metadata.get("sync_status", "unknown"),
        }
