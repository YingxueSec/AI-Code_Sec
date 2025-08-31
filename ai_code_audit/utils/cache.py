#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能缓存机制 - 基于文件内容哈希的LLM响应缓存
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any


class LLMCache:
    """LLM响应缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存有效期（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600
        
    def _get_cache_key(self, code: str, template: str, language: str) -> str:
        """生成缓存键"""
        content = f"{code}|{template}|{language}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, code: str, template: str, language: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的LLM响应
        
        Args:
            code: 代码内容
            template: 模板名称
            language: 编程语言
            
        Returns:
            缓存的响应或None
        """
        try:
            cache_key = self._get_cache_key(code, template, language)
            cache_file = self._get_cache_file(cache_key)
            
            if not cache_file.exists():
                return None
            
            # 检查缓存是否过期
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.ttl_seconds:
                cache_file.unlink()  # 删除过期缓存
                return None
            
            # 读取缓存内容
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            return cached_data
            
        except Exception:
            return None
    
    def set(self, code: str, template: str, language: str, response: Dict[str, Any]) -> bool:
        """
        保存LLM响应到缓存
        
        Args:
            code: 代码内容
            template: 模板名称
            language: 编程语言
            response: LLM响应
            
        Returns:
            是否保存成功
        """
        try:
            cache_key = self._get_cache_key(code, template, language)
            cache_file = self._get_cache_file(cache_key)
            
            # 添加缓存元数据
            cached_data = {
                'response': response,
                'cached_at': time.time(),
                'template': template,
                'language': language,
                'code_hash': hashlib.md5(code.encode('utf-8')).hexdigest()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception:
            return False
    
    def clear_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的文件数量
        """
        cleared_count = 0
        try:
            current_time = time.time()
            for cache_file in self.cache_dir.glob("*.json"):
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > self.ttl_seconds:
                    cache_file.unlink()
                    cleared_count += 1
        except Exception:
            pass
        
        return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计数据
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_files = len(cache_files)
            total_size = sum(f.stat().st_size for f in cache_files)
            
            # 计算过期文件数
            current_time = time.time()
            expired_files = 0
            for cache_file in cache_files:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > self.ttl_seconds:
                    expired_files += 1
            
            return {
                'total_files': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'expired_files': expired_files,
                'valid_files': total_files - expired_files,
                'cache_dir': str(self.cache_dir),
                'ttl_hours': self.ttl_seconds / 3600
            }
            
        except Exception:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'expired_files': 0,
                'valid_files': 0,
                'cache_dir': str(self.cache_dir),
                'ttl_hours': self.ttl_seconds / 3600
            }


# 全局缓存实例
_global_cache = None

def get_cache() -> LLMCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LLMCache()
    return _global_cache


def clear_cache():
    """清理全局缓存"""
    global _global_cache
    if _global_cache:
        cleared = _global_cache.clear_expired()
        return cleared
    return 0
