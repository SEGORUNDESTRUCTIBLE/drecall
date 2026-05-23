#!/usr/bin/env python3
"""Provider validation script for drecall.

Validates settings loading, provider abstraction, provider initialization,
environment variable reading, and error handling without making real API calls.
"""

import builtins
import os
import sys
from pathlib import Path
from unittest import mock

# Ensure repo root is on sys.path when running this test file directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_settings, reset_settings
from providers.base_provider import BaseProvider
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_settings_loading() -> None:
    print_header("TEST 1: Settings Loading and Environment Variables")

    env_vars = {
        "GROQ_API_KEY": "env-groq-key",
        "GEMINI_API_KEY": "env-gemini-key",
        "GROQ_MODEL": "mixtral-8x7b-32768",
        "GEMINI_MODEL": "gemini-pro",
        "DEFAULT_PROVIDER": "gemini",
        "ENABLE_GROQ": "true",
        "ENABLE_GEMINI": "true",
    }

    with mock.patch.dict(os.environ, env_vars, clear=False):
        reset_settings()
        settings = get_settings()

        print(f"groq_api_key={settings.groq_api_key}")
        print(f"gemini_api_key={settings.gemini_api_key}")
        print(f"groq_model={settings.groq_model}")
        print(f"gemini_model={settings.gemini_model}")
        print(f"default_provider={settings.default_provider}")

        assert settings.groq_api_key == "env-groq-key", "GROQ_API_KEY did not load"
        assert settings.gemini_api_key == "env-gemini-key", "GEMINI_API_KEY did not load"
        assert settings.groq_model == "mixtral-8x7b-32768", "GROQ_MODEL did not load"
        assert settings.gemini_model == "gemini-pro", "GEMINI_MODEL did not load"
        assert settings.default_provider == "gemini", "DEFAULT_PROVIDER did not load"
        assert settings.is_provider_enabled("groq"), "Groq provider should be enabled"
        assert settings.is_provider_enabled("gemini"), "Gemini provider should be enabled"
        assert settings.get_active_providers() == ["groq", "gemini"], "Active providers list incorrect"

        print("✓ Settings loaded and environment variables read correctly")

    reset_settings()


def test_base_provider_abstraction() -> None:
    print_header("TEST 2: BaseProvider Abstraction")

    groq = GroqProvider(api_key="test-key", model="mixtral", timeout=20)
    gemini = GeminiProvider(api_key="test-key", model="pro", timeout=22)

    print(f"GroqProvider repr: {repr(groq)}")
    print(f"GeminiProvider repr: {repr(gemini)}")

    assert isinstance(groq, BaseProvider), "GroqProvider does not inherit BaseProvider"
    assert isinstance(gemini, BaseProvider), "GeminiProvider does not inherit BaseProvider"
    assert groq.model == "mixtral-8x7b-32768", "Groq alias resolution failed"
    assert gemini.model == "gemini-pro", "Gemini alias resolution failed"
    assert groq.timeout == 20, "Groq timeout not preserved"
    assert gemini.timeout == 22, "Gemini timeout not preserved"

    print("✓ BaseProvider abstraction and subclass initialization validated")


def test_groq_provider_initialization() -> None:
    print_header("TEST 3: GroqProvider Initialization")

    groq = GroqProvider(api_key="init-test-key", model="mixtral")

    print(f"GroqProvider model: {groq.model}")
    print(f"GroqProvider timeout: {groq.timeout}")
    print(f"GroqProvider config: {groq.config}")

    assert groq.api_key == "init-test-key", "GroqProvider api_key not set"
    assert groq.model == "mixtral-8x7b-32768", "GroqProvider model alias resolution failed"
    assert groq.timeout == 30, "GroqProvider default timeout failed"

    info = groq.get_model_info()
    assert info["provider"] == "groq", "GroqProvider get_model_info returned wrong provider"

    print("✓ GroqProvider initialization passed")


