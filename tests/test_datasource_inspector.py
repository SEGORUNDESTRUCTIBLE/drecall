import pytest

from notion.datasource_inspector import DatasourceInspector
from notion.notion_client import NotionClientWrapper


def test_list_accessible_datasources(monkeypatch):
    fake_search = {
        'results': [
            {
                'object': 'database',
                'id': 'db1',
                'title': [{'text': {'content': 'Test DB'}}],
                'created_time': 't',
                'last_edited_time': 't',
                'parent': {},
                'properties': {'Name': {'id': 'p1', 'type': 'title'}}
            }
        ]
    }

    monkeypatch.setattr(NotionClientWrapper, 'search', lambda self, **kwargs: fake_search)
    inspector = DatasourceInspector(api_key='fake')
    results = inspector.list_accessible_datasources()
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]['title'] == 'Test DB'


def test_inspect_properties_and_suggest_mapping_and_validate(monkeypatch):
    fake_db = {
        'id': 'db1',
        'title': [{'text': {'content': 'My DB'}}],
        'properties': {
            'Name': {'id': 'n', 'type': 'title'},
            'Notes': {'id': 'c', 'type': 'rich_text'},
            'Tags': {'id': 't', 'type': 'multi_select', 'multi_select': {'options': [{'name': 'a'}]}},
        },
        'created_time': 't',
        'last_edited_time': 't',
        'parent': {}
    }

    monkeypatch.setattr(NotionClientWrapper, 'retrieve_page', lambda self, page_id: fake_db)
    inspector = DatasourceInspector(api_key='fake')

    props = inspector.inspect_properties('db1')
    assert 'Name' in props and props['Name']['type'] == 'title'

    mapping = inspector.suggest_mapping('db1')
    assert isinstance(mapping, dict)
    assert mapping.get('title') in ('Name', 'name', None)

    validation = inspector.validate_schema('db1')
    assert isinstance(validation, dict)
    assert 'compatible' in validation


def test_invalid_token_raises():
    with pytest.raises(ValueError):
        DatasourceInspector(api_key=None)


def test_create_datasource_calls_client(monkeypatch):
    def fake_create_database(self, **kwargs):
        return {'id': 'new-db-id'}

    monkeypatch.setattr(NotionClientWrapper, 'create_database', fake_create_database)
    inspector = DatasourceInspector(api_key='fake')
    dbid = inspector.create_datasource('Test DS', parent_page_id='parent1')
    assert dbid == 'new-db-id'
