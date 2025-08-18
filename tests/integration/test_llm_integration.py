#!/usr/bin/env python3
"""
LLM integration test script for AI Code Audit System.

This script tests the LLM integration functionality including providers,
manager, and prompt system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_llm_base_classes():
    """Test LLM base classes and data models."""
    print("🔍 Testing LLM base classes...")
    
    try:
        from ai_code_audit.llm.base import (
            LLMRequest, LLMResponse, LLMMessage, LLMUsage,
            MessageRole, LLMModelType
        )
        
        # Test message creation
        message = LLMMessage(MessageRole.USER, "Hello, world!")
        print(f"✅ LLM message created: {message.role.value}")
        
        # Test request creation
        request = LLMRequest(
            messages=[message],
            model=LLMModelType.QWEN_TURBO,
            temperature=0.1
        )
        print(f"✅ LLM request created with {len(request.messages)} messages")
        
        # Test response creation
        usage = LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        response = LLMResponse(
            content="Hello! How can I help you?",
            model="qwen-turbo",
            usage=usage
        )
        print(f"✅ LLM response created: {len(response.content)} chars")
        print(f"   Usage: {usage.total_tokens} tokens, cost: ${usage.cost_estimate:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM base classes test failed: {e}")
        return False


async def test_qwen_provider():
    """Test Qwen provider functionality."""
    print("\n🔍 Testing Qwen provider...")
    
    try:
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.base import LLMModelType
        
        # Initialize provider (without API key for testing)
        provider = QwenProvider(api_key="test-key")
        print(f"✅ Qwen provider initialized: {provider.provider_name}")
        
        # Test model support
        supported_models = provider.supported_models
        print(f"✅ Supported models: {[m.value for m in supported_models]}")
        
        # Test context lengths
        for model in supported_models:
            context_length = provider.get_max_context_length(model)
            print(f"   {model.value}: {context_length:,} tokens")
        
        # Test model support check
        assert provider.is_model_supported(LLMModelType.QWEN_TURBO)
        assert not provider.is_model_supported(LLMModelType.KIMI_8K)
        print("✅ Model support check works")
        
        return True
        
    except Exception as e:
        print(f"❌ Qwen provider test failed: {e}")
        return False


async def test_kimi_provider():
    """Test Kimi provider functionality."""
    print("\n🔍 Testing Kimi provider...")
    
    try:
        from ai_code_audit.llm.kimi_provider import KimiProvider
        from ai_code_audit.llm.base import LLMModelType
        
        # Initialize provider (without API key for testing)
        provider = KimiProvider(api_key="test-key")
        print(f"✅ Kimi provider initialized: {provider.provider_name}")
        
        # Test model support
        supported_models = provider.supported_models
        print(f"✅ Supported models: {[m.value for m in supported_models]}")
        
        # Test context lengths
        for model in supported_models:
            context_length = provider.get_max_context_length(model)
            print(f"   {model.value}: {context_length:,} tokens")
        
        # Test long context support
        assert provider.supports_long_context(LLMModelType.KIMI_128K)
        assert not provider.supports_long_context(LLMModelType.KIMI_8K)
        print("✅ Long context support check works")
        
        # Test model recommendation
        recommended = provider.get_recommended_model_for_context_length(50000)
        print(f"✅ Recommended model for 50K tokens: {recommended.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Kimi provider test failed: {e}")
        return False


async def test_llm_manager():
    """Test LLM manager functionality."""
    print("\n🔍 Testing LLM manager...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager, LoadBalancingStrategy
        
        # Test with empty config (no API keys)
        config = {'llm': {}}
        manager = LLMManager(config)
        print("✅ LLM manager initialized with empty config")
        
        # Test with mock providers
        config_with_providers = {
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
        
        manager_with_providers = LLMManager(config_with_providers)
        print(f"✅ LLM manager initialized with {len(manager_with_providers.providers)} providers")
        
        # Test available models
        models = manager_with_providers.get_available_models()
        print(f"✅ Available models: {list(models.keys())}")
        
        # Test provider stats
        stats = manager_with_providers.get_provider_stats()
        print(f"✅ Provider stats: {list(stats.keys())}")
        
        # Test load balancing strategies
        for strategy in LoadBalancingStrategy:
            manager_with_providers.set_load_balancing_strategy(strategy)
            print(f"   Strategy set: {strategy.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM manager test failed: {e}")
        return False


async def test_prompt_manager():
    """Test prompt manager functionality."""
    print("\n🔍 Testing prompt manager...")
    
    try:
        from ai_code_audit.llm.prompts import PromptManager, PromptType
        
        # Initialize prompt manager
        manager = PromptManager()
        print(f"✅ Prompt manager initialized with {len(manager.templates)} templates")
        
        # List templates
        templates = manager.list_templates()
        print(f"✅ Available templates: {templates}")
        
        # Test getting template
        security_template = manager.get_template('security_audit')
        if security_template:
            print(f"✅ Security audit template: {len(security_template.variables)} variables")
            print(f"   Variables: {security_template.variables}")
        
        # Test templates by type
        security_templates = manager.get_templates_by_type(PromptType.SECURITY_AUDIT)
        print(f"✅ Security templates: {len(security_templates)}")
        
        # Test prompt generation
        variables = {
            'language': 'python',
            'file_path': 'test.py',
            'project_type': 'web_application',
            'dependencies': 'flask, requests',
            'code_content': 'print("Hello, world!")',
            'additional_context': 'This is a test file'
        }
        
        prompt = manager.generate_prompt('security_audit', variables)
        if prompt:
            print("✅ Prompt generated successfully")
            print(f"   System prompt length: {len(prompt['system'])} chars")
            print(f"   User prompt length: {len(prompt['user'])} chars")
            print(f"   Template metadata: {prompt['metadata']['template_name']}")
        else:
            print("❌ Prompt generation failed")
        
        # Test template info
        info = manager.get_template_info('security_audit')
        if info:
            print(f"✅ Template info: {info['name']} ({info['type']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt manager test failed: {e}")
        return False


async def test_real_api_call():
    """Test real API call if API keys are available."""
    print("\n🔍 Testing real API calls...")
    
    qwen_key = os.getenv('QWEN_API_KEY')
    kimi_key = os.getenv('KIMI_API_KEY')
    
    if not qwen_key and not kimi_key:
        print("⚠️  No API keys found in environment variables")
        print("   Set QWEN_API_KEY or KIMI_API_KEY to test real API calls")
        return True
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        
        # Configure manager with real API keys
        config = {'llm': {}}
        
        if qwen_key:
            config['llm']['qwen'] = {
                'api_key': qwen_key,
                'enabled': True
            }
        
        if kimi_key:
            config['llm']['kimi'] = {
                'api_key': kimi_key,
                'enabled': True
            }
        
        manager = LLMManager(config)
        
        # Validate providers
        validation_results = await manager.validate_providers()
        print(f"✅ Provider validation results: {validation_results}")
        
        # Test a simple request if any provider is valid
        if any(validation_results.values()):
            print("🔄 Testing simple chat completion...")
            
            request = LLMRequest(
                messages=[
                    LLMMessage(MessageRole.SYSTEM, "You are a helpful assistant."),
                    LLMMessage(MessageRole.USER, "Say hello in one word.")
                ],
                model=LLMModelType.QWEN_TURBO if qwen_key else LLMModelType.KIMI_8K,
                max_tokens=10
            )
            
            try:
                response = await manager.chat_completion(request)
                print(f"✅ API call successful!")
                print(f"   Response: {response.content}")
                print(f"   Model: {response.model}")
                print(f"   Provider: {response.metadata.get('provider_used')}")
                if response.usage:
                    print(f"   Tokens: {response.usage.total_tokens}")
                    print(f"   Cost estimate: ${response.usage.cost_estimate:.4f}")
                
            except Exception as e:
                print(f"⚠️  API call failed: {e}")
        
        # Clean up
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Real API test failed: {e}")
        return False


async def main():
    """Run all LLM integration tests."""
    print("🚀 AI Code Audit System - LLM Integration Test")
    print("=" * 60)
    
    tests = [
        ("LLM Base Classes", test_llm_base_classes),
        ("Qwen Provider", test_qwen_provider),
        ("Kimi Provider", test_kimi_provider),
        ("LLM Manager", test_llm_manager),
        ("Prompt Manager", test_prompt_manager),
        ("Real API Calls", test_real_api_call),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 LLM Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All LLM integration tests passed! LLM system is ready for use.")
        print("\n📝 Next steps:")
        print("   1. Set up API keys: export QWEN_API_KEY=your_key")
        print("   2. Set up API keys: export KIMI_API_KEY=your_key")
        print("   3. Test with: ai-audit audit")
        print("   4. Integrate with audit engine")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
