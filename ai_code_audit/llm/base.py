"""
Base classes for LLM integration.

This module defines the abstract base classes and data models
for LLM provider implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

from ai_code_audit.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMModelType(Enum):
    """Supported LLM model types."""
    # Qwen models (through SiliconFlow)
    QWEN_CODER_30B = "Qwen/Qwen3-Coder-30B-A3B-Instruct"

    # Kimi models (through SiliconFlow)
    KIMI_K2 = "moonshotai/Kimi-K2-Instruct"


class MessageRole(Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """A single message in LLM conversation."""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API calls."""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class LLMRequest:
    """Request to LLM provider."""
    messages: List[LLMMessage]
    model: LLMModelType
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def add_message(self, role: MessageRole, content: str) -> None:
        """Add a message to the request."""
        self.messages.append(LLMMessage(role=role, content=content))
    
    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message(MessageRole.SYSTEM, content)
    
    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message(MessageRole.USER, content)
    
    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API format."""
        return {
            "model": self.model.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
        }


@dataclass
class LLMUsage:
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost in USD (rough approximation)."""
        # Very rough cost estimation - should be updated with actual pricing
        input_cost_per_1k = 0.001  # $0.001 per 1K input tokens
        output_cost_per_1k = 0.002  # $0.002 per 1K output tokens
        
        input_cost = (self.prompt_tokens / 1000) * input_cost_per_1k
        output_cost = (self.completion_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None
    response_time: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_complete(self) -> bool:
        """Check if response is complete."""
        return self.finish_reason in ["stop", "end_turn", None]
    
    @property
    def was_truncated(self) -> bool:
        """Check if response was truncated due to length."""
        return self.finish_reason == "length"


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize provider with API key and optional base URL."""
        self.api_key = api_key
        self.base_url = base_url
        self._session = None
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[LLMModelType]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """
        Send chat completion request to LLM.
        
        Args:
            request: LLM request with messages and parameters
            
        Returns:
            LLM response with generated content
            
        Raises:
            LLMError: If request fails
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate API key by making a test request.
        
        Returns:
            True if API key is valid, False otherwise
        """
        pass
    
    async def get_session(self):
        """Get or create HTTP session."""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def is_model_supported(self, model: LLMModelType) -> bool:
        """Check if model is supported by this provider."""
        return model in self.supported_models
    
    def get_max_context_length(self, model: LLMModelType) -> int:
        """Get maximum context length for model."""
        # Default context lengths - should be overridden by providers
        context_lengths = {
            LLMModelType.QWEN_CODER_30B: 262144,  # 256K tokens (262,144)
            LLMModelType.KIMI_K2: 128000,         # 128K tokens
        }
        return context_lengths.get(model, 4096)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Very rough estimation: ~4 characters per token for English
        # This should be replaced with proper tokenization
        return len(text) // 4
    
    def validate_request(self, request: LLMRequest) -> None:
        """
        Validate request before sending.
        
        Args:
            request: LLM request to validate
            
        Raises:
            LLMError: If request is invalid
        """
        if not request.messages:
            raise LLMError("Request must contain at least one message")
        
        if not self.is_model_supported(request.model):
            raise LLMError(f"Model {request.model.value} not supported by {self.provider_name}")
        
        # Check context length
        total_tokens = sum(self.estimate_tokens(msg.content) for msg in request.messages)
        max_context = self.get_max_context_length(request.model)
        
        if total_tokens > max_context * 0.8:  # Leave some room for response
            logger.warning(f"Request may exceed context limit: {total_tokens} tokens (max: {max_context})")
        
        # Validate parameters
        if not 0.0 <= request.temperature <= 2.0:
            raise LLMError("Temperature must be between 0.0 and 2.0")
        
        if not 0.0 <= request.top_p <= 1.0:
            raise LLMError("Top-p must be between 0.0 and 1.0")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name})"
