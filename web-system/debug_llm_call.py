#!/usr/bin/env python3
"""
调试LLM调用的具体问题
"""
import sys
import os
from pathlib import Path
import asyncio

# 添加AI审计引擎到Python路径
ai_engine_path = str(Path(__file__).parent.parent)
sys.path.insert(0, ai_engine_path)

async def debug_llm_call():
    """详细调试LLM调用流程"""
    print("=== LLM调用流程调试 ===")
    
    # 切换到AI引擎根目录
    original_cwd = os.getcwd()
    os.chdir(ai_engine_path)
    
    try:
        # 1. 加载配置和初始化
        print("\n--- 步骤1: 配置加载 ---")
        from ai_code_audit.core.config import ConfigManager
        from ai_code_audit.core.file_filter import FileFilter
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.llm.manager import LLMManager
        from ai_code_audit.templates.advanced_templates import AdvancedTemplateManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        print("✅ 配置加载成功")
        
        # 2. 项目分析
        print("\n--- 步骤2: 项目分析 ---")
        test_project_path = f"{original_cwd}/backend/uploads/10/project"
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(test_project_path, save_to_db=False)
        print(f"✅ 项目分析完成，发现 {len(project_info.files)} 个文件")
        
        # 3. 跳过文件过滤，直接使用所有文件
        print("\n--- 步骤3: 跳过文件过滤，使用所有文件 ---")
        filtered_files = project_info.files
        print(f"文件数: {len(filtered_files)}")
        
        for i, file_info in enumerate(filtered_files):
            print(f"  文件{i+1}: {file_info.path} (语言: {file_info.language})")
        
        if not filtered_files:
            print("❌ 没有文件！")
            return
        
        # 4. LLM管理器初始化
        print("\n--- 步骤4: LLM管理器初始化 ---")
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

        llm_manager = LLMManager(llm_config_dict)
        print(f"✅ LLM管理器初始化完成，提供商: {list(llm_manager.providers.keys())}")
        
        # 5. 模板管理器
        print("\n--- 步骤5: 模板加载 ---")
        template_manager = AdvancedTemplateManager()
        template = "owasp_top_10_2021"
        template_obj = template_manager.get_template(template)
        
        if template_obj:
            print(f"✅ 模板加载成功: {template}")
            print(f"模板系统提示词长度: {len(template_obj.system_prompt) if template_obj.system_prompt else 0}")
        else:
            print(f"❌ 模板加载失败: {template}")
            available_templates = template_manager.list_templates()
            print(f"可用模板: {available_templates}")
            return
        
        # 6. 测试单个文件分析
        print("\n--- 步骤6: 单文件分析测试 ---")
        test_file = filtered_files[0]
        print(f"测试文件: {test_file.path}")
        
        # 读取文件内容
        try:
            with open(test_file.path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ 文件读取成功，内容长度: {len(content)}")
            print(f"内容预览: {content[:200]}...")
        except Exception as e:
            print(f"❌ 文件读取失败: {e}")
            return
        
        # 7. 实际调用LLM
        print("\n--- 步骤7: LLM调用测试 ---")
        try:
            print("开始调用LLM...")
            response = await llm_manager.analyze_code(
                code=content,
                file_path=str(test_file.path),
                language=test_file.language,
                template=template
            )
            print(f"✅ LLM调用成功!")
            print(f"响应类型: {type(response)}")
            
            if response:
                print(f"响应成功状态: {response.get('success', 'unknown')}")
                findings = response.get('findings', [])
                print(f"发现的问题数量: {len(findings)}")
                
                if findings:
                    for i, finding in enumerate(findings[:3]):  # 只显示前3个
                        print(f"  问题{i+1}: {finding.get('type', 'unknown')} - {finding.get('severity', 'unknown')}")
                else:
                    print("  未发现安全问题")
            else:
                print("❌ LLM返回空响应")
                
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 8. 关闭LLM管理器
        await llm_manager.close()
        
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    asyncio.run(debug_llm_call())
