import os
import pytest

from providers.groq_provider import GroqProvider
from providers.gemini_provider import GeminiProvider


def skip_if_no_keys():
    if not (os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        pytest.skip("No live provider API keys configured in environment")


def test_groq_validate_and_json_generation():
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set")

    prov = GroqProvider()
    assert prov.validate_credentials() is True

    # Request JSON-only output
    out = prov.generate('Respond only with a JSON object: {"status": "ok"}', expect_json=True)
    assert isinstance(out, (dict, list))


def test_gemini_validate_and_json_generation():
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")

    prov = GeminiProvider()
    assert prov.validate_credentials() is True

    out = prov.generate('Respond only with a JSON object: {"status": "ok"}', expect_json=True)
    assert isinstance(out, (dict, list))


def test_timeout_behavior():
    # Use a very small timeout to force timeout behavior if provider reachable
    if os.environ.get("GROQ_API_KEY"):
        prov = GroqProvider(timeout=0.001, retries=1)
        with pytest.raises(Exception):
            prov.generate("Hello")

    if os.environ.get("GEMINI_API_KEY"):
        prov = GeminiProvider(timeout=0.001, retries=1)
        with pytest.raises(Exception):
            prov.generate("Hello")


def test_invalid_api_key_handling():
    # Passing an obviously invalid key should not crash test runner
    prov = GroqProvider(api_key="invalid-key-xyz", retries=1)
    assert prov.validate_credentials() is False

    provg = GeminiProvider(api_key="invalid-key-xyz", retries=1)
    assert provg.validate_credentials() is False


def test_malformed_response_handling():
    # If provider returns non-JSON, generate with expect_json should raise ValueError
    # We cannot force providers to return malformed content, so we only run this test
    # when a provider is available and simulate by calling with a prompt that
    # likely returns text. If the provider returns JSON, test will be skipped.
    if os.environ.get("GROQ_API_KEY"):
        prov = GroqProvider()
        try:
            out = prov.generate("Say something brief.", expect_json=True)
            # if we got JSON, skip this check
            if isinstance(out, (dict, list)):
                pytest.skip("Provider returned valid JSON; cannot test malformed handling")
        except ValueError:
            pass
