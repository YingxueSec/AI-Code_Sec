#!/usr/bin/env python3
"""
Test script for simplified model configuration.

This script tests the simplified configuration with only two models:
- Qwen/Qwen3-Coder-30B-A3B-Instruct
- moonshotai/Kimi-K2-Instruct
Both through SiliconFlow API.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_simplified_configuration():
    """Test simplified model configuration."""
    print("🔍 Testing simplified model configuration...")
    
    try:
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.core.config import get_config
        
        # Test model types
        print("\n📋 Available Models:")
        print(f"  QWEN_CODER_30B: {LLMModelType.QWEN_CODER_30B.value}")
        print(f"  KIMI_K2: {LLMModelType.KIMI_K2.value}")
        
        # Test configuration
        config = get_config()
        print(f"\n✅ Default model: {config.llm.default_model}")
        
        if config.llm.qwen:
            print(f"✅ Qwen configured: {config.llm.qwen.base_url}")
            print(f"   API Key: {'*' * 20 + config.llm.qwen.api_key[-8:]}")
        
        if config.llm.kimi:
            print(f"✅ Kimi configured: {config.llm.kimi.base_url}")
            print(f"   API Key: {'*' * 20 + config.llm.kimi.api_key[-8:]}")
        
        # Verify both use SiliconFlow
        if (config.llm.qwen and config.llm.kimi and 
            config.llm.qwen.base_url == config.llm.kimi.base_url == "https://api.siliconflow.cn/v1"):
            print("✅ Both providers use SiliconFlow API")
        else:
            print("❌ API providers mismatch")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_providers():
    """Test both providers."""
    print("\n🔍 Testing providers...")
    
    try:
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.kimi_provider import KimiProvider
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        
        # Test Qwen provider
        qwen_provider = QwenProvider(
            api_key=config.llm.qwen.api_key,
            base_url=config.llm.qwen.base_url
        )
        
        print(f"✅ Qwen provider initialized")
        print(f"   Supported models: {len(qwen_provider.supported_models)}")
        for model in qwen_provider.supported_models:
            context = qwen_provider.get_max_context_length(model)
            print(f"   - {model.name}: {context} tokens")
        
        # Test Kimi provider
        kimi_provider = KimiProvider(
            api_key=config.llm.kimi.api_key,
            base_url=config.llm.kimi.base_url
        )
        
        print(f"✅ Kimi provider initialized")
        print(f"   Supported models: {len(kimi_provider.supported_models)}")
        for model in kimi_provider.supported_models:
            context = kimi_provider.get_max_context_length(model)
            print(f"   - {model.name}: {context} tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False


async def test_llm_manager():
    """Test LLM manager with simplified models."""
    print("\n🔍 Testing LLM manager...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        
        manager = LLMManager()
        
        print(f"✅ LLM manager initialized with {len(manager.providers)} providers")
        
        # Test available models
        models = manager.get_available_models()
        
        for provider_name, provider_models in models.items():
            print(f"\n📋 {provider_name.upper()} Provider:")
            for model in provider_models:
                print(f"   {model.name}: {model.value}")
        
        # Test provider validation
        validation_results = await manager.validate_providers()
        
        print(f"\n🔍 Provider Validation:")
        for provider, is_valid in validation_results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {provider}: {status}")
        
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ LLM manager test failed: {e}")
        return False


async def test_api_calls():
    """Test actual API calls for both models."""
    print("\n🔍 Testing API calls...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        
        manager = LLMManager()
        
        # Test Qwen model
        print("\n📤 Testing Qwen Coder 30B...")
        qwen_request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Write a simple Python hello world function")],
            model=LLMModelType.QWEN_CODER_30B,
            temperature=0.1,
            max_tokens=100
        )
        
        qwen_response = await manager.chat_completion(qwen_request)
        print(f"✅ Qwen response: {qwen_response.content[:80]}...")
        print(f"   Tokens used: {qwen_response.usage.total_tokens if qwen_response.usage else 'Unknown'}")
        
        # Test Kimi model
        print("\n📤 Testing Kimi K2...")
        kimi_request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Explain what is code review in one sentence")],
            model=LLMModelType.KIMI_K2,
            temperature=0.1,
            max_tokens=100
        )
        
        kimi_response = await manager.chat_completion(kimi_request)
        print(f"✅ Kimi response: {kimi_response.content[:80]}...")
        print(f"   Tokens used: {kimi_response.usage.total_tokens if kimi_response.usage else 'Unknown'}")
        
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ API call test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cli_options():
    """Test CLI options."""
    print("\n🔍 Testing CLI options...")
    
    try:
        import subprocess
        
        # Test audit command help
        result = subprocess.run([
            sys.executable, '-m', 'ai_code_audit.cli.main', 'audit', '--help'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            help_output = result.stdout
            
            # Check for simplified model options
            if 'qwen-coder-30b' in help_output and 'kimi-k2' in help_output:
                print("✅ Simplified model options available")
            else:
                print("❌ Model options not found")
                return False
            
            # Check that old options are removed
            old_options = ['qwen-turbo', 'qwen-plus', 'kimi-8k', 'kimi-32k']
            found_old = any(opt in help_output for opt in old_options)
            
            if not found_old:
                print("✅ Old model options removed")
            else:
                print("⚠️  Some old model options still present")
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


async def main():
    """Run all simplified model tests."""
    print("🚀 AI Code Audit System - Simplified Model Configuration Test")
    print("=" * 70)
    print("Testing configuration with only two models:")
    print("  • Qwen/Qwen3-Coder-30B-A3B-Instruct (SiliconFlow)")
    print("  • moonshotai/Kimi-K2-Instruct (SiliconFlow)")
    print("=" * 70)
    
    tests = [
        ("Configuration Loading", test_simplified_configuration),
        ("Provider Initialization", test_providers),
        ("LLM Manager", test_llm_manager),
        ("API Calls", test_api_calls),
        ("CLI Options", test_cli_options),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Simplified Model Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Simplified configuration is ready.")
        print("\n🔧 Available commands:")
        print("   python -m ai_code_audit.cli.main config")
        print("   python -m ai_code_audit.cli.main audit . --model qwen-coder-30b")
        print("   python -m ai_code_audit.cli.main audit . --model kimi-k2")
        print("   python -m ai_code_audit.cli.main audit . --template code_review")
        print("   python -m ai_code_audit.cli.main audit . --template vulnerability_scan")
        print("\n📊 Model Comparison:")
        print("   • qwen-coder-30b: 32K context, optimized for code analysis")
        print("   • kimi-k2: 128K context, excellent for large files and Chinese")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
