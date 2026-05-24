import importlib
import logging
import uuid

cs = importlib.import_module("config.settings")
from notion.notion_manager import NotionEnvStatus, NotionManager
from main import log_notion_startup_health


def test_describe_configuration_reports_env_default_alias():
    dbid = str(uuid.uuid4())
    original = cs.settings.notion_database_id
    try:
        cs.settings.notion_database_id = dbid
        summary = NotionManager.describe_configuration(datasource_map={})
    finally:
        cs.settings.notion_database_id = original

    assert "Notion startup configuration:" in summary
    assert "notion_default (env):" in summary
    assert dbid in summary


def test_log_notion_startup_health_logs_resolved_alias(caplog):
    caplog.set_level(logging.INFO)
    dbid = str(uuid.uuid4())
    env_status = NotionEnvStatus(enabled=True, token_present=True, database_id=dbid, datasource_id=None)
    datasource_map = {"notion_default": {"database_id": dbid}}

    log_notion_startup_health(env_status, "notion_default", dbid, datasource_map)

    assert "=== Notion startup health ===" in caplog.text
    assert f"database_id={dbid}" in caplog.text
    assert "persistence_enabled=True" in caplog.text


def test_log_notion_startup_health_warns_when_unresolved(caplog):
    caplog.set_level(logging.INFO)
    env_status = NotionEnvStatus(enabled=True, token_present=True, database_id=None, datasource_id=None)

    log_notion_startup_health(env_status, "notion_default", None, {})

    assert "=== Notion startup health ===" in caplog.text
    assert "notion_default (env): UNRESOLVED" in caplog.text
    assert "Persistence will be disabled until a valid datasource mapping is configured." in caplog.text
