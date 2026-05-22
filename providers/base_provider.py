"""Base abstract provider for AI model interactions.

Defines the unified interface that all AI providers must implement.
This ensures provider-agnostic architecture and easy extensibility.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseProvider(ABC):
    """Abstract base class for AI providers.
    
    Establishes a unified interface for interacting with different AI services
    (Groq, Gemini, OpenAI, etc.). Ensures all providers implement consistent
    methods for seamless swapping and composition.
    
    This design prevents provider-specific logic from leaking into core code.
    All business logic should remain independent of which provider is used.
    """
    
    def __init__(self, api_key: str, model: str, timeout: int = 30, **kwargs: Any) -> None:
        """Initialize the provider.
        
        Args:
            api_key: API key or authentication token for the service.
            model: Model name/ID to use for completions.
            timeout: Request timeout in seconds (default: 30).
            **kwargs: Additional provider-specific configuration parameters.
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.config = kwargs
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion from a prompt.
        
        Core method for all providers. Implementations should handle:
        - Message construction (system + user prompts)
        - API calls with proper error handling
        - Response extraction and parsing
        - Timeout and retry logic
        
        Args:
            prompt: The user-facing prompt/input.
            system_prompt: Optional system-level instructions that shape behavior.
            temperature: Sampling temperature (0.0-1.0+). Higher = more creative.
            max_tokens: Maximum tokens in response (provider-dependent).
            **kwargs: Additional provider-specific parameters.
            
        Returns:
            Generated text response from the model.
            
        Raises:
            ValueError: If inputs are invalid.
            RuntimeError: If provider communication fails.
            TimeoutError: If request exceeds timeout.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate()")
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that the provider credentials are valid and working.
        
        Should perform a lightweight test (e.g., small API call) to verify
        the API key is valid without consuming significant quota.
        
        Returns:
            True if credentials are valid and provider is reachable, False otherwise.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement validate_credentials()")
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information and capabilities of the current model.
        
        Returns metadata about the model being used, such as:
        - Maximum context length
        - Supported features
        - Model version/release date
        - Rate limits
        
        Returns:
            Dictionary containing model metadata and capabilities.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_model_info()")
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(model={self.model})"
