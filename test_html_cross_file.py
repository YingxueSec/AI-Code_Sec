#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HTML文件的跨文件分析
"""

import sys
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit.llm.manager import LLMManager

async def test_html_cross_file():
    """测试HTML文件的跨文件分析"""
    print("🎯 测试HTML文件的跨文件分析\n")
    
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
    test_file = "examples/test_oa-system/src/main/resources/static/plugins/kindeditor/plugins/baidumap/index.html"
    
    if not Path(test_file).exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 读取文件内容
        with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        print(f"📄 测试文件: {Path(test_file).name}")
        print(f"📄 文件大小: {len(code)} 字符")
        print(f"📄 文件类型: HTML/JavaScript")
        
        # 进行安全分析
        print("\n🔍 开始安全分析...")
        result = await llm_manager.analyze_code(
            code=code,
            file_path=test_file,
            language="javascript",  # 这个HTML文件主要包含JavaScript
            template="security_audit_chinese"
        )
        
        if not result.get('success'):
            print(f"❌ 分析失败: {result.get('error', 'Unknown error')}")
            return False
        
        findings = result.get('findings', [])
        print(f"📊 发现 {len(findings)} 个安全问题")
        
        # 检查跨文件分析
        cross_file_count = 0
        actual_cross_file_count = 0
        
        for i, finding in enumerate(findings, 1):
            print(f"\n--- 问题 {i}: {finding.get('type', 'Unknown')} ---")
            print(f"严重程度: {finding.get('severity', 'N/A')}")
            print(f"置信度: {finding.get('confidence', 'N/A')}")
            print(f"描述: {finding.get('description', 'N/A')[:100]}...")
            
            if 'cross_file_analysis' in finding:
                cross_file_analysis = finding['cross_file_analysis']
                original_conf = cross_file_analysis.get('original_confidence', 'N/A')
                adjusted_conf = cross_file_analysis.get('adjusted_confidence', 'N/A')
                related_files = cross_file_analysis.get('related_files', [])
                evidence = cross_file_analysis.get('evidence', [])
                recommendation = cross_file_analysis.get('recommendation', 'N/A')
                
                print(f"🔗 跨文件分析:")
                print(f"  原始置信度: {original_conf}")
                print(f"  调整后置信度: {adjusted_conf}")
                print(f"  相关文件数: {len(related_files)}")
                print(f"  证据数: {len(evidence)}")
                print(f"  建议: {recommendation}")
                
                cross_file_count += 1
                
                if len(related_files) > 0 or len(evidence) > 0:
                    actual_cross_file_count += 1
                    print(f"  ✅ 实际进行了跨文件分析")
                    
                    if related_files:
                        print(f"  相关文件:")
                        for rf in related_files[:3]:  # 只显示前3个
                            print(f"    - {Path(rf['path']).name} ({rf['relationship']})")
                    
                    if evidence:
                        print(f"  证据:")
                        for ev in evidence[:2]:  # 只显示前2个
                            print(f"    - {ev[:80]}...")
                else:
                    print(f"  ⚠️  触发了跨文件分析但未找到相关文件或证据")
            else:
                print("❌ 未进行跨文件分析")
        
        print(f"\n🎯 跨文件分析统计:")
        print(f"  总问题数: {len(findings)}")
        print(f"  触发跨文件分析的问题数: {cross_file_count}")
        print(f"  实际进行跨文件分析的问题数: {actual_cross_file_count}")
        print(f"  触发率: {cross_file_count/len(findings)*100:.1f}%" if findings else "0%")
        print(f"  有效率: {actual_cross_file_count/cross_file_count*100:.1f}%" if cross_file_count else "0%")
        
        # 保存详细结果
        output_file = 'html_cross_file_analysis_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细结果已保存到: {output_file}")
        
        if actual_cross_file_count > 0:
            print("✅ 跨文件分析功能正常工作！")
            return True
        elif cross_file_count > 0:
            print("⚠️  跨文件分析被触发但未找到相关文件")
            return True
        else:
            print("❌ 跨文件分析未被触发")
            return False
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    try:
        success = await test_html_cross_file()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
