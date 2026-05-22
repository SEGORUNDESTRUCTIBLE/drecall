import pytest

from config import reset_settings
from notion.notion_ingest import NotionIngest
from core.schemas import RecallItem


def test_ingest_detects_datasource_env(monkeypatch):
    monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
    monkeypatch.setenv("NOTION_DATASOURCE_ID", "ds_abc")
    reset_settings()
    ingestor = NotionIngest(client=None)
    assert ingestor.datasource_mode is True
    assert ingestor.target_id == "ds_abc"
    reset_settings()


def test_ingest_warns_on_legacy_db(monkeypatch, caplog):
    monkeypatch.delenv("NOTION_DATASOURCE_ID", raising=False)
    monkeypatch.setenv("NOTION_DATABASE_ID", "db_123")
    reset_settings()
    caplog.clear()
    ingestor = NotionIngest(client=None)
    assert ingestor.datasource_mode is False
    assert ingestor.target_id == "db_123"
    assert any("Legacy NOTION_DATABASE_ID detected" in r.message for r in caplog.records)
    reset_settings()
