"""
并发控制和熔断机制管理器
"""
import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5      # 失败阈值
    recovery_timeout: float = 60.0  # 恢复超时时间
    success_threshold: int = 3      # 半开状态成功阈值


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        
    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # 检查是否可以进入半开状态
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker entering HALF_OPEN state")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """记录成功"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker entering CLOSED state")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker entering OPEN state after {self.failure_count} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker returning to OPEN state")


class AdaptiveConcurrencyManager:
    """自适应并发管理器"""
    
    def __init__(self, initial_concurrency: int = 15, min_concurrency: int = 5, max_concurrency: int = 25):
        self.current_concurrency = initial_concurrency
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(initial_concurrency)
        
        # 性能统计
        self.success_count = 0
        self.error_count = 0
        self.total_requests = 0
        self.last_adjustment_time = time.time()
        self.adjustment_interval = 30.0  # 30秒调整一次
        
        # 熔断器
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig())
        
        logger.info(f"Initialized adaptive concurrency manager with {initial_concurrency} concurrent requests")
    
    async def acquire(self):
        """获取并发许可"""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - too many failures")
        
        await self.semaphore.acquire()
        self.total_requests += 1
    
    def release(self, success: bool = True):
        """释放并发许可"""
        self.semaphore.release()
        
        if success:
            self.success_count += 1
            self.circuit_breaker.record_success()
        else:
            self.error_count += 1
            self.circuit_breaker.record_failure()
        
        # 定期调整并发数
        self._maybe_adjust_concurrency()
    
    def _maybe_adjust_concurrency(self):
        """可能调整并发数"""
        now = time.time()
        if now - self.last_adjustment_time < self.adjustment_interval:
            return
        
        if self.total_requests < 10:  # 样本太少
            return
        
        error_rate = self.error_count / self.total_requests
        
        # 调整策略 - 基于TPM限制优化
        if error_rate > 0.15:  # 错误率超过15%，降低并发
            new_concurrency = max(self.min_concurrency, int(self.current_concurrency * 0.7))
        elif error_rate < 0.03:  # 错误率低于3%，可以增加并发
            new_concurrency = min(self.max_concurrency, int(self.current_concurrency * 1.3))
        else:
            new_concurrency = self.current_concurrency
        
        if new_concurrency != self.current_concurrency:
            logger.info(f"Adjusting concurrency from {self.current_concurrency} to {new_concurrency} "
                       f"(error rate: {error_rate:.2%})")
            self._update_concurrency(new_concurrency)
        
        # 重置统计
        self.success_count = 0
        self.error_count = 0
        self.total_requests = 0
        self.last_adjustment_time = now
    
    def _update_concurrency(self, new_concurrency: int):
        """更新并发数"""
        old_concurrency = self.current_concurrency
        self.current_concurrency = new_concurrency
        
        # 创建新的信号量
        # 注意：这里需要小心处理，确保不会丢失已获取的许可
        current_permits = old_concurrency - self.semaphore._value
        self.semaphore = asyncio.Semaphore(new_concurrency - current_permits)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "current_concurrency": self.current_concurrency,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.total_requests)
        }


class ConcurrencyContext:
    """并发控制上下文管理器"""
    
    def __init__(self, manager: AdaptiveConcurrencyManager):
        self.manager = manager
        self.success = False
    
    async def __aenter__(self):
        await self.manager.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.success = exc_type is None
        self.manager.release(self.success)
        return False  # 不抑制异常
