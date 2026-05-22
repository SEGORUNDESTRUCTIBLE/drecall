"""Google Gemini AI provider implementation.

Provides integration with Google's Gemini API, supporting both
text and multimodal inputs with advanced reasoning capabilities.
"""

import logging
import os
import time
import json
import re
from typing import Any, Dict, Optional

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)

# Gemini model constants
GEMINI_MODELS = {
    "pro": "gemini-pro",
    "pro-vision": "gemini-pro-vision",
    "default": "gemini-pro",
}


class GeminiProvider(BaseProvider):
    """Google Gemini AI provider implementation.
    
    Handles communication with Google's Gemini API.
    Key features:
    - Advanced reasoning capabilities
    - Multimodal support (text, images, video)
    - Configurable safety settings
    
    Maintains same interface as other providers to ensure
    seamless provider swapping without affecting business logic.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "gemini-pro",
        timeout: int = 30,
        retries: int = 3,
        retry_backoff: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Initialize Gemini provider.
        
        Args:
            api_key: Google API key from Google AI Studio.
            model: Model name (default: gemini-pro).
                   Can use keys like 'pro', 'pro-vision' or full model names.
            timeout: Request timeout in seconds (default: 30).
            **kwargs: Additional configuration (e.g., temperature, top_p).
        """
        # Resolve model alias to full name
        model = GEMINI_MODELS.get(model.lower()) if model.lower() in GEMINI_MODELS else model
        
        # allow API key to be pulled from environment if not provided
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        super().__init__(api_key=api_key, model=model, timeout=timeout, **kwargs)
        self.retries = retries
        self.retry_backoff = retry_backoff
        self._client = None
        logger.debug(f"Initialized GeminiProvider with model: {self.model}")
    
    @property
    def client(self):
        """Lazily initialize and return Gemini client module.
        
        Defers import and configuration until first use.
        
        Returns:
            google.generativeai module instance.
            
        Raises:
            ImportError: If google-generativeai package is not installed.
            ValueError: If API key is missing or invalid.
        """
        if self._client is None:
            try:
                import google.generativeai as genai
                logger.debug("Configuring Gemini client")
                if not self.api_key:
                    raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY env var or pass api_key.")
                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError as e:
                logger.error("google-generativeai package not installed")
                raise ImportError(
                    "google-generativeai package is required for GeminiProvider. "
                    "Install with: pip install google-generativeai"
                ) from e
            except Exception as e:
                logger.error(f"Failed to configure Gemini client: {e}")
                raise ValueError(f"Failed to configure Gemini client: {e}") from e
        return self._client
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion using Gemini API.
        
        Args:
            prompt: User input prompt.
            system_prompt: Optional system instructions (used as prefix).
            temperature: Sampling temperature (0.0-1.0+).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional Gemini-specific parameters (e.g., top_p).
            
        Returns:
            Generated text from the model.
            
        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If Gemini API call fails.
            TimeoutError: If request exceeds timeout.
        """
        try:
            # Validate inputs
            if not prompt or not isinstance(prompt, str):
                raise ValueError("Prompt must be a non-empty string")
            
            # Build full prompt (Gemini doesn't have formal system prompts)
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            logger.debug(f"Calling Gemini API with model {self.model}")
            
            # Get model instance
            genai = self.client
            model = genai.GenerativeModel(self.model)
            
            # Extract internal flags
            expect_json = kwargs.pop("expect_json", True)

            # Build generation config
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens
            generation_config.update(kwargs)
            
            # Make API call
            def _call():
                return model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    request_options={"timeout": self.timeout},
                )

            response = self._call_with_retries(_call)
            
            # Extract response text
            # Extract response text and enforce JSON when required
            result = getattr(response, "text", None)
            if result is None:
                # try dict like response
                try:
                    result = response["candidates"][0]["content"][0]["text"]
                except Exception:
                    result = str(response)

            if expect_json:
                return self._ensure_json(result)

            return result
            
        except TimeoutError as e:
            logger.error(f"Gemini API timeout after {self.timeout}s")
            raise TimeoutError(f"Gemini request exceeded {self.timeout}s timeout") from e
        except Exception as e:
            logger.error(f"Gemini API error: {type(e).__name__}: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e
    
    def validate_credentials(self) -> bool:
        """Validate Gemini API credentials with a test call.
        
        Performs a minimal test to verify the API key is valid and
        the service is reachable.
        
        Returns:
            True if credentials are valid, False otherwise.
        """
        try:
            logger.debug("Validating Gemini credentials")
            
            genai = self.client
            model = genai.GenerativeModel(self.model)
            
            # Make a minimal test call
            def _call():
                return model.generate_content(
                    "Hi",
                    generation_config={"max_output_tokens": 5},
                    request_options={"timeout": self.timeout},
                )

            response = self._call_with_retries(_call)
            
            logger.info("Gemini credentials validated successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Gemini credential validation failed: {e}")
            return False

    def _call_with_retries(self, fn):
        last_exc = None
        for attempt in range(1, max(1, self.retries) + 1):
            try:
                return fn()
            except Exception as e:
                last_exc = e
                wait = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(f"Gemini call failed (attempt {attempt}/{self.retries}): {e}; retrying in {wait}s")
                time.sleep(wait)
        logger.error("All Gemini retries failed")
        raise last_exc

    def _ensure_json(self, text: str):
        if text is None:
            raise ValueError("Empty response from provider")
        if isinstance(text, (dict, list)):
            return text
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if match:
                candidate = match.group(1)
                try:
                    return json.loads(candidate)
                except Exception as e:
                    logger.debug(f"Sanitization JSON parse failed: {e}")
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
        """Get information about the current Gemini model.
        
        Returns metadata about the model configuration.
        
        Returns:
            Dictionary with model metadata.
        """
        return {
            "provider": "gemini",
            "model": self.model,
            "capabilities": {
                "chat_completions": True,
                "streaming": False,  # Not yet implemented in this version
                "system_prompts": False,  # Gemini uses prompt prefix instead
                "multimodal": "vision" in self.model,
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
        # Model-specific context windows (approximate)
        context_windows = {
            "gemini-pro": 32768,
            "gemini-pro-vision": 32768,
        }
        return context_windows.get(self.model, 32768)
