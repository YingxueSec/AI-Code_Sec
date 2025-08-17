#!/usr/bin/env python3
"""
Debug script for Kimi provider issues.

This script helps diagnose and fix Kimi model API call problems.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_kimi_configuration():
    """Test Kimi configuration loading."""
    print("🔍 Testing Kimi configuration...")
    
    try:
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        
        if config.llm.kimi:
            print("✅ Kimi configuration found")
            print(f"   API Key: {'*' * 20 + config.llm.kimi.api_key[-8:]}")
            print(f"   Base URL: {config.llm.kimi.base_url}")
            print(f"   Enabled: {config.llm.kimi.enabled}")
            print(f"   Priority: {config.llm.kimi.priority}")
            return config.llm.kimi
        else:
            print("❌ Kimi configuration not found")
            return None
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return None


async def test_kimi_provider_initialization():
    """Test Kimi provider initialization."""
    print("\n🔍 Testing Kimi provider initialization...")
    
    try:
        from ai_code_audit.llm.kimi_provider import KimiProvider
        from ai_code_audit.llm.base import LLMModelType
        
        # Get configuration
        config = await test_kimi_configuration()
        if not config:
            return None
        
        # Initialize provider
        provider = KimiProvider(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
        print("✅ Kimi provider initialized")
        print(f"   Base URL: {provider.base_url}")
        print(f"   Supported models: {len(provider.supported_models)}")
        
        for model in provider.supported_models:
            context_length = provider.get_max_context_length(model)
            print(f"   - {model.name}: {model.value} (context: {context_length})")
        
        return provider
        
    except Exception as e:
        print(f"❌ Provider initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_kimi_api_request():
    """Test Kimi API request preparation."""
    print("\n🔍 Testing Kimi API request preparation...")
    
    try:
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        
        provider = await test_kimi_provider_initialization()
        if not provider:
            return False
        
        # Test with KIMI_K2 model
        request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, "You are a helpful assistant."),
                LLMMessage(MessageRole.USER, "Hello, can you help me?")
            ],
            model=LLMModelType.KIMI_K2,
            temperature=0.1,
            max_tokens=100
        )
        
        # Prepare API request
        api_request = provider._prepare_api_request(request)
        
        print("✅ API request prepared successfully")
        print(f"   Model: {api_request.get('model')}")
        print(f"   Messages: {len(api_request.get('messages', []))}")
        print(f"   Temperature: {api_request.get('temperature')}")
        print(f"   Max tokens: {api_request.get('max_tokens')}")
        
        # Validate model name
        expected_model = "moonshotai/Kimi-K2-Instruct"
        if api_request.get('model') == expected_model:
            print("✅ Model name is correct")
        else:
            print(f"❌ Model name incorrect: expected {expected_model}, got {api_request.get('model')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API request preparation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_kimi_api_call():
    """Test actual Kimi API call."""
    print("\n🔍 Testing actual Kimi API call...")
    
    try:
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        
        provider = await test_kimi_provider_initialization()
        if not provider:
            return False
        
        # Create a simple test request
        request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.USER, "Say 'Hello World' in Python")
            ],
            model=LLMModelType.KIMI_K2,
            temperature=0.1,
            max_tokens=50
        )
        
        print("📤 Sending API request...")
        print(f"   Model: {request.model.value}")
        print(f"   Message: {request.messages[0].content}")
        
        # Make API call
        response = await provider.chat_completion(request)
        
        print("✅ API call successful!")
        print(f"   Response: {response.content[:100]}...")
        print(f"   Tokens used: {response.usage.total_tokens if response.usage else 'Unknown'}")
        print(f"   Provider: {response.metadata.get('provider_used', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        
        # Try to get more detailed error information
        if hasattr(e, 'response'):
            print(f"   HTTP Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'Unknown'}")
            try:
                error_data = e.response.json() if hasattr(e.response, 'json') else str(e.response)
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw response: {str(e.response)}")
        
        import traceback
        traceback.print_exc()
        return False


async def test_kimi_with_different_models():
    """Test Kimi with different model variants."""
    print("\n🔍 Testing different Kimi models...")
    
    try:
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        
        provider = await test_kimi_provider_initialization()
        if not provider:
            return False
        
        # Test different models
        models_to_test = [
            LLMModelType.KIMI_K2,
            LLMModelType.KIMI_8K,
        ]
        
        for model in models_to_test:
            print(f"\n📋 Testing model: {model.name} ({model.value})")
            
            try:
                request = LLMRequest(
                    messages=[LLMMessage(MessageRole.USER, "Hello")],
                    model=model,
                    temperature=0.1,
                    max_tokens=20
                )
                
                response = await provider.chat_completion(request)
                print(f"   ✅ Success: {response.content[:50]}...")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model testing failed: {e}")
        return False


async def test_llm_manager_with_kimi():
    """Test LLM manager with Kimi provider."""
    print("\n🔍 Testing LLM manager with Kimi...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        from ai_code_audit.llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
        
        manager = LLMManager()
        
        print(f"✅ LLM manager initialized with {len(manager.providers)} providers")
        
        # Check if Kimi provider is available
        if 'kimi' in manager.providers:
            print("✅ Kimi provider found in manager")
        else:
            print("❌ Kimi provider not found in manager")
            return False
        
        # Test provider validation
        validation_results = await manager.validate_providers()
        kimi_valid = validation_results.get('kimi', False)
        
        print(f"🔍 Kimi provider validation: {'✅ Valid' if kimi_valid else '❌ Invalid'}")
        
        if kimi_valid:
            # Test actual request through manager
            request = LLMRequest(
                messages=[LLMMessage(MessageRole.USER, "Test message")],
                model=LLMModelType.KIMI_K2,
                temperature=0.1,
                max_tokens=30
            )
            
            response = await manager.chat_completion(request)
            print(f"✅ Manager request successful: {response.content[:50]}...")
        
        await manager.close()
        return True
        
    except Exception as e:
        print(f"❌ LLM manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cli_with_kimi():
    """Test CLI with Kimi model."""
    print("\n🔍 Testing CLI with Kimi model...")
    
    try:
        import subprocess
        
        # Test CLI help to see if kimi-k2 is available
        result = subprocess.run([
            sys.executable, '-m', 'ai_code_audit.cli.main', 'audit', '--help'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            help_output = result.stdout
            if 'kimi-k2' in help_output:
                print("✅ kimi-k2 model option available in CLI")
            else:
                print("❌ kimi-k2 model option not found in CLI")
                return False
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


async def main():
    """Run all Kimi debugging tests."""
    print("🚀 Kimi Provider Debug Analysis")
    print("=" * 50)
    
    tests = [
        ("Configuration Loading", test_kimi_configuration),
        ("Provider Initialization", test_kimi_provider_initialization),
        ("API Request Preparation", test_kimi_api_request),
        ("Actual API Call", test_kimi_api_call),
        ("Different Models", test_kimi_with_different_models),
        ("LLM Manager Integration", test_llm_manager_with_kimi),
        ("CLI Integration", test_cli_with_kimi),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Kimi Debug Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Kimi tests passed! Provider should work correctly.")
        print("\n🔧 Try running:")
        print("   python -m ai_code_audit.cli.main audit . --max-files 1 --model kimi-k2")
    else:
        print("⚠️  Some tests failed. Issues identified:")
        print("   1. Check API key validity")
        print("   2. Verify model names")
        print("   3. Check network connectivity")
        print("   4. Review SiliconFlow API documentation")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
