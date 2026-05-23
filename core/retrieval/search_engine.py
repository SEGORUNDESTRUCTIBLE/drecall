"""Search utilities for keyword and tag retrieval."""

from __future__ import annotations

from typing import Iterable, List, Optional

from core.schemas import RecallItem


class SearchEngine:
    """Search engine for keyword, tag, subject, and state retrieval."""

    @staticmethod
    def _normalize_text(value: Optional[str]) -> str:
        if not value:
            return ""
        return value.strip().lower()

    def search(
        self,
        items: Iterable[RecallItem],
        keyword: Optional[str] = None,
        tags: Optional[List[str]] = None,
        subject: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[RecallItem]:
        keyword = self._normalize_text(keyword)
        subject = self._normalize_text(subject)
        tags = [self._normalize_text(tag) for tag in tags or [] if tag and tag.strip()]
        state = state.strip().upper() if state else None

        results: List[RecallItem] = []
        for item in items:
            if state and item.revision_metadata.get("state", "NEW").upper() != state:
                continue
            if subject and subject not in self._normalize_text(item.subject):
                continue
            if tags and not set(tags).issubset({self._normalize_text(tag) for tag in item.tags}):
                continue
            if keyword:
                haystack = " ".join(
                    [
                        self._normalize_text(item.title),
                        self._normalize_text(item.content),
                        self._normalize_text(item.subject),
                        self._normalize_text(item.system),
                        " ".join(self._normalize_text(tag) for tag in item.tags),
                    ]
                )
                if keyword not in haystack:
                    continue
            results.append(item)

        if keyword:
            results = sorted(results, key=lambda item: self._score_item(item, keyword), reverse=True)
        return results

    def _score_item(self, item: RecallItem, keyword: str) -> int:
        score = 0
        normalized_keyword = self._normalize_text(keyword)
        title = self._normalize_text(item.title)
        content = self._normalize_text(item.content)
        subject = self._normalize_text(item.subject)
        system = self._normalize_text(item.system)
        tags = [self._normalize_text(tag) for tag in item.tags]

        if normalized_keyword in title:
            score += 4
        if normalized_keyword in content:
            score += 3
        if normalized_keyword in subject:
            score += 2
        if normalized_keyword in system:
            score += 1
        if any(normalized_keyword == tag for tag in tags):
            score += 2
        if title.startswith(normalized_keyword) or title.endswith(normalized_keyword):
            score += 1
        return score

    def search_by_tag(self, items: Iterable[RecallItem], tag: str) -> List[RecallItem]:
        normalized = self._normalize_text(tag)
        return [item for item in items if normalized in {self._normalize_text(t) for t in item.tags}]

    def search_by_subject(self, items: Iterable[RecallItem], subject: str) -> List[RecallItem]:
        normalized = self._normalize_text(subject)
        return [item for item in items if normalized in self._normalize_text(item.subject)]
