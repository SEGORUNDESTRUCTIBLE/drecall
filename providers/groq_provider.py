"""Groq AI provider implementation.

Provides integration with Groq's API for high-speed LLM inference.
Groq specializes in fast inference with excellent latency characteristics.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from config import get_settings
from core.contracts.provider_contracts import ProviderResponse, ProviderPermanentError, ProviderTransientError
from .base_provider import BaseProvider

logger = logging.getLogger(__name__)

# Groq model constants
GROQ_MODELS = {
    "mixtral": "mixtral-8x7b-32768",
    "llama2": "llama2-70b-4096",
    # keep alias map but do not hardcode a 'default' here; settings determine default
}


class GroqProvider(BaseProvider):
    """Groq AI provider implementation.
    
    Handles communication with Groq's API for efficient LLM inference.
    Key features:
    - Fast inference times
    - Generous context windows
    - Simple chat completion interface
    
    Not tightly coupled to any specific use case; works with
    any prompt that other providers accept.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: Optional[str] = None,
        timeout: int = 30,
        retries: int = 3,
        retry_backoff: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Initialize Groq provider.
        
        Args:
            api_key: Groq API key from https://console.groq.com/
            model: Model name (default: mixtral).
                   Can use keys like 'mixtral', 'llama2' or full model names.
            timeout: Request timeout in seconds (default: 30).
            **kwargs: Additional configuration (e.g., temperature, max_tokens defaults).
        """
        try:
            active_settings = get_settings()
            api_key = api_key or active_settings.groq_api_key
            # Determine model: explicit argument first, otherwise settings-driven model
            resolved_model = model or active_settings.get_provider("groq")
        except Exception:
            # Graceful fallback if settings unavailable (e.g., in test context)
            api_key = api_key
            resolved_model = model

        # Resolve alias names (e.g., 'mixtral' -> full model id)
        if resolved_model and isinstance(resolved_model, str):
            alias = resolved_model.lower()
            if alias in GROQ_MODELS:
                resolved_model = GROQ_MODELS[alias]

        super().__init__(api_key=api_key, model=resolved_model, timeout=timeout, **kwargs)
        self.retries = retries
        self.retry_backoff = retry_backoff
        self._client = None
        logger.debug(f"Initialized GroqProvider with model: {self.model}")
    
    @property
    def client(self):
        """Lazily initialize and return Groq client.
        
        Defers import and instantiation until first use, reducing startup time
        and allowing graceful degradation if groq package is not installed.
        
        Returns:
            Groq client instance.
            
        Raises:
            ImportError: If groq package is not installed.
            ValueError: If API key is missing or invalid.
        """
        if self._client is None:
            try:
                from groq import Groq
                logger.debug("Initializing Groq client")
                if not self.api_key:
                    raise ValueError("Groq API key is missing. Set GROQ_API_KEY env var or pass api_key.")
                self._client = Groq(api_key=self.api_key)
            except ImportError as e:
                logger.error("groq package not installed")
                raise ImportError(
                    "groq package is required for GroqProvider. "
                    "Install with: pip install groq"
                ) from e
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                raise ValueError(f"Failed to initialize Groq client: {e}") from e
        return self._client
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate text completion using Groq API.
        
        Args:
            prompt: User input prompt.
            system_prompt: Optional system instructions (role/behavior).
            temperature: Sampling temperature (0.0-2.0, typically 0.7).
                        Higher values increase creativity/randomness.
            max_tokens: Maximum tokens to generate (Groq default: model-dependent).
            **kwargs: Additional Groq-specific parameters (e.g., top_p).
            
        Returns:
            Generated text from the model.
            
        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If Groq API call fails.
            TimeoutError: If request exceeds timeout.
        """
        try:
            # Validate inputs
            if not prompt or not isinstance(prompt, str):
                raise ValueError("Prompt must be a non-empty string")
            
            # Build messages list following OpenAI format
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt,
                })
            messages.append({
                "role": "user",
                "content": prompt,
            })
            
            logger.debug(f"Calling Groq API with model {self.model}")
            
            # Extract internal flags (do not forward to API)
            expect_json = kwargs.pop("expect_json", False)

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            request_params.update(kwargs)
            
            # Make API call with timeout handling and timing
            def _call():
                return self.client.chat.completions.create(
                    **request_params,
                    timeout=self.timeout,
                )

            start_ts = time.time()
            response = self._call_with_retries(_call)
            latency_ms = (time.time() - start_ts) * 1000

            # Extract response text
            raw_choices = getattr(response, "choices", None)
            if raw_choices is None and isinstance(response, dict):
                raw_choices = response.get("choices")

            result = None
            if raw_choices:
                try:
                    result = raw_choices[0].message.content
                except Exception:
                    try:
                        result = raw_choices[0].get("message", {}).get("content")
                    except Exception:
                        result = None

            if result is None:
                try:
                    result = response[0]
                except Exception:
                    result = str(response)

            if result is None:
                raise RuntimeError("Empty response from Groq API")

            logger.debug(
                "Groq extraction result type=%s",
                type(result).__name__,
            )

            if expect_json:
                parsed = self._ensure_json(result)
                return ProviderResponse(
                    provider=self.provider_name(),
                    model=self.model,
                    text=json.dumps(parsed) if not isinstance(parsed, str) else parsed,
                    tokens_used=None,
                    latency_ms=latency_ms,
                    error=None,
                    metadata={"format": "json", **request_params},
                )

            if isinstance(result, (dict, list)):
                raw_text = json.dumps(result)
            elif result is None:
                raw_text = ""
            elif not isinstance(result, str):
                raw_text = str(result)
            else:
                raw_text = result

            return ProviderResponse(
                provider=self.provider_name(),
                model=self.model,
                text=raw_text,
                tokens_used=None,
                latency_ms=latency_ms,
                error=None,
                metadata={"format": "text", **request_params},
            )

        except TimeoutError as e:
            logger.error(f"Groq API timeout after {self.timeout}s")
            raise ProviderTransientError(f"Groq request exceeded {self.timeout}s timeout") from e
        except ImportError as e:
            logger.error("Missing Groq client package")
            raise ProviderPermanentError("groq package is required for GroqProvider") from e
        except ValueError as e:
            logger.error(f"Groq input validation error: {e}")
            raise ProviderPermanentError(str(e)) from e
        except Exception as e:
            logger.error(f"Groq API error: {type(e).__name__}: {e}")
            raise ProviderPermanentError(f"Groq API error: {e}") from e
    
    def validate_credentials(self) -> bool:
        """Validate Groq API credentials with a test call.
        
        Performs a minimal test to verify the API key is valid and
        the service is reachable. Does not consume significant quota.
        
        Returns:
            True if credentials are valid, False otherwise.
        """
        try:
            logger.debug("Validating Groq credentials")
            
            # Make a minimal test call
            def _call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                    timeout=self.timeout,
                )

            response = self._retryable_call(_call)
            
            logger.info("Groq credentials validated successfully")
            return True
            
        except ProviderPermanentError as e:
            logger.warning(f"Groq credential validation failed permanently: {e}")
            return False
        except Exception as e:
            logger.warning(f"Groq credential validation failed: {e}")
            return False

    def _call_with_retries(self, fn):
        return self._retryable_call(fn)

    def health_check(self) -> bool:
        return self.validate_credentials()

    def available_models(self) -> List[str]:
        return list(GROQ_MODELS.values()) + list(GROQ_MODELS.keys())

    def token_usage(self) -> Dict[str, Any]:
        return {"tokens_used": None}

    def _ensure_json(self, text: str):
        """Ensure the response is valid JSON, attempt sanitization if needed."""
        if text is None:
            raise ValueError("Empty response from provider")
        if isinstance(text, (dict, list)):
            return text
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            # attempt to extract first JSON object/array from text
            match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if match:
                candidate = match.group(1)
                try:
                    return json.loads(candidate)
                except Exception as e:
                    logger.debug(f"Sanitization JSON parse failed: {e}")
            # final fallback: attempt to coerce simple key:value lines into dict
            lines = [l.strip() for l in text.splitlines() if ":" in l]
            if lines:
                try:
                    out = {}
                    for l in lines:
                        k, v = l.split(":", 1)
                        out[k.strip()] = v.strip()
                    return out
                except Exception:
                    pass
        raise ValueError("Provider returned malformed / non-JSON response")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Groq model.

        Returns metadata about the model configuration.
        Note: Detailed capabilities info requires separate API call
        that may not always be available.

        Returns:
            Dictionary with model metadata.
        """
        return {
            "provider": "groq",
            "model": self.model,
            "capabilities": {
                "chat_completions": True,
                "streaming": False,  # Not yet implemented in this version
                "system_prompts": True,
                "temperature_range": (0.0, 2.0),
            },
            "context_window": self._get_context_window(),
            "timeout_seconds": self.timeout,
        }
    
    def _get_context_window(self) -> int:
        """Get the context window size for the current model.
        
        Returns:
            Context window size in tokens.
        """
        # Model-specific context windows
        context_windows = {
            "mixtral-8x7b-32768": 32768,
            "llama2-70b-4096": 4096,
        }
        return context_windows.get(self.model, 4096)
