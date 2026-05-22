"""Notion datasource inspection and validation for dRecall onboarding.

Provides utilities to discover, inspect, validate, and select Notion datasources
for safe user-guided integration during dRecall onboarding.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from config import get_settings
from notion.notion_client import NotionClientWrapper

logger = logging.getLogger(__name__)

# Notion property type compatibility with RecallItem
PROPERTY_COMPATIBILITY = {
    "title": ["title", "rich_text", "text"],
    "content": ["rich_text", "text"],
    "tags": ["multi_select", "select"],
    "source": ["rich_text", "text", "select"],
    "template_type": ["select", "rich_text"],
    "created_at": ["date", "created_time"],
    "updated_at": ["date", "last_edited_time"],
    "processed": ["checkbox"],
    "enhanced": ["checkbox"],
    "metadata": ["rich_text", "text"],
}

REQUIRED_FIELDS = {"title", "content"}
OPTIONAL_FIELDS = {"tags", "source", "template_type", "created_at", "updated_at", "processed", "enhanced"}


class DatasourceInspector:
    """Inspector for discovering and validating Notion datasources."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().notion_api_key
        self.client = NotionClientWrapper(api_key=self.api_key)
        if not self.api_key:
            raise ValueError("NOTION_API_KEY is required for datasource inspection")

    def list_accessible_datasources(self) -> List[Dict[str, Any]]:
        """List all accessible datasources and databases.

        Returns:
            List of datasource metadata dicts with id, title, type, and stats.
        """
        datasources = []
        try:
            # Attempt to list data sources (newer API)
            result = self.client.search()
            for item in result.get("results", []):
                if item.get("object") == "database":
                    metadata = {
                        "id": item.get("id"),
                        "title": self._extract_title(item),
                        "type": "database",
                        "created_time": item.get("created_time"),
                        "last_edited_time": item.get("last_edited_time"),
                        "parent": item.get("parent", {}),
                        "properties_count": len(item.get("properties", {})),
                        "raw": item,
                    }
                    datasources.append(metadata)
        except Exception as exc:
            logger.warning(f"Failed to list datasources: {exc}")

        return datasources

    def retrieve_datasource(self, datasource_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full metadata for a specific datasource.

        Args:
            datasource_id: The Notion datasource/database ID.

        Returns:
            Full datasource metadata or None if not found.
        """
        try:
            db = self.client.retrieve_page(page_id=datasource_id)
            return {
                "id": db.get("id"),
                "title": self._extract_title(db),
                "properties": db.get("properties", {}),
                "created_time": db.get("created_time"),
                "last_edited_time": db.get("last_edited_time"),
                "parent": db.get("parent", {}),
                "raw": db,
            }
        except Exception as exc:
            logger.error(f"Failed to retrieve datasource {datasource_id}: {exc}")
            return None

    def inspect_properties(self, datasource_id: str) -> Dict[str, Dict[str, Any]]:
        """Get property names and types for a datasource.

        Args:
            datasource_id: The Notion datasource/database ID.

        Returns:
            Dict mapping property names to their type and details.
        """
        ds = self.retrieve_datasource(datasource_id)
        if not ds:
            return {}

        props = {}
        for prop_name, prop_config in ds.get("properties", {}).items():
            props[prop_name] = {
                "type": prop_config.get("type"),
                "id": prop_config.get("id"),
            }
            if prop_config.get("type") == "select":
                props[prop_name]["options"] = [o.get("name") for o in prop_config.get("select", {}).get("options", [])]
            elif prop_config.get("type") == "multi_select":
                props[prop_name]["options"] = [o.get("name") for o in prop_config.get("multi_select", {}).get("options", [])]

        return props

    def validate_schema(self, datasource_id: str) -> Dict[str, Any]:
        """Validate datasource schema compatibility with RecallItem.

        Args:
            datasource_id: The Notion datasource/database ID.

        Returns:
            Validation result with compatibility status and details.
        """
        props = self.inspect_properties(datasource_id)
        if not props:
            return {"compatible": False, "reason": "Could not retrieve properties"}

        result = {
            "compatible": False,
            "partially_compatible": False,
            "required_fields": {},
            "optional_fields": {},
            "missing_required": [],
            "missing_optional": [],
            "unmapped_notion_fields": [],
        }

        # Check required fields
        for field in REQUIRED_FIELDS:
            compatible_types = PROPERTY_COMPATIBILITY.get(field, [])
            found = False
            for prop_name, prop_info in props.items():
                if prop_info.get("type") in compatible_types:
                    result["required_fields"][field] = {"notion_property": prop_name, "type": prop_info.get("type")}
                    found = True
                    break
            if not found:
                result["missing_required"].append(field)

        # Check optional fields
        for field in OPTIONAL_FIELDS:
            compatible_types = PROPERTY_COMPATIBILITY.get(field, [])
            mapped_required_names = {v["notion_property"] for v in result["required_fields"].values()}
            for prop_name, prop_info in props.items():
                if prop_info.get("type") in compatible_types and prop_name not in mapped_required_names:
                    result["optional_fields"][field] = {"notion_property": prop_name, "type": prop_info.get("type")}
                    break

        # Identify unmapped Notion fields
        mapped_required = {v["notion_property"] for v in result["required_fields"].values()}
        mapped_optional = {v["notion_property"] for v in result["optional_fields"].values()}
        mapped_notion_props = mapped_required | mapped_optional
        result["unmapped_notion_fields"] = [p for p in props.keys() if p not in mapped_notion_props]

        # Determine compatibility
        if not result["missing_required"]:
            result["compatible"] = True
        elif len(result["missing_required"]) <= 1:
            result["partially_compatible"] = True

        return result

    def suggest_mapping(self, datasource_id: str) -> Dict[str, str]:
        """Suggest RecallItem → Notion property mapping.

        Args:
            datasource_id: The Notion datasource/database ID.

        Returns:
            Dict mapping RecallItem fields to Notion property names.
        """
        props = self.inspect_properties(datasource_id)
        mapping = {}

        # Try to auto-map fields based on name similarity and type
        prop_names_lower = {name.lower(): name for name in props.keys()}

        suggestions = {
            "title": ["title", "name", "heading"],
            "content": ["content", "notes", "description", "text"],
            "tags": ["tags", "labels", "categories"],
            "source": ["source", "origin", "from"],
            "template_type": ["template", "type", "kind"],
            "created_at": ["created", "created_at", "date_created"],
            "updated_at": ["updated", "updated_at", "date_modified"],
            "processed": ["processed", "is_processed"],
            "enhanced": ["enhanced", "is_enhanced"],
        }

        for recall_field, notion_suggestions in suggestions.items():
            for suggestion in notion_suggestions:
                if suggestion in prop_names_lower:
                    prop_name = prop_names_lower[suggestion]
                    prop_type = props[prop_name].get("type")
                    compatible_types = PROPERTY_COMPATIBILITY.get(recall_field, [])
                    if prop_type in compatible_types:
                        mapping[recall_field] = prop_name
                        break

        return mapping

    def create_datasource(
        self,
        title: str,
        parent_page_id: str,
        schema: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Create a new Notion database for dRecall.

        Args:
            title: Name of the new datasource.
            parent_page_id: Parent page ID where to create the database.
            schema: Optional custom property schema.

        Returns:
            The created database ID or None if creation failed.
        """
        if not schema:
            schema = self._default_schema()

        try:
            properties = {}
            for field_name, notion_type in schema.items():
                properties[field_name] = self._build_property(field_name, notion_type)

            result = self.client.create_database(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": title}}],
                properties=properties,
            )

            db_id = result.get("id")
            logger.info(f"Created new Notion datasource: {title} ({db_id})")
            return db_id
        except Exception as exc:
            logger.error(f"Failed to create datasource: {exc}")
            return None

    @staticmethod
    def _extract_title(item: Dict[str, Any]) -> str:
        """Extract title from Notion object."""
        title_content = item.get("title", [])
        if isinstance(title_content, list) and title_content:
            return title_content[0].get("text", {}).get("content", "Untitled")
        return "Untitled"

    @staticmethod
    def _default_schema() -> Dict[str, str]:
        """Return the default dRecall schema for new datasources."""
        return {
            "Title": "title",
            "Content": "rich_text",
            "Tags": "multi_select",
            "Source": "rich_text",
            "Template": "select",
            "Created": "created_time",
            "Updated": "last_edited_time",
            "Processed": "checkbox",
            "Enhanced": "checkbox",
        }

    @staticmethod
    def _build_property(name: str, notion_type: str) -> Dict[str, Any]:
        """Build a Notion property config."""
        if notion_type == "title":
            return {"title": {}}
        elif notion_type == "rich_text":
            return {"rich_text": {}}
        elif notion_type == "select":
            return {"select": {"options": []}}
        elif notion_type == "multi_select":
            return {"multi_select": {"options": []}}
        elif notion_type == "checkbox":
            return {"checkbox": {}}
        elif notion_type == "created_time":
            return {"created_time": {}}
        elif notion_type == "last_edited_time":
            return {"last_edited_time": {}}
        else:
            return {"rich_text": {}}
