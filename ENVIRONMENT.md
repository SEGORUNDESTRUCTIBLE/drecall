# Environment setup for live providers

This project supports live integration with Groq and Google Gemini providers.
To run the live provider tests and enable real API calls, set the following
environment variables and install the provider SDKs.

Required environment variables:

- `GROQ_API_KEY` — your Groq API key (optional if you don't use Groq)
- `GEMINI_API_KEY` — your Google Gemini API key (optional if you don't use Gemini)

Recommended Python packages:

```bash
pip install groq google-generativeai pytest
```

Notes:
- Live tests in `tests/test_live_provider.py` will be skipped if neither
  `GROQ_API_KEY` nor `GEMINI_API_KEY` are present in the environment.
- Keep API keys secret; do not commit them to source control. Use a `.env`
  file or your CI secret storage for test runs.
