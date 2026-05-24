import importlib
import uuid

cs = importlib.import_module("config.settings")
from notion.datasource_registry import resolve_datasource_alias


def test_resolve_explicit_mapping():
    alias = "my_alias"
    dbid = str(uuid.uuid4())
    mapping = {alias: {"database_id": dbid}}
    resolved = resolve_datasource_alias(alias, datasource_map=mapping)
    assert resolved.get("database_id") == dbid


def test_resolve_raw_uuid():
    dbid = str(uuid.uuid4())
    resolved = resolve_datasource_alias(dbid, datasource_map={})
    assert resolved.get("database_id") == dbid


def test_resolve_env_default_alias():
    dbid = str(uuid.uuid4())
    original = cs.settings.notion_database_id
    try:
        cs.settings.notion_database_id = dbid
        resolved = resolve_datasource_alias("notion_default", datasource_map={})
        assert resolved.get("database_id") == dbid
    finally:
        cs.settings.notion_database_id = original
