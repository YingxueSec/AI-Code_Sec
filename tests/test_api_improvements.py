#!/usr/bin/env python3
"""
测试API改进效果的脚本
"""
import asyncio
import time
import logging
from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.llm.models import LLMRequest, LLMMessage, MessageRole, LLMModelType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_api_improvements():
    """测试API改进效果"""
    print("🧪 测试API改进效果")
    print("=" * 50)
    
    # 初始化LLM管理器
    llm_manager = LLMManager()
    
    # 创建测试请求
    test_requests = []
    for i in range(20):  # 创建20个请求来测试TPM限制优化
        request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, "你是一个代码安全审计专家"),
                LLMMessage(MessageRole.USER, f"请分析这段代码的安全性 #{i+1}: console.log('test');")
            ],
            model=LLMModelType.KIMI_K2,
            temperature=0.1,
            max_tokens=100
        )
        test_requests.append(request)
    
    print(f"📊 初始统计:")
    stats = llm_manager.get_comprehensive_stats()
    print(f"  并发: {stats['concurrency']['current_concurrency']}")
    print(f"  TPM使用率: {stats['rate_limits']['tpm_usage_percent']:.1f}%")
    print(f"  RPM使用率: {stats['rate_limits']['rpm_usage_percent']:.1f}%")
    
    # 并发执行请求
    start_time = time.time()
    
    async def execute_request(req, index):
        try:
            logger.info(f"开始执行请求 #{index+1}")
            response = await llm_manager.chat_completion(req)
            logger.info(f"请求 #{index+1} 完成，响应长度: {len(response.content)}")
            return True, None
        except Exception as e:
            logger.error(f"请求 #{index+1} 失败: {e}")
            return False, str(e)
    
    # 执行所有请求
    tasks = [execute_request(req, i) for i, req in enumerate(test_requests)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 统计结果
    successful = sum(1 for r in results if isinstance(r, tuple) and r[0])
    failed = len(results) - successful
    
    print(f"\n📊 测试结果:")
    print(f"  总请求数: {len(test_requests)}")
    print(f"  成功请求: {successful}")
    print(f"  失败请求: {failed}")
    print(f"  成功率: {successful/len(test_requests)*100:.1f}%")
    print(f"  总耗时: {total_time:.2f}秒")
    print(f"  平均耗时: {total_time/len(test_requests):.2f}秒/请求")
    
    # 详细统计
    final_stats = llm_manager.get_comprehensive_stats()
    print(f"\n🔧 最终统计:")
    print(f"  并发控制:")
    for key, value in final_stats['concurrency'].items():
        print(f"    {key}: {value}")

    print(f"  限流统计:")
    for key, value in final_stats['rate_limits'].items():
        if 'percent' in key:
            print(f"    {key}: {value:.1f}%")
        else:
            print(f"    {key}: {value}")

    print(f"  提供商统计:")
    for key, value in final_stats['providers'].items():
        print(f"    {key}: {value}")
    
    # 失败详情
    if failed > 0:
        print(f"\n❌ 失败详情:")
        for i, result in enumerate(results):
            if isinstance(result, tuple) and not result[0]:
                print(f"  请求 #{i+1}: {result[1]}")
            elif isinstance(result, Exception):
                print(f"  请求 #{i+1}: {result}")
    
    await llm_manager.close()


async def test_error_recovery():
    """测试错误恢复机制"""
    print("\n🔄 测试错误恢复机制")
    print("=" * 50)
    
    llm_manager = LLMManager()
    
    # 创建一个可能导致错误的请求（超长内容）
    long_content = "分析这段代码: " + "x" * 10000  # 超长内容可能导致错误
    
    request = LLMRequest(
        messages=[
            LLMMessage(MessageRole.SYSTEM, "你是一个代码安全审计专家"),
            LLMMessage(MessageRole.USER, long_content)
        ],
        model=LLMModelType.KIMI_K2,
        temperature=0.1,
        max_tokens=50
    )
    
    try:
        print("📤 发送可能失败的请求...")
        response = await llm_manager.chat_completion(request)
        print(f"✅ 请求成功: {response.content[:100]}...")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        print("🔧 检查重试机制是否正常工作...")
    
    await llm_manager.close()


async def test_circuit_breaker():
    """测试熔断器机制"""
    print("\n⚡ 测试熔断器机制")
    print("=" * 50)
    
    llm_manager = LLMManager()
    
    # 创建多个可能失败的请求来触发熔断器
    invalid_requests = []
    for i in range(8):  # 创建8个请求，超过熔断阈值
        request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, ""),  # 空系统消息可能导致错误
                LLMMessage(MessageRole.USER, "")     # 空用户消息可能导致错误
            ],
            model=LLMModelType.KIMI_K2,
            temperature=0.1,
            max_tokens=10
        )
        invalid_requests.append(request)
    
    print("📤 发送可能触发熔断器的请求...")
    
    for i, request in enumerate(invalid_requests):
        try:
            response = await llm_manager.chat_completion(request)
            print(f"✅ 请求 #{i+1} 成功")
        except Exception as e:
            print(f"❌ 请求 #{i+1} 失败: {e}")
        
        # 检查熔断器状态
        stats = llm_manager.get_concurrency_stats()
        print(f"🔧 熔断器状态: {stats.get('circuit_breaker_state', 'unknown')}")
        
        if stats.get('circuit_breaker_state') == 'open':
            print("⚡ 熔断器已打开，停止发送请求")
            break
        
        await asyncio.sleep(1)  # 间隔1秒
    
    await llm_manager.close()


if __name__ == "__main__":
    async def main():
        await test_api_improvements()
        await test_error_recovery()
        await test_circuit_breaker()
    
    asyncio.run(main())
