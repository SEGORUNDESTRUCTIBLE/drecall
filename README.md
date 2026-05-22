# dRecall

Continuous Integration (CI) for dRecall is provided by GitHub Actions.

To add the test badge to this README, replace `<OWNER>` and `<REPO>` with your GitHub repository values:

```
[![CI Tests](https://github.com/<OWNER>/<REPO>/actions/workflows/tests.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/tests.yml)
```

CI details:
- Runs on: `ubuntu-latest`
- Python: `3.12`
- Steps: checkout, setup python, create venv, install requirements, run `pytest -q`
- Live integration tests (Notion/Groq/Gemini) remain skipped unless secrets are provided.

Run tests locally:

```bash
python -m venv .venv
.venv/bin/python -m pip install -U pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```
