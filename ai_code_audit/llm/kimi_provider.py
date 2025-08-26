"""
Kimi LLM provider implementation for SiliconFlow API.

This module implements the Kimi provider for accessing Kimi models
through the SiliconFlow API service (same as Qwen).
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
import logging
import aiohttp

from ai_code_audit.llm.base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMUsage,
    LLMModelType, MessageRole, LLMMessage
)
from ai_code_audit.core.exceptions import LLMError, LLMAPIError, LLMRateLimitError
from ai_code_audit.llm.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)


class KimiProvider(BaseLLMProvider):
    """Kimi LLM provider using SiliconFlow API."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize Kimi provider.

        Args:
            api_key: SiliconFlow API key (same as Qwen)
            base_url: Optional custom base URL (defaults to SiliconFlow API)
        """
        if base_url is None:
            base_url = "https://api.siliconflow.cn/v1"

        super().__init__(api_key, base_url)
        self.max_retries = 5  # 增加重试次数
        self.base_retry_delay = 1.0
        self.max_retry_delay = 60.0  # 最大重试延迟
        self.timeout_multiplier = 1.5  # 超时后的延迟倍数
        self.rate_limiter = get_rate_limiter()  # TPM/RPM限制管理

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "kimi"

    @property
    def supported_models(self) -> List[LLMModelType]:
        """Get list of supported Kimi models."""
        return [
            LLMModelType.KIMI_K2,
        ]

    def get_max_context_length(self, model: LLMModelType) -> int:
        """Get maximum context length for Kimi models."""
        context_lengths = {
            LLMModelType.KIMI_K2: 128000,     # 128K context for K2 model
        }
        return context_lengths.get(model, 128000)

    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """
        Send chat completion request to Kimi API.

        Args:
            request: LLM request with messages and parameters

        Returns:
            LLM response with generated content

        Raises:
            LLMError: If request fails
        """
        # Validate request
        self.validate_request(request)

        # 估算内容长度用于TPM限制
        content_length = sum(len(msg.content) for msg in request.messages)

        # 应用TPM/RPM限制
        if not await self.rate_limiter.acquire_with_estimation(content_length):
            raise LLMRateLimitError("Rate limit exceeded - TPM or RPM limit reached")

        # Prepare API request
        api_request = self._prepare_api_request(request)

        # Send request with retries
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                response = await self._send_request(api_request)
                response_time = time.time() - start_time

                parsed_response = self._parse_response(response, request.model.value, response_time)

                # 记录实际token使用量
                if parsed_response.usage and parsed_response.usage.total_tokens:
                    self.rate_limiter.record_actual_usage(parsed_response.usage.total_tokens)
                else:
                    # 如果没有usage信息，使用估算值
                    estimated_tokens = self.rate_limiter._estimate_tokens(content_length)
                    self.rate_limiter.record_actual_usage(estimated_tokens)

                return parsed_response

            except LLMRateLimitError:
                if attempt < self.max_retries - 1:
                    # 限流错误使用更长的延迟
                    delay = min(self.base_retry_delay * (3 ** attempt), self.max_retry_delay)
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

            except LLMAPIError as e:
                if attempt < self.max_retries - 1 and e.is_retryable:
                    # 根据错误类型调整延迟策略
                    if e.status_code == 502:
                        # 服务器错误，等待更长时间
                        delay = min(self.base_retry_delay * (4 ** attempt), self.max_retry_delay)
                        logger.warning(f"Server error (502), retrying in {delay}s: {e}")
                    elif e.status_code == 503:
                        # 服务不可用，等待更长时间
                        delay = min(self.base_retry_delay * (5 ** attempt), self.max_retry_delay)
                        logger.warning(f"Service unavailable (503), retrying in {delay}s: {e}")
                    elif "timeout" in str(e).lower():
                        # 超时错误，使用超时倍数
                        delay = min(self.base_retry_delay * self.timeout_multiplier * (2 ** attempt), self.max_retry_delay)
                        logger.warning(f"Timeout error, retrying in {delay}s: {e}")
                    else:
                        # 其他错误，标准指数退避
                        delay = min(self.base_retry_delay * (2 ** attempt), self.max_retry_delay)
                        logger.warning(f"API error, retrying in {delay}s: {e}")

                    await asyncio.sleep(delay)
                    continue
                else:
                    # 记录错误到限流器
                    self.rate_limiter.record_error()
                    raise

        # 记录错误到限流器
        self.rate_limiter.record_error()
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
                model=LLMModelType.KIMI_K2,
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
            raise LLMAPIError("Request timeout - consider increasing timeout or reducing request size", is_retryable=True)
        except aiohttp.ClientConnectorError as e:
            raise LLMAPIError(f"Connection error: {e}", is_retryable=True)
        except aiohttp.ClientResponseError as e:
            if e.status == 502:
                raise LLMAPIError(f"Bad Gateway (502): {e}", status_code=502, is_retryable=True)
            elif e.status == 503:
                raise LLMAPIError(f"Service Unavailable (503): {e}", status_code=503, is_retryable=True)
            elif e.status == 504:
                raise LLMAPIError(f"Gateway Timeout (504): {e}", status_code=504, is_retryable=True)
            else:
                raise LLMAPIError(f"HTTP error {e.status}: {e}", status_code=e.status, is_retryable=e.status >= 500)
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
                    return [model.get("id", "") for model in models if "moonshot" in model.get("id", "").lower()]
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

        # SiliconFlow pricing for Kimi (approximate, as of 2024)
        pricing = {
            LLMModelType.KIMI_K2: {"input": 0.001, "output": 0.002},  # per 1K tokens
        }

        model_pricing = pricing.get(request.model, {"input": 0.001, "output": 0.002})

        input_cost = (response.usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (response.usage.completion_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost

    def supports_long_context(self, model: LLMModelType) -> bool:
        """Check if model supports long context (>32K tokens)."""
        return model == LLMModelType.KIMI_128K

    def get_recommended_model_for_context_length(self, estimated_tokens: int) -> LLMModelType:
        """Get recommended model based on context length requirements."""
        # Only KIMI_K2 is available, so always return it
        return LLMModelType.KIMI_K2

    async def validate_api_key(self) -> bool:
        """Validate API key by making a test request."""
        try:
            # Create a simple test request
            test_request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.KIMI_K2,
                max_tokens=1,
                temperature=0.1
            )

            # Try to make a request
            response = await self.chat_completion(test_request)
            return response is not None

        except Exception:
            return False
