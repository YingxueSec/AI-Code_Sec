"""
TPM/RPM 限制管理器
"""
import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """限流配置"""
    rpm: int = 10000      # 每分钟请求数
    tpm: int = 400000     # 每分钟Token数
    window_size: int = 60  # 时间窗口大小(秒)


class TokenBucket:
    """Token桶算法实现"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化Token桶
        
        Args:
            capacity: 桶容量
            refill_rate: 每秒补充速率
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int) -> bool:
        """
        尝试消费tokens
        
        Args:
            tokens: 需要消费的token数量
            
        Returns:
            是否成功消费
        """
        async with self._lock:
            now = time.time()
            # 补充tokens
            time_passed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self, tokens: int) -> float:
        """获取需要等待的时间"""
        if self.tokens >= tokens:
            return 0.0
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


class SlidingWindowRateLimiter:
    """滑动窗口限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times = deque()
        self.token_usage = deque()  # (timestamp, token_count)
        self._lock = asyncio.Lock()
        
        # Token桶限流器
        self.rpm_bucket = TokenBucket(
            capacity=config.rpm,
            refill_rate=config.rpm / 60.0  # 每秒补充速率
        )
        self.tpm_bucket = TokenBucket(
            capacity=config.tpm,
            refill_rate=config.tpm / 60.0  # 每秒补充速率
        )
    
    async def acquire(self, estimated_tokens: int = 5000) -> bool:
        """
        获取请求许可
        
        Args:
            estimated_tokens: 预估的token使用量
            
        Returns:
            是否获得许可
        """
        async with self._lock:
            now = time.time()
            
            # 清理过期记录
            self._cleanup_old_records(now)
            
            # 检查RPM限制
            if not await self.rpm_bucket.consume(1):
                logger.warning("RPM limit reached")
                return False
            
            # 检查TPM限制
            if not await self.tpm_bucket.consume(estimated_tokens):
                logger.warning(f"TPM limit reached, estimated tokens: {estimated_tokens}")
                return False
            
            # 记录请求
            self.request_times.append(now)
            self.token_usage.append((now, estimated_tokens))
            
            return True
    
    async def get_wait_time(self, estimated_tokens: int = 5000) -> float:
        """获取需要等待的时间"""
        rpm_wait = self.rpm_bucket.get_wait_time(1)
        tpm_wait = self.tpm_bucket.get_wait_time(estimated_tokens)
        return max(rpm_wait, tpm_wait)
    
    def _cleanup_old_records(self, now: float):
        """清理过期记录"""
        cutoff = now - self.config.window_size
        
        # 清理请求时间记录
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()
        
        # 清理token使用记录
        while self.token_usage and self.token_usage[0][0] < cutoff:
            self.token_usage.popleft()
    
    def get_current_usage(self) -> Dict:
        """获取当前使用情况"""
        now = time.time()
        self._cleanup_old_records(now)
        
        current_requests = len(self.request_times)
        current_tokens = sum(tokens for _, tokens in self.token_usage)
        
        return {
            "current_rpm": current_requests,
            "max_rpm": self.config.rpm,
            "rpm_usage_percent": (current_requests / self.config.rpm) * 100,
            "current_tpm": current_tokens,
            "max_tpm": self.config.tpm,
            "tpm_usage_percent": (current_tokens / self.config.tpm) * 100,
            "available_tokens": self.tpm_bucket.tokens,
            "available_requests": self.rpm_bucket.tokens
        }


class AdaptiveRateLimiter:
    """自适应限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.base_limiter = SlidingWindowRateLimiter(config)
        self.config = config
        
        # 自适应参数
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 30.0  # 30秒调整一次
        
        # 动态token估算
        self.token_history = deque(maxlen=100)  # 保留最近100次的实际token使用
        self.default_token_estimate = 5000
    
    async def acquire_with_estimation(self, content_length: int = 0) -> bool:
        """
        基于内容长度估算token并获取许可
        
        Args:
            content_length: 内容长度(字符数)
            
        Returns:
            是否获得许可
        """
        estimated_tokens = self._estimate_tokens(content_length)
        
        # 检查是否需要等待
        wait_time = await self.base_limiter.get_wait_time(estimated_tokens)
        if wait_time > 0:
            logger.info(f"Rate limit reached, waiting {wait_time:.2f}s for {estimated_tokens} tokens")
            await asyncio.sleep(wait_time)
        
        return await self.base_limiter.acquire(estimated_tokens)
    
    def _estimate_tokens(self, content_length: int) -> int:
        """估算token数量"""
        if not self.token_history:
            # 没有历史数据，使用默认估算
            if content_length > 0:
                # 粗略估算: 1个token约等于4个字符(中文)或0.75个单词(英文)
                return max(int(content_length * 0.3), 1000)
            return self.default_token_estimate
        
        # 基于历史数据的动态估算
        avg_tokens = sum(self.token_history) / len(self.token_history)
        
        if content_length > 0:
            # 根据内容长度调整
            length_factor = content_length / 10000  # 假设10k字符为基准
            estimated = int(avg_tokens * max(0.5, min(2.0, length_factor)))
        else:
            estimated = int(avg_tokens)
        
        return max(estimated, 1000)  # 最少1000 tokens
    
    def record_actual_usage(self, actual_tokens: int):
        """记录实际token使用量"""
        self.token_history.append(actual_tokens)
        self.success_count += 1
        
        # 更新默认估算
        if len(self.token_history) >= 10:
            self.default_token_estimate = int(sum(self.token_history) / len(self.token_history))
    
    def record_error(self):
        """记录错误"""
        self.error_count += 1
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        base_stats = self.base_limiter.get_current_usage()
        
        # 添加自适应统计
        total_requests = self.success_count + self.error_count
        error_rate = self.error_count / max(1, total_requests)
        
        avg_tokens = 0
        if self.token_history:
            avg_tokens = sum(self.token_history) / len(self.token_history)
        
        base_stats.update({
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_actual_tokens": avg_tokens,
            "current_token_estimate": self.default_token_estimate,
            "token_history_size": len(self.token_history)
        })
        
        return base_stats


# 全局限流器实例
_global_rate_limiter: Optional[AdaptiveRateLimiter] = None


def get_rate_limiter() -> AdaptiveRateLimiter:
    """获取全局限流器实例"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        config = RateLimitConfig(
            rpm=10000,    # Kimi-K2 RPM限制
            tpm=400000    # Kimi-K2 TPM限制
        )
        _global_rate_limiter = AdaptiveRateLimiter(config)
    return _global_rate_limiter
