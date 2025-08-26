#!/usr/bin/env python3
"""
测试LLM配置是否正确
"""

import sys
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit.core.config import get_config
from ai_code_audit.llm.manager import LLMManager

def test_config():
    """测试配置加载"""
    print("🔧 测试配置加载...")
    
    try:
        config = get_config()
        print(f"✅ 配置加载成功")
        print(f"📋 LLM默认模型: {config.llm.default_model}")
        
        if config.llm.qwen:
            print(f"🤖 Qwen配置: enabled={config.llm.qwen.enabled}, api_key={'***' + config.llm.qwen.api_key[-4:] if config.llm.qwen.api_key else 'None'}")
        
        if config.llm.kimi:
            print(f"🤖 Kimi配置: enabled={config.llm.kimi.enabled}, api_key={'***' + config.llm.kimi.api_key[-4:] if config.llm.kimi.api_key else 'None'}")
            
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    return True

def test_llm_manager():
    """测试LLM管理器"""
    print("\n🤖 测试LLM管理器...")
    
    try:
        llm_manager = LLMManager()
        print(f"✅ LLM管理器初始化成功")
        print(f"📋 可用提供商: {list(llm_manager.providers.keys())}")
        
        if not llm_manager.providers:
            print("⚠️  没有可用的LLM提供商")
            return False
            
        # 测试简单的代码分析
        test_code = """
public class Test {
    public void unsafeMethod(String input) {
        String sql = "SELECT * FROM users WHERE name = '" + input + "'";
        // SQL注入漏洞
    }
}
"""
        
        print("\n🔍 测试代码分析...")
        import asyncio
        
        async def test_analysis():
            try:
                response = await llm_manager.analyze_code(
                    code=test_code,
                    file_path="Test.java",
                    language="java",
                    template="security_audit_chinese"
                )
                print(f"📊 分析结果: success={response.get('success', False)}")
                if response.get('findings'):
                    print(f"🚨 发现问题数: {len(response['findings'])}")
                    for finding in response['findings'][:2]:  # 只显示前2个
                        print(f"  - {finding.get('type', 'Unknown')}: {finding.get('severity', 'Unknown')}")
                return response.get('success', False)
            except Exception as e:
                print(f"❌ 代码分析失败: {e}")
                return False
        
        result = asyncio.run(test_analysis())
        return result
        
    except Exception as e:
        print(f"❌ LLM管理器初始化失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 AI代码审计系统 - LLM配置测试")
    print("=" * 50)
    
    # 测试配置
    config_ok = test_config()
    
    # 测试LLM管理器
    if config_ok:
        llm_ok = test_llm_manager()
        
        if llm_ok:
            print("\n🎉 所有测试通过！LLM配置正常")
        else:
            print("\n⚠️  LLM功能测试失败，但配置正常")
    else:
        print("\n❌ 配置测试失败")
