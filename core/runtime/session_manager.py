"""Session persistence and runtime snapshot management."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.runtime.state_manager import RuntimeState

logger = logging.getLogger("drecall.session")


class SessionManager:
    """Manages runtime snapshot persistence for long-lived dRecall sessions."""

    def __init__(
        self,
        runtime_state: RuntimeState,
        snapshot_path: Optional[Path] = None,
    ) -> None:
        self.runtime_state = runtime_state
        self.snapshot_path = Path(snapshot_path or Path("runtime_snapshot.json"))
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, payload: Dict[str, Any]) -> None:
        temp_path = self.snapshot_path.with_suffix(self.snapshot_path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_path.replace(self.snapshot_path)

    def persist_snapshot(self) -> Path:
        payload = self.runtime_state.to_snapshot()
        payload["sync_metadata"] = payload.get("sync_metadata", {})
        payload["sync_metadata"]["last_saved_at"] = datetime.now(timezone.utc).isoformat()
        self.runtime_state.sync_metadata = payload["sync_metadata"]

        self._atomic_write(payload)
        return self.snapshot_path

    def record_item(self, item: Any) -> None:
        self.runtime_state.add_or_replace_item(item)
        try:
            self.persist_snapshot()
        except Exception as exc:
            logger.warning("Failed to persist runtime snapshot after record_item: %s", exc)

    def record_items(self, items: Any) -> None:
        self.runtime_state.items = list(items)
        self.runtime_state.reload_indexes(sync_metadata=self.runtime_state.sync_metadata)
        try:
            self.persist_snapshot()
        except Exception as exc:
            logger.warning("Failed to persist runtime snapshot after record_items: %s", exc)

    def mark_sync(self, source: str, status: str, detail: Optional[str] = None) -> None:
        metadata = self.runtime_state.sync_metadata
        metadata["last_sync_at"] = datetime.now(timezone.utc).isoformat()
        metadata["sync_source"] = source
        metadata["sync_status"] = status
        if detail is not None:
            metadata["sync_detail"] = detail
        self.runtime_state.sync_metadata = metadata
        self.persist_snapshot()
