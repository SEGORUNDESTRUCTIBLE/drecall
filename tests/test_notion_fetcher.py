import pytest
from types import SimpleNamespace

from config import reset_settings
from notion.notion_fetcher import NotionFetcher


def test_fetcher_detects_datasource_env(monkeypatch):
    monkeypatch.setattr(
        "notion.notion_fetcher.get_settings",
        lambda: SimpleNamespace(notion_datasource_id="ds_abc", notion_database_id=None),
    )
    monkeypatch.setenv("NOTION_API_KEY", "fake-token")
    reset_settings()
    fetcher = NotionFetcher(client=None)
    assert fetcher.datasource_mode is True
    assert fetcher.target_id == "ds_abc"
    reset_settings()


def test_fetcher_warns_on_legacy_db(monkeypatch, caplog):
    monkeypatch.setattr(
        "notion.notion_fetcher.get_settings",
        lambda: SimpleNamespace(notion_datasource_id=None, notion_database_id="db_123"),
    )
    monkeypatch.setenv("NOTION_API_KEY", "fake-token")
    reset_settings()
    caplog.clear()
    fetcher = NotionFetcher(client=None)
    assert fetcher.datasource_mode is False
    assert fetcher.target_id == "db_123"
    assert any("Legacy NOTION_DATABASE_ID detected" in r.message for r in caplog.records)
    reset_settings()


def test_fetcher_ignores_whitespace_ids(monkeypatch):
    monkeypatch.setattr(
        "notion.notion_fetcher.get_settings",
        lambda: SimpleNamespace(notion_datasource_id="   ", notion_database_id="  db_123  "),
    )
    monkeypatch.setenv("NOTION_API_KEY", "fake-token")
    reset_settings()
    fetcher = NotionFetcher(client=None)
    assert fetcher.datasource_mode is False
    assert fetcher.target_id == "db_123"
    reset_settings()
