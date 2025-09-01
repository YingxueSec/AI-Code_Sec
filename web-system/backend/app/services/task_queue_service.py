"""
任务队列管理服务 - 控制并发分析任务数量
支持任务队列、优先级排序、实时状态更新
"""

import asyncio
import json
import redis.asyncio as aioredis
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.models.audit import AuditTask, TaskStatus
from app.models.user import User, UserLevel
from app.services.audit_service import AuditService


class QueuePriority(int, Enum):
    """队列优先级"""
    LOW = 1      # 免费用户
    NORMAL = 2   # 标准用户
    HIGH = 3     # 高级用户
    URGENT = 4   # 管理员


@dataclass
class QueueTask:
    """队列任务数据结构"""
    task_id: int
    user_id: int
    user_level: str
    priority: int
    project_path: str
    created_at: str
    estimated_time: int = 300  # 预估执行时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueTask':
        return cls(**data)


class TaskQueueService:
    """任务队列管理服务"""
    
    # Redis键名
    QUEUE_KEY = "audit_task_queue"
    RUNNING_KEY = "audit_running_tasks"
    STATS_KEY = "audit_queue_stats"
    
    # 并发限制配置
    MAX_CONCURRENT_TASKS = 2  # 最大并发任务数
    
    # 用户级别优先级映射
    USER_PRIORITY_MAP = {
        UserLevel.free: QueuePriority.LOW,
        UserLevel.standard: QueuePriority.NORMAL,
        UserLevel.premium: QueuePriority.HIGH,
        "admin": QueuePriority.URGENT
    }
    
    def __init__(self):
        self.redis = None
    
    async def get_redis(self) -> aioredis.Redis:
        """获取Redis连接"""
        if not self.redis:
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
    
    async def add_task_to_queue(
        self,
        task_id: int,
        user: User,
        project_path: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """添加任务到队列"""
        redis = await self.get_redis()
        
        # 确定用户优先级
        user_level = user.level if hasattr(user, 'level') else UserLevel.free
        if user.role == "admin":
            priority = QueuePriority.URGENT
        else:
            priority = self.USER_PRIORITY_MAP.get(user_level, QueuePriority.LOW)
        
        # 创建队列任务
        queue_task = QueueTask(
            task_id=task_id,
            user_id=user.id,
            user_level=user_level.value if hasattr(user_level, 'value') else str(user_level),
            priority=priority.value,
            project_path=project_path,
            created_at=datetime.utcnow().isoformat()
        )
        
        # 添加到优先级队列（使用sorted set，分数为负优先级以实现高优先级在前）
        await redis.zadd(
            self.QUEUE_KEY,
            {json.dumps(queue_task.to_dict()): -priority.value}
        )
        
        # 更新任务状态为排队中
        await db.execute(
            update(AuditTask)
            .where(AuditTask.id == task_id)
            .values(
                status=TaskStatus.pending,
                progress_percent=0.0,
                error_message="任务已加入队列，等待处理..."
            )
        )
        await db.commit()
        
        # 获取队列位置
        position = await self.get_task_position(task_id)
        
        # 尝试启动任务（如果有空闲槽位）
        await self.process_queue(db)
        
        return {
            "status": "queued",
            "queue_position": position,
            "estimated_wait_time": await self.estimate_wait_time(position),
            "message": f"任务已加入队列，当前排队第 {position} 位"
        }
    
    async def get_task_position(self, task_id: int) -> int:
        """获取任务在队列中的位置"""
        redis = await self.get_redis()
        
        # 获取队列中的所有任务
        queue_items = await redis.zrevrange(self.QUEUE_KEY, 0, -1)
        
        for index, item_json in enumerate(queue_items):
            try:
                item = json.loads(item_json)
                if item.get('task_id') == task_id:
                    return index + 1
            except json.JSONDecodeError:
                continue
        
        return -1  # 任务不在队列中
    
    async def estimate_wait_time(self, position: int) -> int:
        """估算等待时间（秒）"""
        if position <= 0:
            return 0
        
        # 基础估算：每个任务5分钟，考虑并发
        base_time_per_task = 300  # 5分钟
        concurrent_slots = self.MAX_CONCURRENT_TASKS
        
        # 计算需要等待的轮次
        wait_rounds = max(0, (position - concurrent_slots - 1) // concurrent_slots + 1)
        
        return wait_rounds * base_time_per_task
    
    async def process_queue(self, db: AsyncSession) -> int:
        """处理队列，启动可用的任务"""
        redis = await self.get_redis()
        started_count = 0
        
        try:
            # 获取当前运行的任务数
            running_count = await redis.scard(self.RUNNING_KEY)
            
            # 计算可启动的任务数
            available_slots = max(0, self.MAX_CONCURRENT_TASKS - running_count)
            
            if available_slots == 0:
                return 0
            
            # 从队列中取出优先级最高的任务
            for _ in range(available_slots):
                # 取出队列头部任务（优先级最高）
                queue_items = await redis.zrevrange(self.QUEUE_KEY, 0, 0, withscores=True)
                
                if not queue_items:
                    break  # 队列为空
                
                item_json, score = queue_items[0]
                
                try:
                    queue_task = QueueTask.from_dict(json.loads(item_json))
                    
                    # 验证任务是否仍然有效
                    task_result = await db.execute(
                        select(AuditTask).where(AuditTask.id == queue_task.task_id)
                    )
                    task = task_result.scalar_one_or_none()
                    
                    if not task or task.status not in [TaskStatus.pending]:
                        # 任务已被取消或状态异常，从队列中移除
                        await redis.zrem(self.QUEUE_KEY, item_json)
                        continue
                    
                    # 获取用户信息
                    user_result = await db.execute(
                        select(User).where(User.id == queue_task.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    
                    if not user:
                        # 用户不存在，从队列中移除
                        await redis.zrem(self.QUEUE_KEY, item_json)
                        continue
                    
                    # 从队列中移除并添加到运行列表
                    await redis.zrem(self.QUEUE_KEY, item_json)
                    await redis.sadd(self.RUNNING_KEY, json.dumps({
                        "task_id": queue_task.task_id,
                        "user_id": queue_task.user_id,
                        "started_at": datetime.utcnow().isoformat()
                    }))
                    
                    # 启动审计分析
                    success = await AuditService.start_audit_analysis(
                        task_id=queue_task.task_id,
                        project_path=queue_task.project_path,
                        user=user,
                        db=db
                    )
                    
                    if success:
                        started_count += 1
                        
                        # 设置任务完成时的清理回调
                        asyncio.create_task(
                            self._monitor_task_completion(queue_task.task_id, db)
                        )
                    else:
                        # 启动失败，从运行列表中移除
                        await self._remove_from_running(queue_task.task_id)
                
                except Exception as e:
                    # 处理异常，移除有问题的任务
                    await redis.zrem(self.QUEUE_KEY, item_json)
                    print(f"处理队列任务时出错: {e}")
            
            # 更新统计信息
            await self._update_queue_stats()
            
        except Exception as e:
            print(f"处理队列时出错: {e}")
        
        return started_count
    
    async def _monitor_task_completion(self, task_id: int, db: AsyncSession):
        """监控任务完成状态"""
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒检查一次
                
                # 查询任务状态
                result = await db.execute(
                    select(AuditTask).where(AuditTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    break
                
                if task.status in [TaskStatus.completed, TaskStatus.failed, TaskStatus.cancelled]:
                    # 任务完成，从运行列表中移除
                    await self._remove_from_running(task_id)
                    
                    # 处理队列中的下一个任务
                    await self.process_queue(db)
                    break
                    
            except Exception as e:
                print(f"监控任务 {task_id} 完成状态时出错: {e}")
                await asyncio.sleep(30)  # 出错时等待更长时间
    
    async def _remove_from_running(self, task_id: int):
        """从运行列表中移除任务"""
        redis = await self.get_redis()
        
        # 获取所有运行中的任务
        running_tasks = await redis.smembers(self.RUNNING_KEY)
        
        for task_json in running_tasks:
            try:
                task_data = json.loads(task_json)
                if task_data.get('task_id') == task_id:
                    await redis.srem(self.RUNNING_KEY, task_json)
                    break
            except json.JSONDecodeError:
                continue
    
    async def cancel_queued_task(self, task_id: int, db: AsyncSession) -> bool:
        """取消队列中的任务"""
        redis = await self.get_redis()
        
        # 从队列中查找并移除任务
        queue_items = await redis.zrange(self.QUEUE_KEY, 0, -1)
        
        for item_json in queue_items:
            try:
                queue_task = QueueTask.from_dict(json.loads(item_json))
                if queue_task.task_id == task_id:
                    await redis.zrem(self.QUEUE_KEY, item_json)
                    
                    # 更新数据库任务状态
                    await db.execute(
                        update(AuditTask)
                        .where(AuditTask.id == task_id)
                        .values(
                            status=TaskStatus.cancelled,
                            completed_at=datetime.utcnow(),
                            error_message="任务已被用户取消"
                        )
                    )
                    await db.commit()
                    
                    return True
            except json.JSONDecodeError:
                continue
        
        return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        redis = await self.get_redis()
        
        # 获取队列中的任务
        queue_count = await redis.zcard(self.QUEUE_KEY)
        running_count = await redis.scard(self.RUNNING_KEY)
        
        # 获取队列中的任务详情
        queue_items = await redis.zrevrange(self.QUEUE_KEY, 0, 9, withscores=True)  # 前10个
        queue_tasks = []
        
        for item_json, priority in queue_items:
            try:
                task_data = json.loads(item_json)
                queue_tasks.append({
                    "task_id": task_data.get('task_id'),
                    "user_id": task_data.get('user_id'),
                    "user_level": task_data.get('user_level'),
                    "priority": -int(priority),  # 转换回正数
                    "created_at": task_data.get('created_at'),
                    "position": len(queue_tasks) + 1
                })
            except (json.JSONDecodeError, ValueError):
                continue
        
        return {
            "queue_length": queue_count,
            "running_count": running_count,
            "available_slots": max(0, self.MAX_CONCURRENT_TASKS - running_count),
            "max_concurrent": self.MAX_CONCURRENT_TASKS,
            "queue_tasks": queue_tasks
        }
    
    async def get_user_queue_info(self, user_id: int) -> Dict[str, Any]:
        """获取用户的队列信息"""
        redis = await self.get_redis()
        
        # 检查是否在运行中
        running_tasks = await redis.smembers(self.RUNNING_KEY)
        for task_json in running_tasks:
            try:
                task_data = json.loads(task_json)
                if task_data.get('user_id') == user_id:
                    return {
                        "status": "running",
                        "task_id": task_data.get('task_id'),
                        "started_at": task_data.get('started_at'),
                        "message": "任务正在执行中"
                    }
            except json.JSONDecodeError:
                continue
        
        # 检查是否在队列中
        queue_items = await redis.zrevrange(self.QUEUE_KEY, 0, -1, withscores=True)
        for index, (item_json, priority) in enumerate(queue_items):
            try:
                task_data = json.loads(item_json)
                if task_data.get('user_id') == user_id:
                    position = index + 1
                    wait_time = await self.estimate_wait_time(position)
                    
                    return {
                        "status": "queued",
                        "task_id": task_data.get('task_id'),
                        "position": position,
                        "priority": -int(priority),
                        "estimated_wait_time": wait_time,
                        "message": f"排队中，当前第 {position} 位，预计等待 {wait_time//60} 分钟"
                    }
            except (json.JSONDecodeError, ValueError):
                continue
        
        return {
            "status": "none",
            "message": "当前没有排队或运行中的任务"
        }
    
    async def _update_queue_stats(self):
        """更新队列统计信息"""
        redis = await self.get_redis()
        
        stats = {
            "last_updated": datetime.utcnow().isoformat(),
            "queue_length": await redis.zcard(self.QUEUE_KEY),
            "running_count": await redis.scard(self.RUNNING_KEY),
            "max_concurrent": self.MAX_CONCURRENT_TASKS
        }
        
        await redis.set(self.STATS_KEY, json.dumps(stats), ex=3600)  # 1小时过期


# 全局队列服务实例
task_queue_service = TaskQueueService()
