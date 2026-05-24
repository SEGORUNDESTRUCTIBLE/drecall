"""Automatic Notion database creation for adaptive revision workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .notion_schema_mapper import NotionSchemaMapper


class DatabaseAutocreator:
    """Creates and configures Notion databases when no suitable target exists."""

    def __init__(self, client: Any, schema_mapper: Optional[NotionSchemaMapper] = None) -> None:
        self.client = client
        self.schema_mapper = schema_mapper or NotionSchemaMapper()

    def build_schema(self, template_name: str, canonical_fields: List[str]) -> Dict[str, Any]:
        """Return the Notion property schema for a given template and canonical field set."""
        schema: Dict[str, Any] = {}
        for field in canonical_fields:
            if field == "title":
                schema[field] = {"title": {}}
            elif field in ("tags", "pyq_tags"):
                schema[field] = {"multi_select": {}}
            elif field in ("next_review_at", "created_at", "updated_at"):
                schema[field] = {"date": {}}
            elif field in ("review_state", "exam", "topic", "subtopic"):
                schema[field] = {"select": {}}
            elif field == "strength_score":
                schema[field] = {"number": {}}
            else:
                schema[field] = {"rich_text": {}}
        return schema

    def create_database(self, parent_page_id: str, title: str, template_name: str, canonical_fields: List[str]) -> Dict[str, Any]:
        """Create a new Notion database for adaptive revision content."""
        properties = self.build_schema(template_name, canonical_fields)
        if not self.client:
            raise RuntimeError("Notion client is required for database creation")

        body = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        return self.client.databases.create(**body)

    def create_or_update_properties(self, database_id: str, schema_updates: Dict[str, str]) -> bool:
        """Create missing properties in an existing database."""
        if not self.client:
            raise RuntimeError("Notion client is required for schema updates")
        for field_name, field_type in schema_updates.items():
            property_payload = {field_name: {field_type: {}}}
            try:
                self.client.databases.update(database_id=database_id, properties=property_payload)
            except Exception:
                return False
        return True

    def ensure_database_for_payload(self, candidate_ids: List[str], canonical_fields: List[str], parent_page_id: str, template_name: str) -> Dict[str, Any]:
        """Select or create a database suitable for a given payload."""
        # Placeholder for actual selection logic; should inspect existing DBs first.
        return self.create_database(parent_page_id=parent_page_id, title=f"Revision {template_name.title()}", template_name=template_name, canonical_fields=canonical_fields)
