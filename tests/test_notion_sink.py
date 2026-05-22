import pytest
from unittest.mock import Mock

from notion.notion_sink import (
    NotionSink,
    DefaultPropertyMapper,
    DefaultBlockBuilder,
    SimpleSchemaValidator,
    SchemaMismatchError,
    DuplicatePersistenceError,
)

from core.contracts.persistence_contracts import PersistencePermanentError


def make_mock_client():
    client = Mock()
    client.pages = Mock()
    client.search = Mock()
    return client


def test_create_page_success():
    client = make_mock_client()
    client.pages.create.return_value = {"id": "page_1", "url": "https://notion/page_1"}

    sink = NotionSink(client=client, datasource_map={"ds1": {}}, backoff_factor=0)

    item = {"title": "Test", "content": "Body", "datasource_id": "ds1", "dedup_key": "dk1"}

    res = sink.create(item)

    assert res.id == "page_1"
    assert "url" in res.metadata
    client.pages.create.assert_called_once()


def test_retrieve_page():
    client = make_mock_client()
    client.pages.retrieve.return_value = {"id": "page_1", "properties": {}}

    sink = NotionSink(client=client, datasource_map={"ds1": {}}, backoff_factor=0)

    out = sink.retrieve_page("page_1")

    assert out["id"] == "page_1"
    client.pages.retrieve.assert_called_once_with(page_id="page_1")


def test_schema_validation_fails():
    client = make_mock_client()

    schema = {"ds1": {"required": ["title", "content"]}}
    validator = SimpleSchemaValidator(schemas=schema)

    sink = NotionSink(client=client, datasource_map={"ds1": {}}, schema_validator=validator, backoff_factor=0)

    item = {"title": "Only title", "datasource_id": "ds1", "dedup_key": "dk2"}

    with pytest.raises(SchemaMismatchError):
        sink.create(item)


def test_invalid_datasource_handling():
    client = make_mock_client()
    sink = NotionSink(client=client, datasource_map={}, backoff_factor=0)

    item = {"title": "No ds", "content": "x"}

    with pytest.raises(PersistencePermanentError):
        sink.create(item)


def test_retry_behavior_on_transient_error():
    client = make_mock_client()

    # first call raises ConnectionError, second returns success
    client.pages.create.side_effect = [ConnectionError("conn"), {"id": "p2", "url": "u"}]

    sink = NotionSink(client=client, datasource_map={"ds1": {}}, backoff_factor=0)

    item = {"title": "T", "content": "C", "datasource_id": "ds1", "dedup_key": "dk3"}

    res = sink.create(item)

    assert res.id == "p2"
    assert client.pages.create.call_count == 2


def test_idempotency_duplicate_detected():
    client = make_mock_client()
    client.search.return_value = {"results": ["exists"]}

    sink = NotionSink(client=client, datasource_map={"ds1": {}}, backoff_factor=0)

    item = {"title": "T", "content": "C", "datasource_id": "ds1", "dedup_key": "dk4"}

    with pytest.raises(DuplicatePersistenceError):
        sink.create(item)
