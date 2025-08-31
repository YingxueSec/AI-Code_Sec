#!/usr/bin/env python3
"""
Context length fix verification script.

This script verifies that the Qwen3-Coder-30B-A3B-Instruct model
context length has been correctly updated to 256K tokens (262,144).
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_qwen_context_length():
    """Test Qwen provider context length configuration."""
    print("🔍 Testing Qwen provider context length...")
    
    try:
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        provider = QwenProvider(
            api_key=config.llm.qwen.api_key,
            base_url=config.llm.qwen.base_url
        )
        
        # Test context length
        context_length = provider.get_max_context_length(LLMModelType.QWEN_CODER_30B)
        expected_length = 262144  # 256K tokens
        
        print(f"✅ Qwen Coder 30B context length: {context_length:,} tokens")
        
        if context_length == expected_length:
            print(f"✅ Context length is correct: {context_length:,} tokens (256K)")
            return True
        else:
            print(f"❌ Context length incorrect: expected {expected_length:,}, got {context_length:,}")
            return False
            
    except Exception as e:
        print(f"❌ Qwen context length test failed: {e}")
        return False


def test_kimi_context_length():
    """Test Kimi provider context length configuration."""
    print("\n🔍 Testing Kimi provider context length...")
    
    try:
        from ai_code_audit.llm.kimi_provider import KimiProvider
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        provider = KimiProvider(
            api_key=config.llm.kimi.api_key,
            base_url=config.llm.kimi.base_url
        )
        
        # Test context length
        context_length = provider.get_max_context_length(LLMModelType.KIMI_K2)
        expected_length = 128000  # 128K tokens
        
        print(f"✅ Kimi K2 context length: {context_length:,} tokens")
        
        if context_length == expected_length:
            print(f"✅ Context length is correct: {context_length:,} tokens (128K)")
            return True
        else:
            print(f"❌ Context length incorrect: expected {expected_length:,}, got {context_length:,}")
            return False
            
    except Exception as e:
        print(f"❌ Kimi context length test failed: {e}")
        return False


def test_base_class_context_length():
    """Test base class default context lengths."""
    print("\n🔍 Testing base class default context lengths...")
    
    try:
        from ai_code_audit.llm.base import BaseLLMProvider, LLMModelType
        
        # Create a dummy provider to test base class
        class TestProvider(BaseLLMProvider):
            def __init__(self):
                super().__init__("test-key", "test-url")

            @property
            def provider_name(self):
                return "test"

            @property
            def supported_models(self):
                return [LLMModelType.QWEN_CODER_30B, LLMModelType.KIMI_K2]

            async def chat_completion(self, request):
                pass

            async def validate_api_key(self):
                return True
        
        provider = TestProvider()
        
        # Test Qwen context length
        qwen_length = provider.get_max_context_length(LLMModelType.QWEN_CODER_30B)
        expected_qwen = 262144
        
        print(f"✅ Base class Qwen context length: {qwen_length:,} tokens")
        
        # Test Kimi context length
        kimi_length = provider.get_max_context_length(LLMModelType.KIMI_K2)
        expected_kimi = 128000
        
        print(f"✅ Base class Kimi context length: {kimi_length:,} tokens")
        
        success = True
        if qwen_length != expected_qwen:
            print(f"❌ Base class Qwen length incorrect: expected {expected_qwen:,}, got {qwen_length:,}")
            success = False
        
        if kimi_length != expected_kimi:
            print(f"❌ Base class Kimi length incorrect: expected {expected_kimi:,}, got {kimi_length:,}")
            success = False
        
        if success:
            print("✅ Base class context lengths are correct")
        
        return success
        
    except Exception as e:
        print(f"❌ Base class context length test failed: {e}")
        return False


def test_context_comparison():
    """Compare context lengths between models."""
    print("\n🔍 Testing context length comparison...")
    
    try:
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.kimi_provider import KimiProvider
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        
        qwen_provider = QwenProvider(
            api_key=config.llm.qwen.api_key,
            base_url=config.llm.qwen.base_url
        )
        
        kimi_provider = KimiProvider(
            api_key=config.llm.kimi.api_key,
            base_url=config.llm.kimi.base_url
        )
        
        qwen_length = qwen_provider.get_max_context_length(LLMModelType.QWEN_CODER_30B)
        kimi_length = kimi_provider.get_max_context_length(LLMModelType.KIMI_K2)
        
        print(f"📊 Context Length Comparison:")
        print(f"   Qwen Coder 30B: {qwen_length:,} tokens (256K)")
        print(f"   Kimi K2:        {kimi_length:,} tokens (128K)")
        print(f"   Ratio:          {qwen_length / kimi_length:.1f}x")
        
        if qwen_length > kimi_length:
            print("✅ Qwen now has longer context than Kimi (as expected)")
            return True
        else:
            print("❌ Context length comparison unexpected")
            return False
            
    except Exception as e:
        print(f"❌ Context comparison test failed: {e}")
        return False


def test_token_estimation():
    """Test token estimation with new context lengths."""
    print("\n🔍 Testing token estimation...")
    
    try:
        from ai_code_audit.llm.qwen_provider import QwenProvider
        from ai_code_audit.llm.base import LLMModelType
        from ai_code_audit.core.config import get_config
        
        config = get_config()
        provider = QwenProvider(
            api_key=config.llm.qwen.api_key,
            base_url=config.llm.qwen.base_url
        )
        
        # Test with different text sizes
        test_texts = [
            "Hello world",  # Small
            "def hello():\n    print('Hello, world!')\n" * 100,  # Medium
            "def hello():\n    print('Hello, world!')\n" * 1000,  # Large
        ]
        
        context_length = provider.get_max_context_length(LLMModelType.QWEN_CODER_30B)
        
        for i, text in enumerate(test_texts):
            estimated_tokens = provider.estimate_tokens(text)
            percentage = (estimated_tokens / context_length) * 100
            
            print(f"   Text {i+1}: {estimated_tokens:,} tokens ({percentage:.1f}% of context)")
            
            if estimated_tokens > context_length:
                print(f"   ⚠️  Text {i+1} exceeds context length!")
        
        print(f"✅ Token estimation test completed with {context_length:,} token context")
        return True
        
    except Exception as e:
        print(f"❌ Token estimation test failed: {e}")
        return False


def main():
    """Run all context length fix verification tests."""
    print("🚀 Context Length Fix Verification")
    print("=" * 50)
    print("Verifying Qwen3-Coder-30B-A3B-Instruct context length fix:")
    print("  Expected: 262,144 tokens (256K)")
    print("  Previous: 32,768 tokens (32K) ❌")
    print("=" * 50)
    
    tests = [
        ("Qwen Provider Context Length", test_qwen_context_length),
        ("Kimi Provider Context Length", test_kimi_context_length),
        ("Base Class Context Length", test_base_class_context_length),
        ("Context Length Comparison", test_context_comparison),
        ("Token Estimation", test_token_estimation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Context Length Fix Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All context length fixes verified!")
        print("\n✅ Key Improvements:")
        print("   • Qwen Coder 30B: 32K → 256K tokens (8x increase)")
        print("   • Now supports much larger files and repositories")
        print("   • Better repository-scale understanding")
        print("   • Can handle entire codebases in single context")
        print("\n📈 Impact:")
        print("   • Can analyze files up to ~1MB of code")
        print("   • Better cross-file dependency analysis")
        print("   • More comprehensive security audits")
        print("   • Reduced need for file chunking")
        return 0
    else:
        print("⚠️  Some tests failed. Context length fix may be incomplete.")
        return 1


if __name__ == "__main__":
    exit(main())
