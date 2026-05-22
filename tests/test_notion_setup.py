from setup.notion_setup import connect_notion, save_selected_datasource, list_datasources
from notion.datasource_inspector import DatasourceInspector


def test_connect_notion_success(monkeypatch):
    monkeypatch.setattr(DatasourceInspector, 'list_accessible_datasources', lambda self: [{'id': 'db1'}])
    assert connect_notion('token') is True


def test_connect_notion_failure(monkeypatch):
    def raise_exc(self):
        raise RuntimeError('bad')

    monkeypatch.setattr(DatasourceInspector, 'list_accessible_datasources', raise_exc)
    assert connect_notion('token') is False


def test_save_selected_datasource(tmp_path, monkeypatch):
    # Run inside a temp directory so we don't touch repo .env
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / '.env'
    env_file.write_text('ENABLE_NOTION=false\n')

    assert save_selected_datasource('ds_123', enable=True) is True

    content = env_file.read_text()
    assert 'NOTION_DATASOURCE_ID=ds_123' in content
    assert 'ENABLE_NOTION=true' in content
