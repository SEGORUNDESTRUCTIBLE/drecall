"""Workspace inspector for intelligent Notion database selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .notion_schema_mapper import NotionSchemaMapper, SchemaMappingReport

logger = logging.getLogger("drecall.workspace_inspector")


@dataclass(frozen=True)
class WorkspaceInspectionResult:
    candidate_id: str
    title: str
    match_score: float
    mapping_report: SchemaMappingReport
    domain_tags: List[str]
    is_suitable: bool
    rationale: Optional[str] = None


class WorkspaceInspector:
    """Inspects existing Notion databases and selects the best persistence target."""

    def __init__(self, client: Any, schema_mapper: Optional[NotionSchemaMapper] = None) -> None:
        self.client = client
        self.schema_mapper = schema_mapper or NotionSchemaMapper()

    def discover_databases(self) -> List[str]:
        """Discover accessible Notion databases when explicit candidates are not provided."""
        candidate_ids: List[str] = []
        if self.client is None:
            return candidate_ids

        try:
            search_payload = self.client.search(filter={"property": "object", "value": "database"})
            for item in search_payload.get("results", []):
                if item.get("object") == "database" and item.get("id"):
                    candidate_ids.append(item["id"])
        except Exception as exc:
            logger.debug("WorkspaceInspector cannot discover databases: %s", exc)

        return candidate_ids

    def inspect_databases(self, candidate_ids: Optional[List[str]], canonical_fields: List[str]) -> List[WorkspaceInspectionResult]:
        """Inspect candidate databases and rank them by schema fit."""
        results: List[WorkspaceInspectionResult] = []
        ids = candidate_ids or self.discover_databases()
        if not ids:
            return results

        for candidate_id in ids:
            properties = self._fetch_properties(candidate_id)
            report = self.schema_mapper.inspect(properties, canonical_fields)
            title = self._fetch_title(candidate_id)
            result = WorkspaceInspectionResult(
                candidate_id=candidate_id,
                title=title,
                match_score=report.score,
                mapping_report=report,
                domain_tags=[],
                is_suitable=report.score >= 0.65,
                rationale="schema fit score",
            )
            results.append(result)
        return sorted(results, key=lambda item: item.match_score, reverse=True)

    def choose_best_database(self, candidate_ids: Optional[List[str]], canonical_fields: List[str]) -> Optional[WorkspaceInspectionResult]:
        """Return the best matching database or None if no candidate is suitable."""
        results = self.inspect_databases(candidate_ids, canonical_fields)
        return results[0] if results else None

    def _fetch_properties(self, database_id: str) -> Dict[str, Any]:
        try:
            db = self.client.databases.retrieve(database_id=database_id)
            return db.get("properties", {}) or {}
        except Exception as exc:
            logger.debug("Failed to fetch properties for database %s: %s", database_id, exc)
            return {}

    def _fetch_title(self, database_id: str) -> str:
        try:
            db = self.client.databases.retrieve(database_id=database_id)
            title = db.get("title", [])
            if title:
                return " ".join([part.get("plain_text", "") for part in title])
        except Exception:
            pass
        return database_id
