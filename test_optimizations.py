#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化方案的效果
"""

import asyncio
import time
import json
from pathlib import Path
from ai_code_audit import audit_project


async def test_optimization_comparison():
    """对比优化前后的性能"""
    
    test_project = "examples/test_cross_file"
    
    print("🚀 开始优化方案对比测试")
    print("="*60)
    
    # 测试1：原始版本（串行 + 无缓存）
    print("\n📊 测试1：原始版本（串行分析）")
    start_time = time.time()
    
    results_original = await audit_project(
        project_path=test_project,
        output_file="test_original.json",
        show_timing=True,
        debug=True  # 强制串行模式
    )
    
    original_time = time.time() - start_time
    original_findings = len(results_original.get('findings', []))
    
    print(f"✅ 原始版本完成")
    print(f"   - 总时间: {original_time:.2f}秒")
    print(f"   - 发现问题: {original_findings}个")
    
    # 等待一下，避免缓存影响
    await asyncio.sleep(2)
    
    # 测试2：优化版本（并行 + 缓存）
    print("\n📊 测试2：优化版本（并行 + 缓存）")
    start_time = time.time()
    
    results_optimized = await audit_project(
        project_path=test_project,
        output_file="test_optimized.json",
        show_timing=True,
        debug=False  # 启用并行模式
    )
    
    optimized_time = time.time() - start_time
    optimized_findings = len(results_optimized.get('findings', []))
    
    print(f"✅ 优化版本完成")
    print(f"   - 总时间: {optimized_time:.2f}秒")
    print(f"   - 发现问题: {optimized_findings}个")
    
    # 测试3：第二次运行（测试缓存效果）
    print("\n📊 测试3：缓存效果测试（第二次运行）")
    start_time = time.time()
    
    results_cached = await audit_project(
        project_path=test_project,
        output_file="test_cached.json",
        show_timing=True,
        debug=False
    )
    
    cached_time = time.time() - start_time
    cached_findings = len(results_cached.get('findings', []))
    
    print(f"✅ 缓存测试完成")
    print(f"   - 总时间: {cached_time:.2f}秒")
    print(f"   - 发现问题: {cached_findings}个")
    
    # 性能对比分析
    print("\n" + "="*60)
    print("📈 性能对比分析")
    print("="*60)
    
    print(f"原始版本时间:     {original_time:>8.2f}秒")
    print(f"优化版本时间:     {optimized_time:>8.2f}秒")
    print(f"缓存版本时间:     {cached_time:>8.2f}秒")
    print("-" * 40)
    
    if original_time > 0:
        parallel_speedup = original_time / optimized_time
        cache_speedup = original_time / cached_time
        
        print(f"并行优化提升:     {parallel_speedup:>8.2f}倍")
        print(f"缓存优化提升:     {cache_speedup:>8.2f}倍")
        print(f"并行优化率:       {(1 - optimized_time/original_time)*100:>7.1f}%")
        print(f"缓存优化率:       {(1 - cached_time/original_time)*100:>7.1f}%")
    
    print("-" * 40)
    print(f"原始版本问题数:   {original_findings:>8}个")
    print(f"优化版本问题数:   {optimized_findings:>8}个")
    print(f"缓存版本问题数:   {cached_findings:>8}个")
    
    # 准确性检查
    accuracy_maintained = (original_findings == optimized_findings == cached_findings)
    print(f"准确性保持:       {'✅ 是' if accuracy_maintained else '❌ 否':>8}")
    
    # 缓存统计
    if 'timing_stats' in results_cached:
        cache_hit_rate = results_cached['timing_stats'].get('缓存命中率', 0)
        print(f"缓存命中率:       {cache_hit_rate:>7.1f}%")
    
    # 生成优化建议
    print("\n" + "="*60)
    print("💡 优化建议")
    print("="*60)
    
    if parallel_speedup > 1.5:
        print("✅ 并行处理效果显著，建议在生产环境中启用")
    else:
        print("⚠️  并行处理效果有限，可能受到API限制影响")
    
    if cache_speedup > 5:
        print("✅ 缓存效果显著，建议启用智能缓存")
    else:
        print("⚠️  缓存效果有限，建议检查缓存配置")
    
    if accuracy_maintained:
        print("✅ 优化后准确性保持，可以安全使用")
    else:
        print("❌ 优化后准确性下降，需要调整优化策略")
    
    # 资源使用建议
    print("\n📋 资源使用建议:")
    if optimized_time < 60:
        print("- 当前性能良好，适合实时分析")
    elif optimized_time < 300:
        print("- 性能可接受，适合批量分析")
    else:
        print("- 性能需要进一步优化，建议:")
        print("  * 增加并发数（注意API限制）")
        print("  * 使用更快的LLM模型")
        print("  * 启用代码预处理")
    
    return {
        'original_time': original_time,
        'optimized_time': optimized_time,
        'cached_time': cached_time,
        'parallel_speedup': parallel_speedup if original_time > 0 else 0,
        'cache_speedup': cache_speedup if original_time > 0 else 0,
        'accuracy_maintained': accuracy_maintained
    }


async def test_cache_effectiveness():
    """测试缓存有效性"""
    from ai_code_audit.utils.cache import get_cache
    
    print("\n🔍 缓存有效性测试")
    print("-" * 40)
    
    cache = get_cache()
    stats = cache.get_stats()
    
    print(f"缓存文件数: {stats['total_files']}")
    print(f"缓存大小: {stats['total_size_mb']:.2f}MB")
    print(f"有效缓存: {stats['valid_files']}")
    print(f"过期缓存: {stats['expired_files']}")
    
    if stats['total_files'] > 0:
        print("✅ 缓存系统正常工作")
    else:
        print("⚠️  缓存系统可能未正常工作")


async def main():
    """主测试函数"""
    try:
        # 运行对比测试
        results = await test_optimization_comparison()
        
        # 测试缓存
        await test_cache_effectiveness()
        
        # 保存测试结果
        with open('optimization_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试结果已保存到: optimization_test_results.json")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
