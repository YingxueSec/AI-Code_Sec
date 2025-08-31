#!/usr/bin/env python3
"""
Test script for corrected model configurations.

This script tests the corrected model names and API configurations
for both Qwen and Kimi models through SiliconFlow.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_model_configurations():
    """Test corrected model configurations."""
    print("🔍 Testing corrected model configurations...")
    
    try:
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.kimi_provider import KimiProvider
        
        print("✅ Model types loaded successfully")
        
        # Test Qwen models
        print("\n📋 Qwen Models:")
        qwen_models = [
            LLMModelType.QWEN_TURBO,
            LLMModelType.QWEN_PLUS,
            LLMModelType.QWEN_MAX,
            LLMModelType.QWEN_CODER,
        ]
        
        for model in qwen_models:
            print(f"  {model.name}: {model.value}")
        
        # Test Kimi models
        print("\n📋 Kimi Models:")
        kimi_models = [
            LLMModelType.KIMI_8K,
            LLMModelType.KIMI_32K,
            LLMModelType.KIMI_128K,
        ]
        
        for model in kimi_models:
            print(f"  {model.name}: {model.value}")
        
        # Test provider initialization
        qwen_provider = QwenProvider(api_key="test-key")
        kimi_provider = KimiProvider(api_key="test-key")
        
        print(f"\n✅ Qwen provider base URL: {qwen_provider.base_url}")
        print(f"✅ Kimi provider base URL: {kimi_provider.base_url}")
        
        # Verify both use SiliconFlow
        if qwen_provider.base_url == kimi_provider.base_url:
            print("✅ Both providers correctly use SiliconFlow API")
        else:
            print("❌ Providers use different APIs")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Model configuration test failed: {e}")
        return False


async def test_configuration_loading():
    """Test configuration loading with corrected settings."""
    print("\n🔍 Testing configuration loading...")
    
    try:
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        
        print("✅ Configuration loaded successfully")
        
        # Test Qwen configuration
        if config.llm.qwen:
            print(f"✅ Qwen API Key: {'*' * 20 + config.llm.qwen.api_key[-8:]}")
            print(f"✅ Qwen Base URL: {config.llm.qwen.base_url}")
        
        # Test Kimi configuration
        if config.llm.kimi:
            print(f"✅ Kimi API Key: {'*' * 20 + config.llm.kimi.api_key[-8:]}")
            print(f"✅ Kimi Base URL: {config.llm.kimi.base_url}")
        
        # Verify both use SiliconFlow
        if (config.llm.qwen and config.llm.kimi and 
            config.llm.qwen.base_url == config.llm.kimi.base_url):
            print("✅ Both providers correctly configured for SiliconFlow")
        else:
            print("⚠️  Providers may use different APIs")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False


async def test_llm_manager():
    """Test LLM manager with corrected configurations."""
    print("\n🔍 Testing LLM manager...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        
        manager = LLMManager()
        
        print(f"✅ LLM manager initialized with {len(manager.providers)} providers")
        
        # Test available models
        models = manager.get_available_models()
        
        for provider_name, provider_models in models.items():
            print(f"\n📋 {provider_name.upper()} Provider Models:")
            for model in provider_models:
                print(f"  {model.name}: {model.value}")
        
        # Test provider validation
        validation_results = await manager.validate_providers()
        
        print(f"\n🔍 Provider Validation Results:")
        for provider, is_valid in validation_results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"  {provider}: {status}")
        
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ LLM manager test failed: {e}")
        return False


async def test_api_request_preparation():
    """Test API request preparation with correct model names."""
    print("\n🔍 Testing API request preparation...")
    
    try:
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.kimi_provider import KimiProvider
        
        # Test Qwen request preparation
        qwen_provider = QwenProvider(api_key="test-key")
        
        qwen_request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Hello")],
            model=LLMModelType.QWEN_TURBO
        )
        
        qwen_api_request = qwen_provider._prepare_api_request(qwen_request)
        print(f"✅ Qwen API request model: {qwen_api_request['model']}")
        
        # Test Kimi request preparation
        kimi_provider = KimiProvider(api_key="test-key")
        
        kimi_request = LLMRequest(
            messages=[LLMMessage(MessageRole.USER, "Hello")],
            model=LLMModelType.KIMI_8K
        )
        
        kimi_api_request = kimi_provider._prepare_api_request(kimi_request)
        print(f"✅ Kimi API request model: {kimi_api_request['model']}")
        
        # Verify model names are correct
        expected_qwen_model = "Qwen/Qwen2.5-7B-Instruct"
        expected_kimi_model = "moonshot-v1-8k"
        
        if qwen_api_request['model'] == expected_qwen_model:
            print("✅ Qwen model name is correct")
        else:
            print(f"❌ Qwen model name incorrect: expected {expected_qwen_model}, got {qwen_api_request['model']}")
            return False
        
        if kimi_api_request['model'] == expected_kimi_model:
            print("✅ Kimi model name is correct")
        else:
            print(f"❌ Kimi model name incorrect: expected {expected_kimi_model}, got {kimi_api_request['model']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API request preparation test failed: {e}")
        return False


async def test_cli_model_options():
    """Test CLI model options."""
    print("\n🔍 Testing CLI model options...")
    
    try:
        import subprocess
        
        # Test audit command help
        result = subprocess.run([
            sys.executable, '-m', 'ai_code_audit.cli.main', 'audit', '--help'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ CLI audit command help works")
            
            # Check if new model options are available
            help_output = result.stdout
            if 'qwen-coder' in help_output:
                print("✅ qwen-coder model option available")
            else:
                print("❌ qwen-coder model option missing")
                return False
            
            if 'kimi-8k' in help_output:
                print("✅ kimi model options available")
            else:
                print("❌ kimi model options missing")
                return False
        else:
            print(f"❌ CLI help command failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI model options test failed: {e}")
        return False


async def main():
    """Run all corrected model tests."""
    print("🚀 AI Code Audit System - Corrected Model Configuration Test")
    print("=" * 70)
    
    tests = [
        ("Model Configurations", test_model_configurations),
        ("Configuration Loading", test_configuration_loading),
        ("LLM Manager", test_llm_manager),
        ("API Request Preparation", test_api_request_preparation),
        ("CLI Model Options", test_cli_model_options),
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
    print(f"📊 Corrected Model Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All model configuration corrections verified!")
        print("\n📝 Corrected configurations:")
        print("   • Both Qwen and Kimi use SiliconFlow API: https://api.siliconflow.cn/v1")
        print("   • Qwen models: Qwen/Qwen2.5-7B-Instruct, etc.")
        print("   • Kimi models: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k")
        print("   • Added qwen-coder model option")
        print("\n🔧 Ready to test with real API:")
        print("   # Use the simplified audit function:")
        print("   import asyncio")
        print("   from ai_code_audit import audit_project")
        print("   asyncio.run(audit_project('.', max_files=1))")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
