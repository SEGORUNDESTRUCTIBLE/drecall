"""Retrieval engine coordinating search, filters, export, and health metrics."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.schemas import RecallItem
from .filter_engine import FilterEngine
from .search_engine import SearchEngine


logger = logging.getLogger("drecall.retrieval")


class RetrievalEngine:
    """Engine supporting retrieval workflows and operational memory metrics."""

    def __init__(self, persistence_sink: Optional[Any] = None) -> None:
        self.search = SearchEngine()
        self.filter = FilterEngine()
        self.persistence_sink = persistence_sink
        self.logger = logger

    def search_items(
        self,
        items: Iterable[RecallItem],
        keyword: Optional[str] = None,
        tags: Optional[List[str]] = None,
        subject: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[RecallItem]:
        self.logger.info("Searching items keyword=%s tags=%s subject=%s state=%s", keyword, tags, subject, state)
        return self.search.search(items, keyword=keyword, tags=tags, subject=subject, state=state)

    def review_due(self, items: Iterable[RecallItem], as_of: Optional[datetime] = None) -> List[RecallItem]:
        self.logger.info("Retrieving due items as_of=%s", as_of)
        return self.filter.due_items(items, as_of=as_of)

    def review_weak(self, items: Iterable[RecallItem], threshold: float = 0.5) -> List[RecallItem]:
        self.logger.info("Retrieving weak memory items threshold=%s", threshold)
        return self.filter.weak_items(items, threshold=threshold)

    def recent_items(self, items: Iterable[RecallItem], limit: int = 20) -> List[RecallItem]:
        self.logger.info("Retrieving recent items limit=%d", limit)
        return self.filter.recent_items(items, limit=limit)

    def failed_items(self, items: Iterable[RecallItem]) -> List[RecallItem]:
        self.logger.info("Retrieving failed items")
        return self.filter.failed_items(items)

    def duplicates(self, items: Iterable[RecallItem]) -> List[List[RecallItem]]:
        self.logger.info("Retrieving duplicate groups")
        return self.filter.duplicate_groups(items)

    def filter_by_subject(self, items: Iterable[RecallItem], subject: str) -> List[RecallItem]:
        self.logger.info("Filtering by subject=%s", subject)
        return self.filter.filter_by_subject(items, subject)

    def filter_by_tag(self, items: Iterable[RecallItem], tag: str) -> List[RecallItem]:
        self.logger.info("Filtering by tag=%s", tag)
        return self.filter.filter_by_tag(items, tag)

    def export_items(self, items: Iterable[RecallItem], path: str, include_revision: bool = True) -> str:
        path_obj = Path(path)
        payload = []
        for item in items:
            item_dict = item.model_dump(mode="json")
            if not include_revision:
                item_dict.pop("revision_metadata", None)
            payload.append(item_dict)

        path_obj.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.logger.info("Exported %d items to %s", len(payload), path_obj)
        return str(path_obj)

    def snapshot_items(self, items: Iterable[RecallItem], path: str) -> str:
        self.logger.info("Creating snapshot backup to %s", path)
        return self.export_items(items, path, include_revision=True)

    def archive_items(self, items: Iterable[RecallItem], path: str, only_failed: bool = False) -> str:
        path_obj = Path(path)
        archive_payload = []
        for item in items:
            if only_failed:
                events = item.revision_metadata.get("review_events", []) if item.revision_metadata else []
                if not any(event.get("outcome") == "forgotten" for event in events):
                    continue
            archive_payload.append(item.model_dump(mode="json"))

        path_obj.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")
        self.logger.info("Archived %d items to %s", len(archive_payload), path_obj)
        return str(path_obj)

    def load_snapshot(self, path: str) -> List[RecallItem]:
        path_obj = Path(path)
        content = path_obj.read_text(encoding="utf-8")
        raw = json.loads(content)
        items = [RecallItem.model_validate(entry) for entry in raw if isinstance(entry, dict)]
        self.logger.info("Loaded %d items from snapshot %s", len(items), path_obj)
        return items

    def memory_health(self, items: Iterable[RecallItem], threshold: float = 0.5) -> Dict[str, Any]:
        item_list = list(items)
        total = len(item_list)
        duplicates = self.duplicates(item_list)
        weak_count = len(self.review_weak(item_list, threshold=threshold))
        due_count = len(self.review_due(item_list))
        overdue_count = len([item for item in item_list if item.revision_metadata and item.revision_metadata.get("next_review_at") and datetime.fromisoformat(item.revision_metadata["next_review_at"]).replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)])
        failed_count = len(self.failed_items(item_list))
        quality_count = len([item for item in item_list if len(item.content or "") >= 20 and item.tags])

        duplicate_items = len([item for group in duplicates for item in group])
        state_counts: Dict[str, int] = {}
        for item in item_list:
            state = (item.revision_metadata or {}).get("state", "NEW")
            normalized_state = state.upper() if isinstance(state, str) else "UNKNOWN"
            state_counts[normalized_state] = state_counts.get(normalized_state, 0) + 1

        metrics = {
            "total_memory_items": total,
            "duplicate_groups": len(duplicates),
            "duplicate_items": duplicate_items,
            "duplicate_ratio": duplicate_items / total if total else 0.0,
            "weak_memory_density": weak_count / total if total else 0.0,
            "due_items": due_count,
            "due_ratio": due_count / total if total else 0.0,
            "review_load": due_count / total if total else 0.0,
            "overdue_count": overdue_count,
            "overdue_ratio": overdue_count / total if total else 0.0,
            "failed_items": failed_count,
            "ingestion_quality_ratio": quality_count / total if total else 0.0,
            "state_counts": state_counts,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self.logger.info("Memory health metrics computed: %s", metrics)
        return metrics

    def persistence_search(self, text: str, limit: int = 10) -> List[Any]:
        if not self.persistence_sink or not getattr(self.persistence_sink, "query_similar", None):
            self.logger.warning("Persistence sink does not support search")
            return []
        self.logger.info("Querying persistence sink for text=%s limit=%d", text, limit)
        return self.persistence_sink.query_similar(text=text, limit=limit)
