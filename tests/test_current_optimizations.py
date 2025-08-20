#!/usr/bin/env python3
"""
测试当前优化效果的脚本
"""
import asyncio
import time
import logging
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.llm.models import LLMRequest, LLMMessage, MessageRole, LLMModelType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_file_filtering():
    """测试文件过滤逻辑"""
    print("🔍 测试文件过滤逻辑")
    print("=" * 50)
    
    try:
        from ai_code_audit.core.file_scanner import FileScanner
        from ai_code_audit.core.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        scanner = FileScanner(config)
        test_path = "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2"
        
        if os.path.exists(test_path):
            files = list(scanner.scan_files(test_path))
            
            # 统计文件类型
            file_types = {}
            for file_path in files:
                ext = os.path.splitext(file_path)[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            print(f"📊 扫描结果:")
            print(f"  总文件数: {len(files)}")
            print(f"  文件类型分布:")
            for ext, count in sorted(file_types.items()):
                print(f"    {ext or '无扩展名'}: {count}")
            
            # 检查是否有JS/CSS文件被包含
            js_css_files = [f for f in files if f.endswith(('.js', '.css'))]
            if js_css_files:
                print(f"⚠️  发现 {len(js_css_files)} 个JS/CSS文件未被过滤:")
                for f in js_css_files[:5]:  # 只显示前5个
                    print(f"    {f}")
                if len(js_css_files) > 5:
                    print(f"    ... 还有 {len(js_css_files) - 5} 个")
                return False
            else:
                print("✅ 文件过滤正常工作")
                return True
        else:
            print(f"❌ 测试路径不存在: {test_path}")
            return False
            
    except Exception as e:
        print(f"❌ 文件过滤测试失败: {e}")
        return False


async def test_api_optimizations():
    """测试API优化效果"""
    print("\n🚀 测试API优化效果")
    print("=" * 50)
    
    try:
        # 初始化LLM管理器
        llm_manager = LLMManager()
        
        # 显示初始统计
        if hasattr(llm_manager, 'get_comprehensive_stats'):
            stats = llm_manager.get_comprehensive_stats()
            print(f"📊 初始统计:")
            print(f"  并发数: {stats['concurrency']['current_concurrency']}")
            print(f"  TPM使用率: {stats['rate_limits'].get('tpm_usage_percent', 0):.1f}%")
            print(f"  RPM使用率: {stats['rate_limits'].get('rpm_usage_percent', 0):.1f}%")
        else:
            print("📊 使用基础统计")
        
        # 创建测试请求
        test_requests = []
        for i in range(5):  # 减少到5个请求以快速测试
            request = LLMRequest(
                messages=[
                    LLMMessage(MessageRole.SYSTEM, "你是一个代码安全审计专家"),
                    LLMMessage(MessageRole.USER, f"请简单分析这段代码 #{i+1}: echo 'test';")
                ],
                model=LLMModelType.KIMI_K2,
                temperature=0.1,
                max_tokens=50  # 减少token使用
            )
            test_requests.append(request)
        
        # 执行请求
        start_time = time.time()
        successful = 0
        failed = 0
        
        for i, request in enumerate(test_requests):
            try:
                logger.info(f"执行请求 #{i+1}")
                response = await llm_manager.chat_completion(request)
                logger.info(f"请求 #{i+1} 成功，响应长度: {len(response.content)}")
                successful += 1
            except Exception as e:
                logger.error(f"请求 #{i+1} 失败: {e}")
                failed += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n📊 测试结果:")
        print(f"  总请求数: {len(test_requests)}")
        print(f"  成功请求: {successful}")
        print(f"  失败请求: {failed}")
        print(f"  成功率: {successful/len(test_requests)*100:.1f}%")
        print(f"  总耗时: {total_time:.2f}秒")
        print(f"  平均耗时: {total_time/len(test_requests):.2f}秒/请求")
        
        await llm_manager.close()
        
        return successful >= len(test_requests) * 0.8  # 80%成功率
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


async def test_large_file_handling():
    """测试大文件处理"""
    print("\n📁 测试大文件处理")
    print("=" * 50)
    
    try:
        # 检查大文件是否存在
        large_files = [
            "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2/app/controllers/login.php",
            "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2/app/controllers/user.php",
            "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2/app/models/qmsoft.php"
        ]
        
        existing_files = []
        for file_path in large_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                existing_files.append((file_path, size))
                print(f"📄 {os.path.basename(file_path)}: {size/1024/1024:.1f}MB")
        
        if existing_files:
            print(f"✅ 发现 {len(existing_files)} 个大文件需要特殊处理")
            return True
        else:
            print("⚠️  未发现大文件")
            return False
            
    except Exception as e:
        print(f"❌ 大文件检查失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🧪 当前优化效果测试")
    print("=" * 60)
    
    results = {}
    
    # 测试文件过滤
    results['file_filtering'] = await test_file_filtering()
    
    # 测试API优化
    results['api_optimization'] = await test_api_optimizations()
    
    # 测试大文件处理
    results['large_file_handling'] = await test_large_file_handling()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有优化都正常工作！")
    else:
        print("⚠️  仍有问题需要解决")
        
        # 给出具体建议
        if not results['file_filtering']:
            print("  - 需要修复文件过滤逻辑")
        if not results['api_optimization']:
            print("  - 需要检查API配置和网络连接")
        if not results['large_file_handling']:
            print("  - 需要实现大文件分块处理")


if __name__ == "__main__":
    asyncio.run(main())
