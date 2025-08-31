#!/usr/bin/env python3
"""
调试AI集成问题的脚本
"""
import sys
import os
from pathlib import Path
import asyncio

# 添加AI审计引擎到Python路径
ai_engine_path = str(Path(__file__).parent.parent)
sys.path.insert(0, ai_engine_path)

async def test_ai_integration():
    """测试AI集成"""
    print("=== AI集成调试测试 ===")
    
    # 1. 检查工作目录
    original_cwd = os.getcwd()
    print(f"原始工作目录: {original_cwd}")
    
    # 2. 切换到AI引擎根目录
    os.chdir(ai_engine_path)
    new_cwd = os.getcwd()
    print(f"AI引擎工作目录: {new_cwd}")
    
    try:
        # 3. 测试配置加载
        print("\n--- 测试配置加载 ---")
        from ai_code_audit.core.config import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print(f"Kimi配置存在: {bool(config.llm.kimi and config.llm.kimi.api_key)}")
        print(f"Qwen配置存在: {bool(config.llm.qwen and config.llm.qwen.api_key)}")
        
        if config.llm.kimi and config.llm.kimi.api_key:
            print(f"Kimi API密钥: {config.llm.kimi.api_key[:6]}...")
            print(f"Kimi启用状态: {config.llm.kimi.enabled}")
            
        # 4. 测试LLM管理器初始化
        print("\n--- 测试LLM管理器 ---")
        from ai_code_audit.llm.manager import LLMManager
        
        # 构建LLM配置
        llm_config_dict = {
            'llm': {
                'performance': {
                    'max_parallel_requests': 5,
                    'batch_size': 3,
                    'timeout': 300
                }
            }
        }
        
        # 添加kimi配置
        if config.llm.kimi and config.llm.kimi.enabled:
            llm_config_dict['llm']['kimi'] = {
                'api_key': config.llm.kimi.api_key,
                'base_url': config.llm.kimi.base_url,
                'enabled': config.llm.kimi.enabled,
                'priority': config.llm.kimi.priority,
                'max_requests_per_minute': config.llm.kimi.max_requests_per_minute,
                'cost_weight': config.llm.kimi.cost_weight,
                'performance_weight': config.llm.kimi.performance_weight,
            }

        # 添加qwen配置
        if config.llm.qwen and config.llm.qwen.enabled:
            llm_config_dict['llm']['qwen'] = {
                'api_key': config.llm.qwen.api_key,
                'base_url': config.llm.qwen.base_url,
                'enabled': config.llm.qwen.enabled,
                'priority': config.llm.qwen.priority,
                'max_requests_per_minute': config.llm.qwen.max_requests_per_minute,
                'cost_weight': config.llm.qwen.cost_weight,
                'performance_weight': config.llm.qwen.performance_weight,
            }

        print(f"LLM配置: {llm_config_dict}")
        
        llm_manager = LLMManager(llm_config_dict)
        print(f"LLM提供商数量: {len(llm_manager.providers)}")
        print(f"可用提供商: {list(llm_manager.providers.keys())}")
        
        # 5. 测试具体的审计流程
        print("\n--- 测试审计流程 ---")
        test_project_path = f"{original_cwd}/backend/uploads/10/project"
        print(f"测试项目路径: {test_project_path}")
        print(f"项目路径存在: {Path(test_project_path).exists()}")
        
        if Path(test_project_path).exists():
            # 检查文件
            files = list(Path(test_project_path).glob("*.py"))
            print(f"发现Python文件: {[f.name for f in files]}")
            
            if files:
                # 读取文件内容的前几行
                sample_file = files[0]
                with open(sample_file, 'r') as f:
                    lines = f.readlines()[:5]
                print(f"示例文件内容: {lines}")
        
        # 6. 关闭LLM管理器
        await llm_manager.close()
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
        print(f"\n恢复工作目录: {os.getcwd()}")

if __name__ == "__main__":
    asyncio.run(test_ai_integration())
