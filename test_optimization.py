#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化效果的脚本
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit import audit_project


async def test_optimization():
    """测试优化后的系统"""
    print("🚀 开始测试优化后的AI代码审计系统")
    print("=" * 60)
    
    # 测试项目路径
    test_project = "test_project"  # 您的测试项目路径
    
    # 测试参数
    test_configs = [
        {
            "name": "基础测试 - 单线程",
            "config": {
                "project_path": test_project,
                "max_files": 10,
                "quick_mode": True,
                "verbose": True,
                "enable_cross_file": True,
                "max_concurrent": 1
            }
        },
        {
            "name": "递归保护测试",
            "config": {
                "project_path": test_project,
                "max_files": 5,
                "enable_cross_file": True,
                "verbose": True,
                "debug": True
            }
        }
    ]
    
    results = []
    
    for test_config in test_configs:
        print(f"\n📋 测试: {test_config['name']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # 运行测试
            result = await audit_project(**test_config['config'])
            
            duration = time.time() - start_time
            
            # 统计结果
            total_files = len(result.get('files', []))
            total_findings = sum(len(file_result.get('findings', [])) for file_result in result.get('files', []))
            success_rate = len([f for f in result.get('files', []) if f.get('success', False)]) / max(total_files, 1)
            
            test_result = {
                'name': test_config['name'],
                'duration': duration,
                'total_files': total_files,
                'total_findings': total_findings,
                'success_rate': success_rate,
                'status': 'SUCCESS'
            }
            
            print(f"✅ 测试完成:")
            print(f"   - 耗时: {duration:.2f}秒")
            print(f"   - 文件数: {total_files}")
            print(f"   - 发现问题: {total_findings}")
            print(f"   - 成功率: {success_rate:.1%}")
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                'name': test_config['name'],
                'duration': duration,
                'error': str(e),
                'status': 'FAILED'
            }
            
            print(f"❌ 测试失败:")
            print(f"   - 耗时: {duration:.2f}秒")
            print(f"   - 错误: {e}")
        
        results.append(test_result)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {result['name']}: {result['duration']:.2f}秒")
        
        if result['status'] == 'SUCCESS':
            print(f"   成功率: {result.get('success_rate', 0):.1%}, 发现问题: {result.get('total_findings', 0)}")
        else:
            print(f"   错误: {result.get('error', 'Unknown')}")
    
    # 检查是否有递归错误
    recursion_errors = [r for r in results if 'recursion' in str(r.get('error', '')).lower()]
    if recursion_errors:
        print(f"\n⚠️  发现 {len(recursion_errors)} 个递归错误，优化可能未完全生效")
    else:
        print(f"\n🎉 未发现递归错误，优化生效！")
    
    return results


def check_optimization_status():
    """检查优化状态"""
    print("🔍 检查优化状态")
    print("-" * 30)
    
    # 检查关键文件是否存在修改
    key_files = [
        "ai_code_audit/llm/manager.py",
        "ai_code_audit/analysis/cross_file_analyzer.py", 
        "ai_code_audit/llm/qwen_provider.py",
        "ai_code_audit/llm/kimi_provider.py",
        "ai_code_audit/utils/recursion_monitor.py",
        "ai_code_audit/__init__.py"
    ]
    
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 文件不存在")
    
    # 检查关键修改
    try:
        from ai_code_audit.utils.recursion_monitor import RecursionGuard, AnalysisType
        print("✅ 递归监控器导入成功")
    except ImportError as e:
        print(f"❌ 递归监控器导入失败: {e}")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        # 检查analyze_code方法是否有analysis_context参数
        import inspect
        sig = inspect.signature(LLMManager.analyze_code)
        if 'analysis_context' in sig.parameters:
            print("✅ LLMManager.analyze_code 已添加 analysis_context 参数")
        else:
            print("❌ LLMManager.analyze_code 缺少 analysis_context 参数")
    except Exception as e:
        print(f"❌ LLMManager 检查失败: {e}")


if __name__ == "__main__":
    print("🔧 AI代码审计系统优化测试")
    print("=" * 60)
    
    # 检查优化状态
    check_optimization_status()
    
    print("\n")
    
    # 运行测试
    try:
        asyncio.run(test_optimization())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
