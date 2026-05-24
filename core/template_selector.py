"""Template selection for adaptive revision structuring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TemplateDefinition:
    name: str
    prompt: str
    required_fields: List[str]
    revision_sections: List[str]
    metadata_extraction_rules: Dict[str, Any]
    image_requirements: bool
    scheduling_defaults: Dict[str, Any]
    supported_input_types: List[str]
    output_format: str
    tags: List[str]
    revision_support: bool


@dataclass(frozen=True)
class TemplateChoice:
    template_name: str
    schema_key: str
    priority: int
    rationale: Optional[str]
    definition: TemplateDefinition


class TemplateSelector:
    """Selects the appropriate template for a detected domain and content type."""

    _TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "medical"

    def __init__(self) -> None:
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, TemplateDefinition]:
        definitions: Dict[str, TemplateDefinition] = {}
        if not self._TEMPLATES_DIR.exists():
            return definitions

        for file_path in sorted(self._TEMPLATES_DIR.glob("*.yaml")):
            try:
                raw = file_path.read_text(encoding="utf-8")
                data = self._parse_simple_yaml(raw)
                definition = TemplateDefinition(
                    name=str(data.get("name", file_path.stem)),
                    prompt=str(data.get("prompt", "")),
                    required_fields=list(data.get("required_fields", [])),
                    revision_sections=list(data.get("revision_sections", [])),
                    metadata_extraction_rules=dict(data.get("metadata_extraction_rules", {})),
                    image_requirements=bool(data.get("image_requirements", False)),
                    scheduling_defaults=dict(data.get("scheduling_defaults", {})),
                    supported_input_types=list(data.get("supported_input_types", [])),
                    output_format=str(data.get("output_format", "canonical_revision")),
                    tags=list(data.get("tags", [])),
                    revision_support=bool(data.get("revision_support", True)),
                )
                definitions[definition.name] = definition
            except Exception:
                continue
        return definitions

    def _cast_scalar(self, value: str) -> Any:
        lower = value.strip().lower()
        if lower in ("true", "yes", "on"):
            return True
        if lower in ("false", "no", "off"):
            return False
        if lower == "null" or lower == "none":
            return None
        try:
            if "." in lower:
                return float(lower)
            return int(lower)
        except ValueError:
            pass
        if value.startswith("\"") and value.endswith("\""):
            return value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        return value

    def _parse_simple_yaml(self, raw_text: str) -> Dict[str, Any]:
        lines = [line.rstrip() for line in raw_text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        result: Dict[str, Any] = {}
        parents: List[tuple[Any, int]] = [(result, -1)]

        i = 0
        while i < len(lines):
            line = lines[i]
            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()
            while parents and indent <= parents[-1][1]:
                parents.pop()
            parent, _ = parents[-1]

            if ":" not in stripped:
                i += 1
                continue

            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if raw_value == "":
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                next_strip = next_line.strip()
                if next_strip.startswith("-"):
                    node: Any = []
                else:
                    node = {}
                if isinstance(parent, dict):
                    parent[key] = node
                    parents.append((node, indent))
                elif isinstance(parent, list):
                    parent.append({key: node})
                    parents.append((node, indent))
                i += 1
                continue

            value = self._cast_scalar(raw_value)
            if isinstance(parent, dict):
                parent[key] = value
            elif isinstance(parent, list):
                parent.append({key: value})
            i += 1

        # Second pass to convert simple lists if necessary
        def normalize(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: normalize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [normalize(v) for v in obj]
            return obj

        return normalize(result)

    def select(self, domain: str, content_type: str, intent: str, metadata: Optional[Dict[str, str]] = None) -> TemplateChoice:
        if not domain or not content_type:
            raise ValueError("Domain and content type are required")

        content_type = content_type.lower()
        direct_match = self.templates.get(content_type)
        if direct_match:
            return TemplateChoice(
                template_name=direct_match.name,
                schema_key=direct_match.name,
                priority=1,
                rationale=f"Direct match for content_type {content_type}",
                definition=direct_match,
            )

        for template in self.templates.values():
            if content_type in template.supported_input_types:
                return TemplateChoice(
                    template_name=template.name,
                    schema_key=template.name,
                    priority=2,
                    rationale=f"Selected {template.name} based on supported_input_types",
                    definition=template,
                )

        fallback = self.templates.get("concept") or next(iter(self.templates.values()), None)
        if fallback is None:
            raise ValueError("No medical templates are available for selection")

        return TemplateChoice(
            template_name=fallback.name,
            schema_key=fallback.name,
            priority=10,
            rationale="Fallback template selection",
            definition=fallback,
        )

    def get_template(self, template_name: str) -> Optional[TemplateDefinition]:
        return self.templates.get(template_name)
