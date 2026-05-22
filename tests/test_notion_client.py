import os
import pytest

from config import reset_settings
from notion.notion_client import NotionClientWrapper


def test_notion_client_init_no_key():
    # Temporarily ensure env var is not set
    old = os.environ.pop("NOTION_API_KEY", None)
    reset_settings()
    with pytest.raises(ValueError):
        NotionClientWrapper().client
    if old:
        os.environ["NOTION_API_KEY"] = old
    reset_settings()


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
