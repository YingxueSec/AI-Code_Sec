"""
Qwen LLM provider implementation for SiliconFlow API.

This module implements the Qwen provider for accessing Qwen models
through the SiliconFlow API service.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
import logging

from ai_code_audit.llm.base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMUsage, 
    LLMModelType, MessageRole, LLMMessage
)
from ai_code_audit.core.exceptions import LLMError, LLMAPIError, LLMRateLimitError

logger = logging.getLogger(__name__)


class QwenProvider(BaseLLMProvider):
    """Qwen LLM provider using SiliconFlow API."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize Qwen provider.
        
        Args:
            api_key: SiliconFlow API key
            base_url: Optional custom base URL (defaults to SiliconFlow API)
        """
        if base_url is None:
            base_url = "https://api.siliconflow.cn/v1"
        
        super().__init__(api_key, base_url)
        self.max_retries = 3
        self.retry_delay = 1.0
    
    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "qwen"
    
    @property
    def supported_models(self) -> List[LLMModelType]:
        """Get list of supported Qwen models."""
        return [
            LLMModelType.QWEN_CODER_30B,
        ]
    
    def get_max_context_length(self, model: LLMModelType) -> int:
        """Get maximum context length for Qwen models."""
        context_lengths = {
            LLMModelType.QWEN_CODER_30B: 262144,  # 256K tokens (262,144)
        }
        return context_lengths.get(model, 262144)
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """
        Send chat completion request to Qwen API.
        
        Args:
            request: LLM request with messages and parameters
            
        Returns:
            LLM response with generated content
            
        Raises:
            LLMError: If request fails
        """
        # Validate request
        self.validate_request(request)
        
        # Prepare API request
        api_request = self._prepare_api_request(request)
        
        # Send request with retries
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                response = await self._send_request(api_request)
                response_time = time.time() - start_time

                return self._parse_response(response, request.model.value, response_time)

            except RecursionError:
                # 递归错误不重试
                logger.error("RecursionError detected, stopping all retries")
                raise LLMError("Maximum recursion depth exceeded")

            except LLMRateLimitError:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

            except LLMAPIError as e:
                # 检查错误类型，某些错误不应该重试
                error_str = str(e).lower()
                if "maximum recursion depth exceeded" in error_str or "recursion" in error_str:
                    logger.error("Recursion depth error in API call, stopping retries")
                    raise LLMError("Recursion depth exceeded in API call")

                if attempt < self.max_retries - 1 and e.is_retryable:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
        
        raise LLMError("Max retries exceeded")
    
    async def validate_api_key(self) -> bool:
        """
        Validate API key by making a test request.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Create a minimal test request
            test_request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "Hello")],
                model=LLMModelType.QWEN_CODER_30B,
                max_tokens=1
            )
            
            await self.chat_completion(test_request)
            return True
            
        except LLMError as e:
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                return False
            # Other errors might indicate valid key but other issues
            return True
        except Exception:
            return False
    
    def _prepare_api_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepare API request payload."""
        payload = request.to_api_format()

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        # Use the model name directly from the enum value
        payload["model"] = request.model.value

        return payload
    
    async def _send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send HTTP request to API."""
        session = await self.get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    return response_data
                elif response.status == 401:
                    raise LLMAPIError("Authentication failed - invalid API key", status_code=401)
                elif response.status == 429:
                    raise LLMRateLimitError("Rate limit exceeded", status_code=429)
                elif response.status >= 500:
                    raise LLMAPIError(f"Server error: {response_data}", status_code=response.status, is_retryable=True)
                else:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise LLMAPIError(f"API error: {error_msg}", status_code=response.status)
        
        except asyncio.TimeoutError:
            raise LLMAPIError("Request timeout", is_retryable=True)
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMAPIError(f"Request failed: {e}", is_retryable=True)
    
    def _parse_response(self, response_data: Dict[str, Any], model: str, response_time: float) -> LLMResponse:
        """Parse API response into LLMResponse object."""
        try:
            # Extract content
            choices = response_data.get("choices", [])
            if not choices:
                raise LLMError("No choices in response")
            
            choice = choices[0]
            content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason")
            
            # Extract usage information
            usage_data = response_data.get("usage", {})
            usage = None
            if usage_data:
                usage = LLMUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )
            
            return LLMResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                response_time=response_time,
                metadata={
                    "provider": self.provider_name,
                    "raw_response": response_data,
                }
            )
            
        except KeyError as e:
            raise LLMError(f"Invalid response format: missing {e}")
        except Exception as e:
            raise LLMError(f"Failed to parse response: {e}")
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from API."""
        session = await self.get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        url = f"{self.base_url}/models"
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    return [model.get("id", "") for model in models if "qwen" in model.get("id", "").lower()]
                else:
                    logger.warning(f"Failed to get models list: {response.status}")
                    return []
        
        except Exception as e:
            logger.warning(f"Failed to get models list: {e}")
            return []
    
    def estimate_cost(self, request: LLMRequest, response: LLMResponse) -> float:
        """Estimate cost for request/response pair."""
        if not response.usage:
            return 0.0
        
        # SiliconFlow pricing (approximate, as of 2024)
        pricing = {
            LLMModelType.QWEN_CODER_30B: {"input": 0.001, "output": 0.002},  # per 1K tokens
        }
        
        model_pricing = pricing.get(request.model, {"input": 0.001, "output": 0.002})
        
        input_cost = (response.usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (response.usage.completion_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost

    async def validate_api_key(self) -> bool:
        """Validate API key by making a test request."""
        try:
            # Create a simple test request
            test_request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.QWEN_CODER_30B,
                max_tokens=1,
                temperature=0.1
            )

            # Try to make a request
            response = await self.chat_completion(test_request)
            return response is not None

        except Exception:
            return False
