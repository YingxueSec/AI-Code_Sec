#!/usr/bin/env python3
"""
API key validation script.

This script tests the API keys to ensure they work correctly.
"""

import asyncio
import sys
import aiohttp
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_api_key(api_key: str, model_name: str, provider_name: str):
    """Test a specific API key with a model."""
    print(f"\n🔍 Testing {provider_name} API key...")
    print(f"   Model: {model_name}")
    print(f"   API Key: {'*' * 20 + api_key[-8:]}")
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello, test message"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    tokens = data.get('usage', {}).get('total_tokens', 0)
                    print(f"✅ {provider_name} API key works!")
                    print(f"   Response: {content[:50]}...")
                    print(f"   Tokens used: {tokens}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ {provider_name} API key failed!")
                    print(f"   Status: {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ {provider_name} API test failed: {e}")
        return False


async def test_configuration_keys():
    """Test API keys from configuration."""
    print("🔍 Testing API keys from configuration...")
    
    try:
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        
        results = []
        
        # Test Qwen key
        if config.llm.qwen and config.llm.qwen.api_key:
            result = await test_api_key(
                config.llm.qwen.api_key,
                "Qwen/Qwen3-Coder-30B-A3B-Instruct",
                "Qwen"
            )
            results.append(("Qwen", result))
        else:
            print("❌ Qwen configuration not found")
            results.append(("Qwen", False))
        
        # Test Kimi key
        if config.llm.kimi and config.llm.kimi.api_key:
            result = await test_api_key(
                config.llm.kimi.api_key,
                "moonshotai/Kimi-K2-Instruct",
                "Kimi"
            )
            results.append(("Kimi", result))
        else:
            print("❌ Kimi configuration not found")
            results.append(("Kimi", False))
        
        return results
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return []


async def test_environment_keys():
    """Test API keys from environment variables."""
    print("\n🔍 Testing API keys from environment variables...")
    
    import os
    
    results = []
    
    # Test Qwen key from environment
    qwen_key = os.getenv('QWEN_API_KEY')
    if qwen_key:
        result = await test_api_key(
            qwen_key,
            "Qwen/Qwen3-Coder-30B-A3B-Instruct",
            "Qwen (env)"
        )
        results.append(("Qwen (env)", result))
    else:
        print("⚠️  QWEN_API_KEY environment variable not set")
        results.append(("Qwen (env)", False))
    
    # Test Kimi key from environment
    kimi_key = os.getenv('KIMI_API_KEY')
    if kimi_key:
        result = await test_api_key(
            kimi_key,
            "moonshotai/Kimi-K2-Instruct",
            "Kimi (env)"
        )
        results.append(("Kimi (env)", result))
    else:
        print("⚠️  KIMI_API_KEY environment variable not set")
        results.append(("Kimi (env)", False))
    
    return results


async def test_hardcoded_keys():
    """Test the specific API keys you provided."""
    print("\n🔍 Testing hardcoded API keys...")
    
    # Your provided keys
    qwen_key = "sk-bldkmthquuuypfythtasqvdhwtclplekygnbylvboctetkeh"
    kimi_key = "sk-kpepqjjtmxpcdhqcvrdekuroxvmpmphkfouhzbcbudbpzzzt"
    
    results = []
    
    # Test Qwen key
    result = await test_api_key(
        qwen_key,
        "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "Qwen (hardcoded)"
    )
    results.append(("Qwen (hardcoded)", result))
    
    # Test Kimi key
    result = await test_api_key(
        kimi_key,
        "moonshotai/Kimi-K2-Instruct",
        "Kimi (hardcoded)"
    )
    results.append(("Kimi (hardcoded)", result))
    
    return results


async def test_provider_validation():
    """Test provider validation through LLM manager."""
    print("\n🔍 Testing provider validation through LLM manager...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        
        manager = LLMManager()
        
        print(f"✅ LLM manager initialized with {len(manager.providers)} providers")
        
        # Test provider validation
        validation_results = await manager.validate_providers()
        
        results = []
        for provider, is_valid in validation_results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {provider}: {status}")
            results.append((provider, is_valid))
        
        await manager.close()
        
        return results
        
    except Exception as e:
        print(f"❌ Provider validation failed: {e}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """Run all API key tests."""
    print("🚀 API Key Validation Test")
    print("=" * 50)
    
    all_results = []
    
    # Test configuration keys
    config_results = await test_configuration_keys()
    all_results.extend(config_results)
    
    # Test environment keys
    env_results = await test_environment_keys()
    all_results.extend(env_results)
    
    # Test hardcoded keys
    hardcoded_results = await test_hardcoded_keys()
    all_results.extend(hardcoded_results)
    
    # Test provider validation
    provider_results = await test_provider_validation()
    all_results.extend(provider_results)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 API Key Test Summary")
    print("-" * 30)
    
    valid_count = 0
    total_count = 0
    
    for name, is_valid in all_results:
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{name}: {status}")
        if is_valid:
            valid_count += 1
        total_count += 1
    
    print(f"\nResult: {valid_count}/{total_count} tests passed")
    
    if valid_count > 0:
        print("\n🎉 At least some API keys are working!")
        print("You can proceed with using the system.")
    else:
        print("\n⚠️  No API keys are working.")
        print("Please check:")
        print("  1. API key validity")
        print("  2. Account balance/credits")
        print("  3. Model availability on SiliconFlow")
        print("  4. Network connectivity")
    
    return 0 if valid_count > 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
