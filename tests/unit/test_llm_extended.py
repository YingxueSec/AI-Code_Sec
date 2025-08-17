"""
Extended LLM integration tests.

This module provides comprehensive testing for:
- Multiple LLM provider integrations (OpenAI, Claude, Local models)
- Advanced LLM manager functionality
- Error handling and fallback mechanisms
- Performance and rate limiting
- Real-world usage scenarios
"""

import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.llm.base import BaseLLMProvider, LLMResponse, LLMRequest, LLMMessage, MessageRole, LLMModelType
from ai_code_audit.llm.qwen_provider import QwenProvider
from ai_code_audit.llm.kimi_provider import KimiProvider
from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.core.exceptions import LLMError, LLMAPIError, LLMRateLimitError
from ai_code_audit.core.config import LLMProviderConfig, LLMConfig


class TestExtendedLLMProviders:
    """Extended tests for LLM provider implementations."""
    
    @pytest.fixture
    def provider_configs(self):
        """Fixture providing multiple provider configurations."""
        return {
            'qwen': LLMProviderConfig(
                api_key="test_qwen_key",
                base_url="https://api.siliconflow.cn/v1",
                enabled=True,
                priority=1,
                cost_weight=0.8
            ),
            'kimi': LLMProviderConfig(
                api_key="test_kimi_key", 
                base_url="https://api.moonshot.cn/v1",
                enabled=True,
                priority=2,
                cost_weight=1.0
            )
        }
    
    @pytest.mark.asyncio
    async def test_provider_error_handling(self, provider_configs):
        """Test provider error handling scenarios."""
        provider = QwenProvider(
            api_key=provider_configs['qwen'].api_key,
            base_url=provider_configs['qwen'].base_url
        )
        
        # Test API error handling
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 429  # Rate limit error
            mock_response.json = AsyncMock(return_value={
                "error": {
                    "message": "Rate limit exceeded",
                    "type": "rate_limit_error"
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.QWEN_CODER_30B
            )
            
            with pytest.raises(LLMRateLimitError):
                await provider.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_provider_retry_mechanism(self, provider_configs):
        """Test provider retry mechanism on failures."""
        provider = QwenProvider(
            api_key=provider_configs['qwen'].api_key,
            base_url=provider_configs['qwen'].base_url
        )
        
        # Mock first call fails, second succeeds
        with patch('aiohttp.ClientSession.post') as mock_post:
            # First call - network error
            mock_error_response = Mock()
            mock_error_response.status = 500
            mock_error_response.json = AsyncMock(side_effect=Exception("Network error"))
            
            # Second call - success
            mock_success_response = Mock()
            mock_success_response.status = 200
            mock_success_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {"content": "Success after retry", "role": "assistant"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            })
            
            mock_post.return_value.__aenter__.side_effect = [
                mock_error_response,
                mock_success_response
            ]
            
            request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.QWEN_CODER_30B
            )
            
            result = await provider.chat_completion(request)
            assert result.content == "Success after retry"
            assert mock_post.call_count == 2  # Verify retry happened
    
    @pytest.mark.asyncio
    async def test_provider_api_key_validation(self, provider_configs):
        """Test API key validation functionality."""
        provider = QwenProvider(
            api_key=provider_configs['qwen'].api_key,
            base_url=provider_configs['qwen'].base_url
        )
        
        # Mock successful validation
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {"content": "test", "role": "assistant"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            is_valid = await provider.validate_api_key()
            assert is_valid is True
        
        # Mock failed validation
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 401  # Unauthorized
            mock_response.json = AsyncMock(return_value={
                "error": {"message": "Invalid API key", "type": "authentication_error"}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            is_valid = await provider.validate_api_key()
            assert is_valid is False


class TestLLMManagerExtended:
    """Extended tests for LLM manager functionality."""
    
    @pytest_asyncio.fixture
    async def llm_manager(self):
        """Fixture providing configured LLM manager."""
        config = {
            'llm': {
                'qwen': {
                    'api_key': 'test_qwen_key',
                    'base_url': 'https://api.siliconflow.cn/v1',
                    'enabled': True,
                    'priority': 1,
                    'max_requests_per_minute': 60,
                    'cost_weight': 0.8,
                    'performance_weight': 1.0
                },
                'kimi': {
                    'api_key': 'test_kimi_key',
                    'base_url': 'https://api.moonshot.cn/v1',
                    'enabled': True,
                    'priority': 2,
                    'max_requests_per_minute': 60,
                    'cost_weight': 1.0,
                    'performance_weight': 1.0
                }
            }
        }

        manager = LLMManager(config)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_manager_provider_selection(self, llm_manager):
        """Test manager provider selection logic."""
        # Mock both providers
        with patch.object(llm_manager.providers['qwen'], 'chat_completion') as mock_qwen, \
             patch.object(llm_manager.providers['kimi'], 'chat_completion') as mock_kimi:
            
            from ai_code_audit.llm.base import LLMUsage
            mock_qwen.return_value = LLMResponse(
                content="Qwen response",
                model=LLMModelType.QWEN_CODER_30B.value,
                usage=LLMUsage(prompt_tokens=50, completion_tokens=50, total_tokens=100),
                finish_reason="stop"
            )
            
            request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.QWEN_CODER_30B
            )
            
            result = await llm_manager.chat_completion(request)
            
            # Should use Qwen (higher priority)
            assert result.content == "Qwen response"
            mock_qwen.assert_called_once()
            mock_kimi.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_manager_fallback_mechanism(self, llm_manager):
        """Test manager fallback to secondary provider."""
        with patch.object(llm_manager.providers['qwen'], 'chat_completion') as mock_qwen, \
             patch.object(llm_manager.providers['kimi'], 'chat_completion') as mock_kimi, \
             patch.object(llm_manager.providers['qwen'], 'is_model_supported') as mock_qwen_support, \
             patch.object(llm_manager.providers['kimi'], 'is_model_supported') as mock_kimi_support:

            # Both providers support the model
            mock_qwen_support.return_value = True
            mock_kimi_support.return_value = True

            # Qwen fails
            mock_qwen.side_effect = LLMAPIError("Qwen API error")

            # Kimi succeeds
            from ai_code_audit.llm.base import LLMUsage
            mock_kimi.return_value = LLMResponse(
                content="Kimi fallback response",
                model=LLMModelType.QWEN_CODER_30B.value,  # Use same model for consistency
                usage=LLMUsage(prompt_tokens=50, completion_tokens=50, total_tokens=100),
                finish_reason="stop"
            )

            request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.QWEN_CODER_30B
            )

            result = await llm_manager.chat_completion(request)

            # Should fallback to Kimi
            assert result.content == "Kimi fallback response"
            mock_qwen.assert_called_once()
            mock_kimi.assert_called_once()


class TestLLMPerformance:
    """Performance and load testing for LLM integration."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent LLM requests."""
        provider = QwenProvider(api_key="test_key", base_url="https://test.api")
        
        # Mock successful responses
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {"content": "Concurrent response", "role": "assistant"},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Create multiple concurrent requests
            requests = [
                LLMRequest(
                    messages=[LLMMessage(MessageRole.USER, f"test {i}")],
                    model=LLMModelType.QWEN_CODER_30B
                )
                for i in range(5)
            ]
            
            # Execute concurrently
            start_time = time.time()
            results = await asyncio.gather(*[
                provider.chat_completion(req) for req in requests
            ])
            end_time = time.time()
            
            # Verify all requests completed
            assert len(results) == 5
            assert all(r.content == "Concurrent response" for r in results)
            
            # Should complete in reasonable time (concurrent, not sequential)
            assert end_time - start_time < 2.0  # Assuming each mock takes minimal time
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self):
        """Test rate limiting behavior and backoff."""
        provider = QwenProvider(api_key="test_key", base_url="https://test.api")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # First request hits rate limit
            mock_rate_limit_response = Mock()
            mock_rate_limit_response.status = 429
            mock_rate_limit_response.json = AsyncMock(return_value={
                "error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}
            })
            
            mock_post.return_value.__aenter__.return_value = mock_rate_limit_response
            
            request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "test")],
                model=LLMModelType.QWEN_CODER_30B
            )
            
            with pytest.raises(LLMRateLimitError):
                await provider.chat_completion(request)
