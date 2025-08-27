#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
递归监控器
用于检测和防止分析过程中的无限递归调用
"""

import threading
import logging
from typing import Set, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """分析类型枚举"""
    MAIN_ANALYSIS = "main_analysis"
    CROSS_FILE = "cross_file"
    RELATED_FILE = "related_file"
    CONFIDENCE_CALC = "confidence_calc"


class RecursionMonitor:
    """递归监控器"""
    
    def __init__(self, max_depth: int = 50):
        """
        初始化递归监控器
        
        Args:
            max_depth: 最大允许的调用深度，远低于Python默认的1000
        """
        self.max_depth = max_depth
        self.call_stack = threading.local()
        
    def enter_analysis(self, file_path: str, analysis_type: AnalysisType) -> None:
        """
        进入分析
        
        Args:
            file_path: 文件路径
            analysis_type: 分析类型
            
        Raises:
            RecursionError: 如果检测到循环调用或深度超限
        """
        if not hasattr(self.call_stack, 'stack'):
            self.call_stack.stack = []
        
        call_info = f"{analysis_type.value}:{file_path}"
        
        # 检查是否已经在分析同一个文件的同一类型
        if call_info in self.call_stack.stack:
            logger.error(f"Circular analysis detected: {call_info}")
            logger.error(f"Current stack: {self.call_stack.stack}")
            raise RecursionError(f"Circular analysis detected: {call_info}")
        
        # 检查调用深度
        if len(self.call_stack.stack) >= self.max_depth:
            logger.error(f"Analysis depth exceeded: {len(self.call_stack.stack)} >= {self.max_depth}")
            logger.error(f"Current stack: {self.call_stack.stack}")
            raise RecursionError(f"Analysis depth exceeded: {len(self.call_stack.stack)}")
        
        self.call_stack.stack.append(call_info)
        logger.debug(f"Entered analysis: {call_info} (depth: {len(self.call_stack.stack)})")
        
    def exit_analysis(self, file_path: str, analysis_type: AnalysisType) -> None:
        """
        退出分析
        
        Args:
            file_path: 文件路径
            analysis_type: 分析类型
        """
        if not hasattr(self.call_stack, 'stack') or not self.call_stack.stack:
            logger.warning(f"Attempted to exit analysis but stack is empty: {analysis_type.value}:{file_path}")
            return
            
        call_info = f"{analysis_type.value}:{file_path}"
        
        if self.call_stack.stack and self.call_stack.stack[-1] == call_info:
            self.call_stack.stack.pop()
            logger.debug(f"Exited analysis: {call_info} (depth: {len(self.call_stack.stack)})")
        else:
            logger.warning(f"Stack mismatch when exiting: expected {call_info}, got {self.call_stack.stack[-1] if self.call_stack.stack else 'empty'}")
    
    def get_current_depth(self) -> int:
        """获取当前调用深度"""
        if not hasattr(self.call_stack, 'stack'):
            return 0
        return len(self.call_stack.stack)
    
    def get_current_stack(self) -> List[str]:
        """获取当前调用栈"""
        if not hasattr(self.call_stack, 'stack'):
            return []
        return self.call_stack.stack.copy()
    
    def is_analyzing_file(self, file_path: str, analysis_type: Optional[AnalysisType] = None) -> bool:
        """
        检查是否正在分析指定文件
        
        Args:
            file_path: 文件路径
            analysis_type: 分析类型，如果为None则检查任何类型
            
        Returns:
            bool: 如果正在分析则返回True
        """
        if not hasattr(self.call_stack, 'stack'):
            return False
        
        if analysis_type is None:
            # 检查任何类型的分析
            return any(file_path in call for call in self.call_stack.stack)
        else:
            # 检查特定类型的分析
            call_info = f"{analysis_type.value}:{file_path}"
            return call_info in self.call_stack.stack


# 全局递归监控器实例
recursion_monitor = RecursionMonitor()


def get_recursion_monitor() -> RecursionMonitor:
    """获取全局递归监控器实例"""
    return recursion_monitor


class RecursionGuard:
    """递归保护上下文管理器"""
    
    def __init__(self, file_path: str, analysis_type: AnalysisType, monitor: Optional[RecursionMonitor] = None):
        self.file_path = file_path
        self.analysis_type = analysis_type
        self.monitor = monitor or get_recursion_monitor()
        
    async def __aenter__(self):
        """异步进入上下文"""
        self.monitor.enter_analysis(self.file_path, self.analysis_type)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步退出上下文"""
        self.monitor.exit_analysis(self.file_path, self.analysis_type)
        
    def __enter__(self):
        """同步进入上下文"""
        self.monitor.enter_analysis(self.file_path, self.analysis_type)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步退出上下文"""
        self.monitor.exit_analysis(self.file_path, self.analysis_type)
