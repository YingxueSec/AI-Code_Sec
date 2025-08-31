#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定的文件上传文件，验证跨文件分析
"""

import sys
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit.llm.manager import LLMManager

async def test_upload_file():
    """测试文件上传文件的跨文件分析"""
    print("🎯 测试文件上传文件的跨文件分析\n")
    
    # 初始化LLM管理器
    config = {
        'llm': {
            'kimi': {
                'api_key': 'sk-kpepqjjtmxpcdhqcvrdekuroxvmpmphkfouhzbcbudbpzzzt',
                'base_url': 'https://api.siliconflow.cn/v1',
                'model_name': 'moonshotai/Kimi-K2-Instruct',
                'enabled': True,
                'priority': 1,
                'max_requests_per_minute': 10000,
                'cost_weight': 1.0,
                'performance_weight': 1.0,
                'timeout': 60
            }
        }
    }
    
    try:
        llm_manager = LLMManager(config)
        # 设置项目路径，启用跨文件分析
        project_path = "examples/test_oa-system"
        llm_manager.set_project_path(project_path)
        print("✅ LLM管理器和跨文件分析器初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 测试文件
    test_file = "examples/test_oa-system/src/main/resources/static/plugins/kindeditor/php/upload_json.php"
    
    if not Path(test_file).exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 读取文件内容
        with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        print(f"📄 测试文件: {Path(test_file).name}")
        print(f"📄 文件大小: {len(code)} 字符")
        print(f"📄 文件类型: PHP文件上传脚本")
        
        # 进行安全分析
        print("\n🔍 开始安全分析...")
        result = await llm_manager.analyze_code(
            code=code,
            file_path=test_file,
            language="php",
            template="security_audit_chinese"
        )
        
        if not result.get('success'):
            print(f"❌ 分析失败: {result.get('error', 'Unknown error')}")
            return False
        
        findings = result.get('findings', [])
        print(f"📊 发现 {len(findings)} 个安全问题")
        
        # 检查是否有跨文件分析
        cross_file_count = 0
        for i, finding in enumerate(findings, 1):
            print(f"\n--- 问题 {i}: {finding.get('type', 'Unknown')} ---")
            print(f"严重程度: {finding.get('severity', 'N/A')}")
            print(f"置信度: {finding.get('confidence', 'N/A')}")
            print(f"描述: {finding.get('description', 'N/A')[:100]}...")
            
            if 'cross_file_analysis' in finding:
                cross_file_analysis = finding['cross_file_analysis']
                print(f"🔗 跨文件分析:")
                print(f"  原始置信度: {cross_file_analysis.get('original_confidence', 'N/A')}")
                print(f"  调整后置信度: {cross_file_analysis.get('adjusted_confidence', 'N/A')}")
                print(f"  相关文件数: {len(cross_file_analysis.get('related_files', []))}")
                print(f"  证据数: {len(cross_file_analysis.get('evidence', []))}")
                print(f"  建议: {cross_file_analysis.get('recommendation', 'N/A')}")
                
                if cross_file_analysis.get('related_files'):
                    print(f"  相关文件:")
                    for rf in cross_file_analysis['related_files']:
                        print(f"    - {Path(rf['path']).name} ({rf['relationship']})")
                
                if cross_file_analysis.get('evidence'):
                    print(f"  证据:")
                    for evidence in cross_file_analysis['evidence'][:2]:  # 只显示前2个
                        print(f"    - {evidence[:80]}...")
                
                cross_file_count += 1
            else:
                print("❌ 未进行跨文件分析")
        
        print(f"\n🎯 跨文件分析统计:")
        print(f"  总问题数: {len(findings)}")
        print(f"  进行跨文件分析的问题数: {cross_file_count}")
        print(f"  跨文件分析覆盖率: {cross_file_count/len(findings)*100:.1f}%" if findings else "0%")
        
        # 保存详细结果
        output_file = 'upload_file_analysis_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细结果已保存到: {output_file}")
        
        if cross_file_count > 0:
            print("✅ 跨文件分析功能正常工作！")
            return True
        else:
            print("⚠️  跨文件分析未被触发，需要进一步调试")
            return False
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

async def main():
    """主函数"""
    try:
        success = await test_upload_file()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