def test_gemini_provider_initialization() -> None:
    print_header("TEST 4: GeminiProvider Initialization")

    gemini = GeminiProvider(api_key="init-test-key", model="pro")

    print(f"GeminiProvider model: {gemini.model}")
    print(f"GeminiProvider timeout: {gemini.timeout}")
    print(f"GeminiProvider config: {gemini.config}")

    assert gemini.api_key == "init-test-key", "GeminiProvider api_key not set"
    assert gemini.model == "gemini-pro", "GeminiProvider model alias resolution failed"
    assert gemini.timeout == 30, "GeminiProvider default timeout failed"

    info = gemini.get_model_info()
    assert info["provider"] == "gemini", "GeminiProvider get_model_info returned wrong provider"

    print("✓ GeminiProvider initialization passed")


def test_groq_provider_response_extraction() -> None:
    print_header("TEST 5: GroqProvider Response Extraction")

    class FakeMessage:
        def __init__(self, content: str):
            self.content = content

    class FakeChoice:
        def __init__(self, content: str):
            self.message = FakeMessage(content)

    class FakeResponse:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    groq = GroqProvider(api_key="dummy", model="mixtral")
    groq._call_with_retries = lambda fn: FakeResponse('{"status":"ok"}')

    result = groq.generate("Hello", expect_json=False)
    assert isinstance(result, str)
    assert result == '{"status":"ok"}'

    # Dict-like response object should be extracted correctly as well
    class FakeDictResponse(dict):
        pass

    fake_dict_resp = FakeDictResponse({
        "choices": [
            {"message": {"content": '{"status":"ok"}'}},
        ]
    })
    groq._call_with_retries = lambda fn: fake_dict_resp
    result = groq.generate("Hello", expect_json=False)
    assert isinstance(result, str)
    assert result == '{"status":"ok"}'

    print("✓ GroqProvider response extraction passed")


def test_error_handling() -> None:
    print_header("TEST 6: Error Handling Without API Calls")

    groq = GroqProvider(api_key="dummy", model="mixtral")
    gemini = GeminiProvider(api_key="dummy", model="pro")

    for provider in (groq, gemini):
        provider_name = provider.__class__.__name__
        print(f"Checking {provider_name} empty prompt handling")
        try:
            provider.generate("")
            raise AssertionError("Expected RuntimeError for empty prompt")
        except RuntimeError as exc:
            assert isinstance(
                exc.__cause__, ValueError
            ), f"{provider_name} should chain ValueError in __cause__"
            assert "Prompt must be a non-empty string" in str(
                exc.__cause__
            ), f"{provider_name} underlying ValueError message mismatch"
            assert "API error" in str(exc).lower() or provider_name.replace("Provider", "").lower() in str(
                exc
            ).lower(), f"{provider_name} RuntimeError message should include provider context"
            print(f"✓ {provider_name} raised RuntimeError with chained ValueError: {exc}")
        except Exception as exc:
            raise AssertionError(
                f"Unexpected exception type for {provider_name}: {type(exc).__name__}"
            ) from exc

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "groq" or name == "google.generativeai":
            raise ImportError(f"No module named {name}")
        return builtins.__import__(name, globals, locals, fromlist, level)

    with mock.patch("builtins.__import__", side_effect=fake_import):
        for provider in (
            GroqProvider(api_key="dummy", model="mixtral"),
            GeminiProvider(api_key="dummy", model="pro"),
        ):
            provider_name = provider.__class__.__name__
            try:
                provider.generate("hello")
                raise AssertionError(
                    f"Expected RuntimeError when {provider_name} client package is missing"
                )
            except RuntimeError as exc:
                assert isinstance(
                    exc.__cause__, ImportError
                ), f"{provider_name} should chain ImportError in __cause__"
                assert "No module named" in str(
                    exc.__cause__
                ) or "package is required" in str(exc.__cause__), (
                    f"{provider_name} underlying ImportError message mismatch"
                )
                print(
                    f"✓ {provider_name} raised RuntimeError with chained ImportError for missing package: {exc}"
                )
            except Exception as exc:
                raise AssertionError(
                    f"Unexpected exception type for {provider_name} client initialization: {type(exc).__name__}"
                ) from exc

    print("✓ Error handling verified without invoking real APIs")


def main() -> int:
    test_settings_loading()
    test_base_provider_abstraction()
    test_groq_provider_initialization()
    test_gemini_provider_initialization()
    test_error_handling()

    print_header("ALL PROVIDER VALIDATION CHECKS COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
