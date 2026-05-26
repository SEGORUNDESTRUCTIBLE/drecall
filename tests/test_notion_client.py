import os
from types import SimpleNamespace

import pytest

from config import reset_settings
from notion.notion_client import NotionClientWrapper


def test_notion_client_init_no_key(monkeypatch):
    monkeypatch.setattr(
        "notion.notion_client.get_settings",
        lambda: SimpleNamespace(notion_api_key=None),
    )
    reset_settings()
    with pytest.raises(ValueError):
        NotionClientWrapper().client
    reset_settings()


def test_notion_client_init_empty_token(monkeypatch):
    monkeypatch.setattr(
        "notion.notion_client.get_settings",
        lambda: SimpleNamespace(notion_api_key=""),
    )
    reset_settings()
    with pytest.raises(ValueError):
        NotionClientWrapper()
    reset_settings()


def test_notion_client_init_whitespace_token(monkeypatch):
    monkeypatch.setattr(
        "notion.notion_client.get_settings",
        lambda: SimpleNamespace(notion_api_key="   "),
    )
    reset_settings()
    with pytest.raises(ValueError):
        NotionClientWrapper()
    reset_settings()


def test_detect_notion_mode():
    from notion.notion_client import detect_notion_mode

    assert detect_notion_mode({"object": "data_source"}) is True
    assert detect_notion_mode({"object": "database"}) is False
    assert detect_notion_mode({"type": "data_source"}) is False
    assert detect_notion_mode(None) is False
    assert detect_notion_mode({}) is False


def test_notion_client_init_with_key_skip():
    if not os.environ.get("NOTION_API_KEY"):
        pytest.skip("NOTION_API_KEY not set")
    # If key exists, ensure client property returns without raising
    wrapper = NotionClientWrapper()
    c = wrapper.client
    assert c is not None


def test_datasource_env_preference(monkeypatch):
    # Ensure wrapper does not error when datasource env var present (no network call)
    monkeypatch.setenv("NOTION_DATASOURCE_ID", "ds_123")
    reset_settings()
    # Notion client shouldn't be created when not accessing `.client`
    w = NotionClientWrapper()
    assert hasattr(w, 'request')
    reset_settings()
