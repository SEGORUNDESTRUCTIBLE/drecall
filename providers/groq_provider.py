"""Groq AI provider implementation.

Provides integration with Groq's API for high-speed LLM inference.
Groq specializes in fast inference with excellent latency characteristics.
"""

import logging
from typing import Any, Dict, Optional

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)

# Groq model constants
GROQ_MODELS = {
    "mixtral": "mixtral-8x7b-32768",
    "llama2": "llama2-70b-4096",
    "default": "mixtral-8x7b-32768",
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
        api_key: str,
        model: str = "mixtral-8x7b-32768",
        timeout: int = 30,
        **kwargs: Any,
    ) -> None:
        """Initialize Groq provider.
        
        Args:
            api_key: Groq API key from https://console.groq.com/
            model: Model name (default: mixtral-8x7b-32768).
                   Can use keys like 'mixtral', 'llama2' or full model names.
            timeout: Request timeout in seconds (default: 30).
            **kwargs: Additional configuration (e.g., temperature, max_tokens defaults).
        """
        # Resolve model alias to full name
        model = GROQ_MODELS.get(model.lower()) if model.lower() in GROQ_MODELS else model
        
        super().__init__(api_key=api_key, model=model, timeout=timeout, **kwargs)
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
    ) -> str:
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
            
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            request_params.update(kwargs)
            
            # Make API call with timeout handling
            response = self.client.chat.completions.create(
                **request_params,
                timeout=self.timeout,
            )
            
            # Extract response text
            result = response.choices[0].message.content
            logger.debug(f"Groq API returned {len(result)} characters")
            
            return result
            
        except TimeoutError as e:
            logger.error(f"Groq API timeout after {self.timeout}s")
            raise TimeoutError(f"Groq request exceeded {self.timeout}s timeout") from e
        except Exception as e:
            logger.error(f"Groq API error: {type(e).__name__}: {e}")
            raise RuntimeError(f"Groq API error: {e}") from e
    
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                timeout=self.timeout,
            )
            
            logger.info("Groq credentials validated successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Groq credential validation failed: {e}")
            return False
    
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
