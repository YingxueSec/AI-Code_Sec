"""
Unit tests for LLM integration functionality.

This module tests:
- LLM provider implementations (Qwen, Kimi)
- LLM manager and load balancing
- Prompt template management
- Error handling and fallback mechanisms
- Rate limiting and cost optimization
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.llm.base import BaseLLMProvider, LLMResponse, LLMRequest, LLMMessage, MessageRole
from ai_code_audit.llm.qwen_provider import QwenProvider
from ai_code_audit.llm.kimi_provider import KimiProvider
from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.llm.prompts import PromptTemplate, PromptManager
from ai_code_audit.core.exceptions import LLMError
from ai_code_audit.core.config import LLMConfig


class TestLLMProviders:
    """Test individual LLM provider implementations."""
    
    @pytest.fixture
    def qwen_config(self):
        """Fixture providing Qwen configuration."""
        from ai_code_audit.core.config import LLMProviderConfig
        return LLMProviderConfig(
            api_key="test_qwen_key",
            base_url="https://api.siliconflow.cn/v1",
            enabled=True,
            priority=1,
            cost_weight=0.8
        )
    
    @pytest.fixture
    def kimi_config(self):
        """Fixture providing Kimi configuration."""
        from ai_code_audit.core.config import LLMProviderConfig
        return LLMProviderConfig(
            api_key="test_kimi_key",
            base_url="https://api.moonshot.cn/v1",
            enabled=True,
            priority=2,
            cost_weight=1.0
        )
    
    @pytest.mark.asyncio
    async def test_qwen_provider_initialization(self, qwen_config):
        """Test Qwen provider initialization."""
        provider = QwenProvider(
            api_key=qwen_config.api_key,
            base_url=qwen_config.base_url
        )

        assert provider.provider_name == "qwen"
        assert provider.api_key == qwen_config.api_key
        assert provider.base_url == qwen_config.base_url
    
    @pytest.mark.asyncio
    async def test_kimi_provider_initialization(self, kimi_config):
        """Test Kimi provider initialization."""
        provider = KimiProvider(
            api_key=kimi_config.api_key,
            base_url=kimi_config.base_url
        )

        assert provider.provider_name == "kimi"
        assert provider.api_key == kimi_config.api_key
        assert provider.base_url == kimi_config.base_url
    
    @pytest.mark.asyncio
    async def test_qwen_provider_chat_completion(self, qwen_config):
        """Test Qwen provider chat completion."""
        provider = QwenProvider(
            api_key=qwen_config.api_key,
            base_url=qwen_config.base_url
        )

        # Mock the HTTP client
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": "This code looks secure. No issues found.",
                        "role": "assistant"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response

            # Create a test request
            from ai_code_audit.llm.base import LLMModelType
            request = LLMRequest(
                messages=[
                    LLMMessage(MessageRole.SYSTEM, "You are a code security analyst."),
                    LLMMessage(MessageRole.USER, "Analyze this code: SELECT * FROM users WHERE id = ?")
                ],
                model=LLMModelType.QWEN_CODER_30B,
                temperature=0.1
            )

            result = await provider.chat_completion(request)

            assert isinstance(result, LLMResponse)
            assert result.provider_name == "qwen"
            assert result.model_used == LLMModelType.QWEN_CODER_30B
            assert result.content == "This code looks secure. No issues found."
            assert result.usage.total_tokens == 150
            assert result.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_kimi_provider_chat_completion(self, kimi_config):
        """Test Kimi provider chat completion."""
        provider = KimiProvider(
            api_key=kimi_config.api_key,
            base_url=kimi_config.base_url
        )
        
        # Mock the HTTP client
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "issues_found": 1,
                            "security_score": 0.8,
                            "issues": []
                        })
                    }
                }],
                "usage": {
                    "prompt_tokens": 80,
                    "completion_tokens": 30,
                    "total_tokens": 110
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await provider.analyze_code(
                code="print('Hello, World!')",
                file_path="hello.py",
                context={}
            )
            
            assert isinstance(result, LLMResponse)
            assert result.provider_name == "kimi"
            assert result.success
            assert result.token_usage["total_tokens"] == 110
    
    @pytest.mark.asyncio
    async def test_provider_error_handling(self, qwen_config):
        """Test provider error handling."""
        provider = QwenProvider(qwen_config)
        
        # Mock HTTP error
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(LLMError):
                await provider.analyze_code("test code", "test.py", {})
    
    @pytest.mark.asyncio
    async def test_provider_rate_limiting(self, qwen_config):
        """Test provider rate limiting handling."""
        provider = QwenProvider(qwen_config)
        
        # Mock rate limit error
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 429
            mock_response.text = AsyncMock(return_value="Rate limit exceeded")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(LLMError, match="Rate limit"):
                await provider.analyze_code("test code", "test.py", {})


class TestLLMManager:
    """Test LLM manager functionality."""
    
    @pytest.fixture
    def llm_config(self):
        """Fixture providing LLM configuration."""
        return LLMConfig(
            default_model="qwen",
            qwen=QwenConfig(
                api_key="test_qwen_key",
                enabled=True,
                priority=1,
                cost_weight=0.8
            ),
            kimi=KimiConfig(
                api_key="test_kimi_key",
                enabled=True,
                priority=2,
                cost_weight=1.0
            )
        )
    
    @pytest.fixture
    def llm_manager(self, llm_config):
        """Fixture providing LLM manager."""
        return LLMManager(llm_config)
    
    def test_manager_initialization(self, llm_manager, llm_config):
        """Test LLM manager initialization."""
        assert llm_manager.config == llm_config
        assert len(llm_manager.providers) == 2
        assert "qwen" in llm_manager.providers
        assert "kimi" in llm_manager.providers
        assert llm_manager.load_balancing_strategy == LoadBalancingStrategy.PRIORITY
    
    def test_get_available_providers(self, llm_manager):
        """Test getting available providers."""
        providers = llm_manager.get_available_providers()
        
        assert len(providers) == 2
        assert all(provider.is_available() for provider in providers)
    
    def test_select_provider_priority_strategy(self, llm_manager):
        """Test provider selection with priority strategy."""
        llm_manager.load_balancing_strategy = LoadBalancingStrategy.PRIORITY
        
        provider = llm_manager._select_provider()
        
        # Should select Qwen (priority 1, lower is higher priority)
        assert provider.name == "qwen"
    
    def test_select_provider_cost_strategy(self, llm_manager):
        """Test provider selection with cost strategy."""
        llm_manager.load_balancing_strategy = LoadBalancingStrategy.COST
        
        provider = llm_manager._select_provider()
        
        # Should select Qwen (cost_weight 0.8, lower is cheaper)
        assert provider.name == "qwen"
    
    def test_select_provider_round_robin_strategy(self, llm_manager):
        """Test provider selection with round-robin strategy."""
        llm_manager.load_balancing_strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        # First call should return first provider
        provider1 = llm_manager._select_provider()
        provider2 = llm_manager._select_provider()
        
        # Should alternate between providers
        assert provider1.name != provider2.name
    
    @pytest.mark.asyncio
    async def test_analyze_code_success(self, llm_manager):
        """Test successful code analysis."""
        # Mock provider response
        mock_response = LLMResponse(
            content='{"issues_found": 1, "security_score": 0.8}',
            provider_name="qwen",
            model_used="test_model",
            success=True,
            token_usage={"total_tokens": 100},
            response_time=0.5
        )
        
        with patch.object(llm_manager.providers["qwen"], 'analyze_code', return_value=mock_response):
            result = await llm_manager.analyze_code("test code", "test.py", {})
            
            assert result == mock_response
            assert result.success
    
    @pytest.mark.asyncio
    async def test_analyze_code_with_fallback(self, llm_manager):
        """Test code analysis with provider fallback."""
        # Mock first provider failure
        with patch.object(llm_manager.providers["qwen"], 'analyze_code', side_effect=LLMError("Provider failed")):
            # Mock second provider success
            mock_response = LLMResponse(
                content='{"issues_found": 0, "security_score": 1.0}',
                provider_name="kimi",
                model_used="test_model",
                success=True,
                token_usage={"total_tokens": 80},
                response_time=0.3
            )
            
            with patch.object(llm_manager.providers["kimi"], 'analyze_code', return_value=mock_response):
                result = await llm_manager.analyze_code("test code", "test.py", {})
                
                assert result == mock_response
                assert result.provider_name == "kimi"
    
    @pytest.mark.asyncio
    async def test_analyze_code_all_providers_fail(self, llm_manager):
        """Test code analysis when all providers fail."""
        # Mock all providers failing
        for provider in llm_manager.providers.values():
            with patch.object(provider, 'analyze_code', side_effect=LLMError("Provider failed")):
                pass
        
        with pytest.raises(LLMError, match="All LLM providers failed"):
            await llm_manager.analyze_code("test code", "test.py", {})
    
    def test_get_provider_stats(self, llm_manager):
        """Test getting provider statistics."""
        stats = llm_manager.get_provider_stats()
        
        assert "total_providers" in stats
        assert "available_providers" in stats
        assert "providers" in stats
        assert len(stats["providers"]) == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, llm_manager):
        """Test LLM manager health check."""
        # Mock provider health checks
        for provider in llm_manager.providers.values():
            with patch.object(provider, 'health_check', return_value=True):
                pass
        
        health = await llm_manager.health_check()
        
        assert health["healthy"]
        assert health["total_providers"] == 2
        assert health["healthy_providers"] == 2


class TestPromptManagement:
    """Test prompt template management."""
    
    def test_prompt_template_creation(self):
        """Test creating prompt templates."""
        from ai_code_audit.llm.prompts import PromptType

        template = PromptTemplate(
            name="security_analysis",
            type=PromptType.SECURITY_ANALYSIS,
            system_prompt="You are a security analyst.",
            user_prompt_template="Analyze this code for security issues: {code}",
            variables=["code"],
            description="Security analysis template"
        )

        assert template.name == "security_analysis"
        assert "code" in template.variables
        assert template.description is not None
    
    def test_prompt_template_render(self):
        """Test rendering prompt templates through manager."""
        manager = PromptManager()

        # Use existing template
        rendered = manager.generate_prompt(
            "security_audit",
            {
                "language": "python",
                "file_path": "test.py",
                "project_type": "web_app",
                "dependencies": "flask",
                "code_content": "print('hello')",
                "additional_context": "test context"
            }
        )

        assert rendered is not None
        assert "system" in rendered
        assert "user" in rendered
        assert "print('hello')" in rendered["user"]
    
    def test_prompt_template_missing_variable(self):
        """Test prompt template with missing variables."""
        manager = PromptManager()

        # Try to render with missing variables
        rendered = manager.generate_prompt(
            "security_audit",
            {"language": "python"}  # Missing required variables
        )

        # Should return None or handle gracefully
        assert rendered is None
    
    def test_prompt_manager_initialization(self):
        """Test prompt manager initialization."""
        manager = PromptManager()
        
        # Should have default templates
        assert len(manager.templates) > 0
        assert "security_analysis" in manager.templates
        assert "code_review" in manager.templates
    
    def test_prompt_manager_get_template(self):
        """Test getting templates from prompt manager."""
        manager = PromptManager()
        
        template = manager.get_template("security_analysis")
        
        assert template is not None
        assert template.name == "security_analysis"
        assert isinstance(template, PromptTemplate)
    
    def test_prompt_manager_add_template(self):
        """Test adding custom templates."""
        manager = PromptManager()
        
        custom_template = PromptTemplate(
            name="custom_analysis",
            template="Custom analysis for {language}: {code}",
            required_variables=["language", "code"]
        )
        
        manager.add_template(custom_template)
        
        retrieved = manager.get_template("custom_analysis")
        assert retrieved == custom_template
    
    def test_prompt_manager_render_template(self):
        """Test rendering templates through manager."""
        manager = PromptManager()

        rendered = manager.generate_prompt(
            "security_audit",
            {
                "language": "python",
                "file_path": "query.py",
                "project_type": "web_app",
                "dependencies": "none",
                "code_content": "SELECT * FROM users",
                "additional_context": "database query"
            }
        )

        assert rendered is not None
        assert "SELECT * FROM users" in rendered["user"]
        assert "query.py" in rendered["user"]


class TestLLMIntegration:
    """Test integration between LLM components."""
    
    @pytest.fixture
    def integrated_setup(self):
        """Fixture providing integrated LLM setup."""
        config = LLMConfig(
            default_model="qwen",
            qwen=QwenConfig(
                api_key="test_key",
                enabled=True,
                priority=1
            )
        )
        
        manager = LLMManager(config)
        prompt_manager = PromptManager()
        
        return manager, prompt_manager
    
    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self, integrated_setup):
        """Test end-to-end code analysis."""
        llm_manager, prompt_manager = integrated_setup
        
        # Mock LLM response
        mock_response = LLMResponse(
            content='{"issues_found": 1, "security_score": 0.7, "issues": []}',
            provider_name="qwen",
            model_used="test_model",
            success=True,
            token_usage={"total_tokens": 120},
            response_time=0.4
        )
        
        with patch.object(llm_manager.providers["qwen"], 'analyze_code', return_value=mock_response):
            # Render prompt
            prompt = prompt_manager.render_template(
                "security_analysis",
                code="print('Hello, World!')",
                file_path="hello.py",
                language="python"
            )
            
            # Analyze code
            result = await llm_manager.analyze_code(
                code="print('Hello, World!')",
                file_path="hello.py",
                context={"prompt": prompt}
            )
            
            assert result.success
            assert result.provider_name == "qwen"
            assert "issues_found" in result.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
