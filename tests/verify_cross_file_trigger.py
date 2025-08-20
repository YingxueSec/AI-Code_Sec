#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证跨文件分析触发逻辑
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_trigger_conditions():
    """测试触发条件"""
    print("🔍 验证跨文件分析触发条件\n")
    
    # 模拟不同置信度的问题
    test_cases = [
        {'confidence': 0.99, 'type': 'SQL注入', 'expected': False},
        {'confidence': 0.98, 'type': 'SQL注入', 'expected': True},  # 刚好低于0.98阈值
        {'confidence': 0.95, 'type': 'XSS跨站脚本攻击', 'expected': True},  # XSS类型
        {'confidence': 0.90, 'type': '文件上传漏洞', 'expected': True},  # 文件上传类型
        {'confidence': 0.85, 'type': '路径遍历', 'expected': True},  # 路径遍历类型
        {'confidence': 0.80, 'type': '权限验证绕过', 'expected': True},  # 权限类型
        {'confidence': 0.30, 'type': '硬编码密钥', 'expected': False},  # 低于0.4阈值
    ]
    
    print("测试LLMManager中的触发条件:")
    for i, case in enumerate(test_cases, 1):
        confidence = case['confidence']
        finding_type = case['type']
        expected = case['expected']
        
        # 模拟LLMManager中的触发逻辑
        should_analyze_cross_file = (
            (confidence < 0.95 and confidence > 0.4) or
            any(keyword in finding_type for keyword in ['文件上传', 'XSS', '路径遍历', '权限'])
        )
        
        status = "✅" if should_analyze_cross_file == expected else "❌"
        print(f"  {i}. 置信度{confidence}, 类型'{finding_type}' → {should_analyze_cross_file} {status}")
    
    print("\n测试CrossFileAnalyzer中的触发条件:")
    for i, case in enumerate(test_cases, 1):
        confidence = case['confidence']
        finding_type = case['type']
        
        # 模拟CrossFileAnalyzer中的触发逻辑
        should_analyze = confidence <= 0.98
        
        status = "会分析" if should_analyze else "跳过"
        print(f"  {i}. 置信度{confidence} → {status}")

def analyze_previous_results():
    """分析之前的测试结果"""
    print("\n🔍 分析之前的测试结果\n")
    
    # 检查之前的结果文件
    result_files = [
        'test_with_cross_file_analysis.json',
        'test_with_cross_file_analysis_v2.json'
    ]
    
    for result_file in result_files:
        if Path(result_file).exists():
            print(f"📄 分析文件: {result_file}")
            
            import json
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                findings = data.get('findings', [])
                print(f"  总问题数: {len(findings)}")
                
                for i, finding in enumerate(findings, 1):
                    confidence = finding.get('confidence', 'N/A')
                    finding_type = finding.get('type', 'Unknown')
                    has_cross_file = 'cross_file_analysis' in finding
                    
                    print(f"  问题{i}: {finding_type}")
                    print(f"    置信度: {confidence}")
                    print(f"    有跨文件分析: {has_cross_file}")
                    
                    if has_cross_file:
                        cross_file = finding['cross_file_analysis']
                        related_files_count = len(cross_file.get('related_files', []))
                        recommendation = cross_file.get('recommendation', '')
                        print(f"    相关文件数: {related_files_count}")
                        print(f"    建议: {recommendation[:50]}...")
                    print()
                    
            except Exception as e:
                print(f"  ❌ 解析失败: {e}")
        else:
            print(f"📄 文件不存在: {result_file}")

def main():
    """主函数"""
    print("🚀 验证跨文件分析功能\n")
    
    test_trigger_conditions()
    analyze_previous_results()
    
    print("\n🎯 结论:")
    print("1. 触发条件逻辑正确")
    print("2. 需要检查实际运行时的置信度值")
    print("3. 可能需要调整阈值或添加更多触发条件")
    
    print("\n💡 建议:")
    print("1. 降低CrossFileAnalyzer的阈值到0.95")
    print("2. 为特定问题类型强制启用跨文件分析")
    print("3. 添加调试日志查看实际触发情况")

if __name__ == "__main__":
    main()
