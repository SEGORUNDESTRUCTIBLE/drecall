"""Guided Notion onboarding helpers for dRecall.

This module provides high-level functions used by the CLI onboarding
flow to connect, list, validate, choose and persist a Notion datasource.
It builds on `notion.datasource_inspector.DatasourceInspector` to perform
safe operations and recommends sandbox usage.
"""

from typing import Any, Dict, Optional, List, Tuple

import logging

from config import get_settings, reset_settings
from notion.datasource_inspector import DatasourceInspector

logger = logging.getLogger(__name__)


def connect_notion(api_token: str) -> bool:
    try:
        inspector = DatasourceInspector(api_key=api_token)
        _ = inspector.list_accessible_datasources()
        logger.info("Notion token validated")
        return True
    except Exception as exc:
        logger.error(f"Notion connection failed: {exc}")
        return False


def validate_token(api_token: str) -> bool:
    return connect_notion(api_token)


def list_datasources(api_token: str) -> List[Dict[str, Any]]:
    inspector = DatasourceInspector(api_key=api_token)
    return inspector.list_accessible_datasources()


def choose_datasource_interactive(api_token: str) -> Optional[str]:
    datasources = list_datasources(api_token)
    if not datasources:
        return None
    for i, ds in enumerate(datasources, 1):
        print(f"{i}. {ds.get('title')} (id={ds.get('id')}) — properties={ds.get('properties_count')}")
    choice = input(f"Select datasource (1-{len(datasources)}) or 'q': ")
    if choice.strip().lower() == 'q':
        return None
    try:
        idx = int(choice) - 1
        return datasources[idx]['id']
    except Exception:
        return None


def create_new_datasource(api_token: str, title: str, parent_page_id: str) -> Optional[str]:
    inspector = DatasourceInspector(api_key=api_token)
    return inspector.create_datasource(title=title, parent_page_id=parent_page_id)


def save_selected_datasource(datasource_id: str, enable: bool = True) -> bool:
    env_file = ".env"
    try:
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        updated = False
        new_lines = []
        for line in lines:
            if line.startswith('NOTION_DATASOURCE_ID='):
                new_lines.append(f"NOTION_DATASOURCE_ID={datasource_id}\n")
                updated = True
            elif line.startswith('ENABLE_NOTION='):
                new_lines.append(f"ENABLE_NOTION={'true' if enable else 'false'}\n")
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"NOTION_DATASOURCE_ID={datasource_id}\n")
        if not any(l.startswith('ENABLE_NOTION=') for l in new_lines):
            new_lines.append(f"ENABLE_NOTION={'true' if enable else 'false'}\n")

        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        reset_settings()
        logger.info('Saved datasource to .env')
        return True
    except Exception as exc:
        logger.error(f"Failed to save datasource: {exc}")
        return False


def onboarding_flow() -> Optional[str]:
    settings = get_settings()
    print('Start dRecall Notion Onboarding')
    token = settings.notion_api_key
    if not token:
        token = input('Paste your Notion integration token (sandbox only): ').strip()
    if not validate_token(token):
        print('Token validation failed')
        return None

    datasources = list_datasources(token)
    if not datasources:
        print('No accessible datasources found. You may need to share a datasource with the integration.')
        create = input('Create a new sandbox datasource? (y/n): ').strip().lower()
        if create != 'y':
            return None
        parent = input('Parent page id to create datasource under: ').strip()
        title = input('Datasource title (default: dRecall_Testing): ').strip() or 'dRecall_Testing'
        dsid = create_new_datasource(token, title, parent)
        if dsid:
            save_selected_datasource(dsid, enable=True)
            return dsid
        return None

    # Pick first datasource for simplicity in non-interactive mode
    print(f"Found {len(datasources)} datasources")
    for i, ds in enumerate(datasources, 1):
        print(f"{i}. {ds.get('title')} — id={ds.get('id')}")

    chosen = choose_datasource_interactive(token)
    if not chosen:
        return None
    valid, msg, details = DatasourceInspector(api_key=token).validate_schema(chosen), '', {}
    # Save chosen
    save_selected_datasource(chosen, enable=True)
    return chosen
