# dRecall development environment

This repository is standardized for Python 3.12 and a stable AI tooling stack.
Use `.venv/` for local development, enable VS Code support, and install dependencies from `requirements.txt`.

## Recommended Python version

- Python 3.12.x
- Do not use Python 3.14 for local development or workspace environment creation.

## Create and activate the virtual environment

Windows PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:
```cmd
py -3.12 -m venv .venv
.\.venv\Scripts\activate.bat
```

macOS / Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment variables

Copy the example env file and fill in secrets:

```bash
copy .env.example .env
```

### Safe Notion sandbox testing

Use a dedicated sandbox workspace or a separate Notion account for live Notion validation.
Do not use your primary study or production workspace.

- Create a new Notion workspace or dedicated sandbox workspace.
- Create a dedicated datasource called `dRecall_Testing`.
- Create a new Notion integration for dRecall.
- Share the sandbox datasource with the integration.
- Use only the sandbox workspace's `NOTION_API_KEY` and `NOTION_DATASOURCE_ID`.

Required live provider variables:

- `GROQ_API_KEY` — Groq API key
- `GEMINI_API_KEY` — Google Gemini API key
- `NOTION_API_KEY` — Notion integration token (sandbox only)
- `NOTION_DATASOURCE_ID` — Sandbox datasource id

Optional support variables:

- `NOTION_DATABASE_ID`
- `ENABLE_GROQ`
- `ENABLE_GEMINI`
- `ENABLE_NOTION`
- `NOTION_LIVE_TEST_CLEANUP` — set to `true` to archive live test pages after validation

## VS Code support

This workspace is configured to automatically use `.env` and activate the local `.venv` interpreter.
Ensure the Python extension is installed, then open the workspace and select the `.venv` interpreter.

## Running tests

```bash
python -m pytest -q
```

## Notes

- `.venv/` is ignored by Git and should be recreated with Python 3.12.
- Do not commit `.env`; keep secrets out of source control.
