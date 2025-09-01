#!/usr/bin/env python3
"""
简化的队列功能测试脚本
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_queue_functionality():
    """测试队列核心功能"""
    print("🧪 开始测试队列功能...")
    
    try:
        # 测试1: 导入队列服务
        print("📦 测试导入队列服务...")
        from app.services.task_queue_service import task_queue_service, QueueTask, QueuePriority
        print("✅ 队列服务导入成功")
        
        # 测试2: Redis连接
        print("🔌 测试Redis连接...")
        redis = await task_queue_service.get_redis()
        pong = await redis.ping()
        print(f"✅ Redis连接成功: {pong}")
        
        # 测试3: 获取队列状态
        print("📊 测试获取队列状态...")
        status = await task_queue_service.get_queue_status()
        print(f"✅ 队列状态: 队列长度={status['queue_length']}, 运行中={status['running_count']}")
        
        # 测试4: 创建模拟队列任务
        print("📝 测试创建队列任务...")
        from datetime import datetime
        
        # 清理现有队列
        await redis.delete("audit_task_queue")
        await redis.delete("audit_running_tasks")
        
        # 添加测试任务到队列
        test_task = QueueTask(
            task_id=999,
            user_id=1,
            user_level="admin",
            priority=QueuePriority.URGENT.value,
            project_path="/tmp/test",
            created_at=datetime.utcnow().isoformat()
        )
        
        await redis.zadd(
            "audit_task_queue",
            {str(test_task.to_dict()): -test_task.priority}
        )
        
        # 验证任务添加成功
        queue_length = await redis.zcard("audit_task_queue")
        print(f"✅ 测试任务添加成功，队列长度: {queue_length}")
        
        # 测试5: 获取队列详情
        print("🔍 测试获取队列详情...")
        updated_status = await task_queue_service.get_queue_status()
        print(f"✅ 更新后队列状态: {updated_status}")
        
        # 测试6: 用户队列信息
        print("👤 测试用户队列信息...")
        user_info = await task_queue_service.get_user_queue_info(1)
        print(f"✅ 用户队列信息: {user_info}")
        
        # 清理测试数据
        await redis.delete("audit_task_queue")
        await redis.delete("audit_running_tasks")
        
        await task_queue_service.close()
        print("✅ 所有测试通过！队列功能正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_integration():
    """测试API集成"""
    print("\n🌐 测试API集成...")
    
    try:
        # 测试导入API模块
        print("📦 测试导入API模块...")
        from app.api.audit import router
        print("✅ API模块导入成功")
        
        # 检查队列相关路由
        routes = [route.path for route in router.routes]
        queue_routes = [path for path in routes if 'queue' in path]
        print(f"✅ 队列相关路由: {queue_routes}")
        
        return True
        
    except Exception as e:
        print(f"❌ API集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 队列系统功能测试")
    print("=" * 50)
    
    # 测试核心功能
    core_test = await test_queue_functionality()
    
    # 测试API集成
    api_test = await test_api_integration()
    
    print("\n" + "=" * 50)
    if core_test and api_test:
        print("🎉 所有测试通过！队列系统可以正常使用")
        return True
    else:
        print("❌ 测试失败，需要修复问题")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
