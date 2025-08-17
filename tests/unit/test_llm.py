"""
Unit tests for LLM integration functionality.

This module tests the LLM providers, manager, and prompt system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ai_code_audit.llm.base import (
    LLMRequest, LLMResponse, LLMMessage, LLMUsage, 
    MessageRole, LLMModelType, BaseLLMProvider
)
from ai_code_audit.llm.qwen_provider import QwenProvider
from ai_code_audit.llm.kimi_provider import KimiProvider
from ai_code_audit.llm.manager import LLMManager, ProviderConfig, LoadBalancingStrategy
from ai_code_audit.llm.prompts import PromptManager, PromptTemplate, PromptType
from ai_code_audit.core.exceptions import LLMError, LLMAPIError, LLMRateLimitError


class TestLLMBase:
    """Test base LLM classes and data models."""
    
    def test_llm_message_creation(self):
        """Test LLM message creation."""
        message = LLMMessage(MessageRole.USER, "Hello, world!")
        
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.timestamp is not None
        assert isinstance(message.timestamp, datetime)
    
    def test_llm_message_to_dict(self):
        """Test LLM message dictionary conversion."""
        message = LLMMessage(MessageRole.SYSTEM, "You are a helpful assistant.")
        
        result = message.to_dict()
        
        assert result == {
            "role": "system",
            "content": "You are a helpful assistant."
        }
    
    def test_llm_request_creation(self):
        """Test LLM request creation."""
        messages = [
            LLMMessage(MessageRole.SYSTEM, "You are a helpful assistant."),
            LLMMessage(MessageRole.USER, "Hello!")
        ]
        
        request = LLMRequest(
            messages=messages,
            model=LLMModelType.QWEN_TURBO,
            temperature=0.5,
            max_tokens=100
        )
        
        assert len(request.messages) == 2
        assert request.model == LLMModelType.QWEN_TURBO
        assert request.temperature == 0.5
        assert request.max_tokens == 100
    
    def test_llm_request_add_messages(self):
        """Test adding messages to LLM request."""
        request = LLMRequest(
            messages=[],
            model=LLMModelType.QWEN_TURBO
        )
        
        request.add_system_message("You are a helpful assistant.")
        request.add_user_message("Hello!")
        
        assert len(request.messages) == 2
        assert request.messages[0].role == MessageRole.SYSTEM
        assert request.messages[1].role == MessageRole.USER
    
    def test_llm_request_to_api_format(self):
        """Test LLM request API format conversion."""
        request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Hello!")],
            model=LLMModelType.QWEN_TURBO,
            temperature=0.5
        )
        
        api_format = request.to_api_format()
        
        assert api_format["model"] == "qwen-turbo"
        assert api_format["temperature"] == 0.5
        assert len(api_format["messages"]) == 1
        assert api_format["messages"][0]["role"] == "user"
    
    def test_llm_usage_cost_estimate(self):
        """Test LLM usage cost estimation."""
        usage = LLMUsage(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost = usage.cost_estimate
        
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_llm_response_properties(self):
        """Test LLM response properties."""
        response = LLMResponse(
            content="Hello! How can I help you?",
            model="qwen-turbo",
            finish_reason="stop"
        )
        
        assert response.is_complete
        assert not response.was_truncated
        
        response_truncated = LLMResponse(
            content="This response was cut off...",
            model="qwen-turbo",
            finish_reason="length"
        )
        
        assert response_truncated.was_truncated


class TestQwenProvider:
    """Test Qwen provider functionality."""
    
    def test_qwen_provider_initialization(self):
        """Test Qwen provider initialization."""
        provider = QwenProvider(api_key="test-key")
        
        assert provider.provider_name == "qwen"
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.siliconflow.cn/v1"
        assert LLMModelType.QWEN_TURBO in provider.supported_models
    
    def test_qwen_provider_model_support(self):
        """Test Qwen provider model support."""
        provider = QwenProvider(api_key="test-key")
        
        assert provider.is_model_supported(LLMModelType.QWEN_TURBO)
        assert provider.is_model_supported(LLMModelType.QWEN_PLUS)
        assert provider.is_model_supported(LLMModelType.QWEN_MAX)
        assert not provider.is_model_supported(LLMModelType.KIMI_8K)
    
    def test_qwen_provider_context_length(self):
        """Test Qwen provider context length."""
        provider = QwenProvider(api_key="test-key")
        
        assert provider.get_max_context_length(LLMModelType.QWEN_TURBO) == 8192
        assert provider.get_max_context_length(LLMModelType.QWEN_PLUS) == 32768
        assert provider.get_max_context_length(LLMModelType.QWEN_MAX) == 32768
    
    def test_qwen_provider_prepare_api_request(self):
        """Test Qwen provider API request preparation."""
        provider = QwenProvider(api_key="test-key")
        
        request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Hello!")],
            model=LLMModelType.QWEN_TURBO
        )
        
        api_request = provider._prepare_api_request(request)
        
        assert api_request["model"] == "Qwen/Qwen2.5-7B-Instruct"
        assert "messages" in api_request


class TestKimiProvider:
    """Test Kimi provider functionality."""
    
    def test_kimi_provider_initialization(self):
        """Test Kimi provider initialization."""
        provider = KimiProvider(api_key="test-key")
        
        assert provider.provider_name == "kimi"
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.moonshot.cn/v1"
        assert LLMModelType.KIMI_8K in provider.supported_models
    
    def test_kimi_provider_model_support(self):
        """Test Kimi provider model support."""
        provider = KimiProvider(api_key="test-key")
        
        assert provider.is_model_supported(LLMModelType.KIMI_8K)
        assert provider.is_model_supported(LLMModelType.KIMI_32K)
        assert provider.is_model_supported(LLMModelType.KIMI_128K)
        assert not provider.is_model_supported(LLMModelType.QWEN_TURBO)
    
    def test_kimi_provider_context_length(self):
        """Test Kimi provider context length."""
        provider = KimiProvider(api_key="test-key")
        
        assert provider.get_max_context_length(LLMModelType.KIMI_8K) == 8192
        assert provider.get_max_context_length(LLMModelType.KIMI_32K) == 32768
        assert provider.get_max_context_length(LLMModelType.KIMI_128K) == 131072
    
    def test_kimi_provider_long_context_support(self):
        """Test Kimi provider long context support."""
        provider = KimiProvider(api_key="test-key")
        
        assert not provider.supports_long_context(LLMModelType.KIMI_8K)
        assert not provider.supports_long_context(LLMModelType.KIMI_32K)
        assert provider.supports_long_context(LLMModelType.KIMI_128K)
    
    def test_kimi_provider_model_recommendation(self):
        """Test Kimi provider model recommendation."""
        provider = KimiProvider(api_key="test-key")
        
        assert provider.get_recommended_model_for_context_length(5000) == LLMModelType.KIMI_8K
        assert provider.get_recommended_model_for_context_length(20000) == LLMModelType.KIMI_32K
        assert provider.get_recommended_model_for_context_length(50000) == LLMModelType.KIMI_128K


class TestLLMManager:
    """Test LLM manager functionality."""
    
    def test_llm_manager_initialization_no_providers(self):
        """Test LLM manager initialization with no providers."""
        config = {'llm': {}}
        
        manager = LLMManager(config)
        
        # Should not raise exception, just log warning
        assert len(manager.providers) == 0
    
    def test_llm_manager_initialization_with_providers(self):
        """Test LLM manager initialization with providers."""
        config = {
            'llm': {
                'qwen': {
                    'api_key': 'test-qwen-key',
                    'enabled': True
                },
                'kimi': {
                    'api_key': 'test-kimi-key',
                    'enabled': True
                }
            }
        }
        
        manager = LLMManager(config)
        
        assert 'qwen' in manager.providers
        assert 'kimi' in manager.providers
        assert len(manager.providers) == 2
    
    def test_llm_manager_provider_order_cost_optimized(self):
        """Test LLM manager cost-optimized provider ordering."""
        config = {
            'llm': {
                'qwen': {
                    'api_key': 'test-qwen-key',
                    'enabled': True,
                    'cost_weight': 1.0
                },
                'kimi': {
                    'api_key': 'test-kimi-key',
                    'enabled': True,
                    'cost_weight': 1.5
                }
            }
        }
        
        manager = LLMManager(config)
        manager.set_load_balancing_strategy(LoadBalancingStrategy.COST_OPTIMIZED)
        
        request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Hello!")],
            model=LLMModelType.QWEN_TURBO
        )
        
        provider_order = manager._get_provider_order(request)
        
        # Qwen should come first (lower cost weight)
        assert provider_order[0] == 'qwen'
    
    def test_llm_manager_get_available_models(self):
        """Test LLM manager get available models."""
        config = {
            'llm': {
                'qwen': {
                    'api_key': 'test-qwen-key',
                    'enabled': True
                }
            }
        }
        
        manager = LLMManager(config)
        models = manager.get_available_models()
        
        assert 'qwen' in models
        assert LLMModelType.QWEN_TURBO in models['qwen']
    
    def test_llm_manager_provider_stats(self):
        """Test LLM manager provider statistics."""
        config = {
            'llm': {
                'qwen': {
                    'api_key': 'test-qwen-key',
                    'enabled': True
                }
            }
        }
        
        manager = LLMManager(config)
        stats = manager.get_provider_stats()
        
        assert 'qwen' in stats
        assert stats['qwen']['provider_type'] == 'qwen'
        assert stats['qwen']['enabled'] == True
        assert stats['qwen']['request_count'] == 0


class TestPromptManager:
    """Test prompt manager functionality."""
    
    def test_prompt_manager_initialization(self):
        """Test prompt manager initialization."""
        manager = PromptManager()
        
        assert len(manager.templates) > 0
        assert 'security_audit' in manager.templates
        assert 'code_review' in manager.templates
    
    def test_prompt_manager_get_template(self):
        """Test getting prompt template."""
        manager = PromptManager()
        
        template = manager.get_template('security_audit')
        
        assert template is not None
        assert template.name == 'security_audit'
        assert template.type == PromptType.SECURITY_AUDIT
        assert len(template.variables) > 0
    
    def test_prompt_manager_list_templates(self):
        """Test listing prompt templates."""
        manager = PromptManager()
        
        templates = manager.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert 'security_audit' in templates
    
    def test_prompt_manager_get_templates_by_type(self):
        """Test getting templates by type."""
        manager = PromptManager()
        
        security_templates = manager.get_templates_by_type(PromptType.SECURITY_AUDIT)
        
        assert len(security_templates) > 0
        assert all(t.type == PromptType.SECURITY_AUDIT for t in security_templates)
    
    def test_prompt_manager_generate_prompt(self):
        """Test generating prompt from template."""
        manager = PromptManager()
        
        variables = {
            'language': 'python',
            'file_path': 'test.py',
            'project_type': 'web_application',
            'dependencies': 'flask, requests',
            'code_content': 'print("Hello, world!")',
            'additional_context': 'This is a test file'
        }
        
        prompt = manager.generate_prompt('security_audit', variables)
        
        assert prompt is not None
        assert 'system' in prompt
        assert 'user' in prompt
        assert 'metadata' in prompt
        assert 'python' in prompt['user']
        assert 'test.py' in prompt['user']
    
    def test_prompt_manager_generate_prompt_missing_variables(self):
        """Test generating prompt with missing variables."""
        manager = PromptManager()
        
        variables = {
            'language': 'python',
            # Missing other required variables
        }
        
        prompt = manager.generate_prompt('security_audit', variables)
        
        assert prompt is None
    
    def test_prompt_manager_validate_template(self):
        """Test template validation."""
        manager = PromptManager()
        
        # Valid template
        valid_template = PromptTemplate(
            name="test_template",
            type=PromptType.CODE_REVIEW,
            system_prompt="You are a code reviewer.",
            user_prompt_template="Review this {language} code: {code}",
            variables=["language", "code"],
            max_context_length=8192,
            temperature=0.1
        )
        
        errors = manager.validate_template(valid_template)
        assert len(errors) == 0
        
        # Invalid template (missing variable)
        invalid_template = PromptTemplate(
            name="invalid_template",
            type=PromptType.CODE_REVIEW,
            system_prompt="You are a code reviewer.",
            user_prompt_template="Review this {language} code: {code}",
            variables=["language"],  # Missing 'code' variable
            max_context_length=8192,
            temperature=0.1
        )
        
        errors = manager.validate_template(invalid_template)
        assert len(errors) > 0
    
    def test_prompt_manager_add_remove_template(self):
        """Test adding and removing templates."""
        manager = PromptManager()
        
        initial_count = len(manager.templates)
        
        # Add template
        new_template = PromptTemplate(
            name="test_template",
            type=PromptType.CODE_REVIEW,
            system_prompt="Test system prompt",
            user_prompt_template="Test user prompt",
            variables=[],
        )
        
        manager.add_template(new_template)
        assert len(manager.templates) == initial_count + 1
        assert 'test_template' in manager.templates
        
        # Remove template
        success = manager.remove_template('test_template')
        assert success
        assert len(manager.templates) == initial_count
        assert 'test_template' not in manager.templates


if __name__ == "__main__":
    pytest.main([__file__])
