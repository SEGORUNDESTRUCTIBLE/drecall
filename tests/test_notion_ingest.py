import pytest
from types import SimpleNamespace

from config import reset_settings
from notion.notion_ingest import NotionIngest
from core.schemas import RecallItem


def test_ingest_detects_datasource_env(monkeypatch):
    monkeypatch.setattr(
        "notion.notion_ingest.get_settings",
        lambda: SimpleNamespace(notion_datasource_id="ds_abc", notion_database_id=None),
    )
    monkeypatch.setenv("NOTION_API_KEY", "fake-token")
    reset_settings()
    ingestor = NotionIngest(client=None)
    assert ingestor.datasource_mode is True
    assert ingestor.target_id == "ds_abc"
    reset_settings()


def test_ingest_warns_on_legacy_db(monkeypatch, caplog):
    monkeypatch.setattr(
        "notion.notion_ingest.get_settings",
        lambda: SimpleNamespace(notion_datasource_id=None, notion_database_id="db_123"),
    )
    monkeypatch.setenv("NOTION_API_KEY", "fake-token")
    reset_settings()
    caplog.clear()
    ingestor = NotionIngest(client=None)
    assert ingestor.datasource_mode is False
    assert ingestor.target_id == "db_123"
    assert any("Legacy NOTION_DATABASE_ID detected" in r.message for r in caplog.records)
    reset_settings()
