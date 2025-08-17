"""
Cache optimization system for AI Code Audit System.

This module provides advanced caching capabilities including:
- Analysis result caching with intelligent invalidation
- Incremental analysis support
- File change detection and cache management
- Performance optimization for repeated audits
"""

import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Types of cached data."""
    ANALYSIS_RESULT = "analysis_result"
    FILE_HASH = "file_hash"
    DEPENDENCY_GRAPH = "dependency_graph"
    SYMBOL_INDEX = "symbol_index"
    CONTEXT_DATA = "context_data"


class CacheStatus(Enum):
    """Cache entry status."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    MISSING = "missing"


@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    cache_type: CacheType
    data: Any
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    file_dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def touch(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()


@dataclass
class CacheStats:
    """Cache statistics."""
    total_entries: int = 0
    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class CacheManager:
    """Intelligent cache management system."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 500):
        """Initialize cache manager."""
        self.cache_dir = Path(cache_dir or ".ai_audit_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.file_hashes: Dict[str, str] = {}
        self.stats = CacheStats()
        
        # Load existing cache
        self._load_cache_index()
        self._load_file_hashes()
    
    def _load_cache_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                
                for entry_data in index_data.get('entries', []):
                    entry = CacheEntry(
                        key=entry_data['key'],
                        cache_type=CacheType(entry_data['cache_type']),
                        data=None,  # Will be loaded on demand
                        created_at=datetime.fromisoformat(entry_data['created_at']),
                        last_accessed=datetime.fromisoformat(entry_data['last_accessed']),
                        expires_at=datetime.fromisoformat(entry_data['expires_at']) if entry_data.get('expires_at') else None,
                        file_dependencies=set(entry_data.get('file_dependencies', [])),
                        metadata=entry_data.get('metadata', {})
                    )
                    self.memory_cache[entry.key] = entry
                
                self.stats = CacheStats(**index_data.get('stats', {}))
                logger.info(f"Loaded cache index with {len(self.memory_cache)} entries")
                
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.json"
        
        try:
            entries_data = []
            for entry in self.memory_cache.values():
                entry_data = {
                    'key': entry.key,
                    'cache_type': entry.cache_type.value,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                    'file_dependencies': list(entry.file_dependencies),
                    'metadata': entry.metadata
                }
                entries_data.append(entry_data)
            
            index_data = {
                'entries': entries_data,
                'stats': asdict(self.stats)
            }
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _load_file_hashes(self):
        """Load file hashes for change detection."""
        hash_file = self.cache_dir / "file_hashes.json"
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.file_hashes = json.load(f)
                logger.info(f"Loaded {len(self.file_hashes)} file hashes")
            except Exception as e:
                logger.warning(f"Failed to load file hashes: {e}")
    
    def _save_file_hashes(self):
        """Save file hashes to disk."""
        hash_file = self.cache_dir / "file_hashes.json"
        try:
            with open(hash_file, 'w') as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save file hashes: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file content."""
        try:
            path = Path(file_path)
            if path.exists():
                content = path.read_bytes()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
        return ""
    
    def _generate_cache_key(self, cache_type: CacheType, identifier: str, context: Optional[Dict] = None) -> str:
        """Generate cache key."""
        key_parts = [cache_type.value, identifier]
        
        if context:
            # Sort context for consistent keys
            context_str = json.dumps(context, sort_keys=True)
            context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
            key_parts.append(context_hash)
        
        return ":".join(key_parts)
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        # Use first 2 chars for subdirectory to avoid too many files in one dir
        subdir = cache_key[:2]
        cache_subdir = self.cache_dir / subdir
        cache_subdir.mkdir(exist_ok=True)
        return cache_subdir / f"{cache_key}.cache"
    
    def _load_cache_data(self, entry: CacheEntry) -> Any:
        """Load cache data from disk."""
        if entry.data is not None:
            return entry.data
        
        cache_file = self._get_cache_file_path(entry.key)
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    entry.data = pickle.load(f)
                return entry.data
            except Exception as e:
                logger.warning(f"Failed to load cache data for {entry.key}: {e}")
        
        return None
    
    def _save_cache_data(self, entry: CacheEntry):
        """Save cache data to disk."""
        cache_file = self._get_cache_file_path(entry.key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(entry.data, f)
        except Exception as e:
            logger.error(f"Failed to save cache data for {entry.key}: {e}")
    
    def get(self, cache_type: CacheType, identifier: str, context: Optional[Dict] = None) -> Optional[Any]:
        """Get item from cache."""
        cache_key = self._generate_cache_key(cache_type, identifier, context)
        
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # Check if entry is valid
            if self._is_entry_valid(entry):
                entry.touch()
                data = self._load_cache_data(entry)
                if data is not None:
                    self.stats.hits += 1
                    logger.debug(f"Cache hit for {cache_key}")
                    return data
            else:
                # Entry is invalid, remove it
                self._remove_entry(cache_key)
        
        self.stats.misses += 1
        logger.debug(f"Cache miss for {cache_key}")
        return None
    
    def put(
        self,
        cache_type: CacheType,
        identifier: str,
        data: Any,
        context: Optional[Dict] = None,
        file_dependencies: Optional[Set[str]] = None,
        ttl_hours: Optional[int] = None
    ) -> str:
        """Put item in cache."""
        cache_key = self._generate_cache_key(cache_type, identifier, context)
        
        # Calculate expiration
        expires_at = None
        if ttl_hours:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            cache_type=cache_type,
            data=data,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            expires_at=expires_at,
            file_dependencies=file_dependencies or set(),
            metadata={'identifier': identifier}
        )
        
        # Save to memory and disk
        self.memory_cache[cache_key] = entry
        self._save_cache_data(entry)
        
        # Update file hashes for dependencies
        if file_dependencies:
            for file_path in file_dependencies:
                self.file_hashes[file_path] = self._calculate_file_hash(file_path)
        
        self.stats.total_entries = len(self.memory_cache)
        
        # Cleanup if needed
        self._cleanup_if_needed()
        
        logger.debug(f"Cached {cache_key} with {len(file_dependencies or [])} dependencies")
        return cache_key
    
    def invalidate(self, cache_type: Optional[CacheType] = None, identifier: Optional[str] = None):
        """Invalidate cache entries."""
        keys_to_remove = []
        
        for key, entry in self.memory_cache.items():
            should_remove = False
            
            if cache_type and entry.cache_type == cache_type:
                should_remove = True
            
            if identifier and entry.metadata.get('identifier') == identifier:
                should_remove = True
            
            if should_remove:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
        
        self.stats.invalidations += len(keys_to_remove)
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    
    def invalidate_by_file_changes(self, changed_files: Set[str]):
        """Invalidate cache entries affected by file changes."""
        keys_to_remove = []
        
        for key, entry in self.memory_cache.items():
            # Check if any dependencies have changed
            for dep_file in entry.file_dependencies:
                if dep_file in changed_files:
                    keys_to_remove.append(key)
                    break
                
                # Check if file hash has changed
                current_hash = self._calculate_file_hash(dep_file)
                if current_hash != self.file_hashes.get(dep_file, ""):
                    keys_to_remove.append(key)
                    break
        
        for key in keys_to_remove:
            self._remove_entry(key)
        
        # Update file hashes
        for file_path in changed_files:
            self.file_hashes[file_path] = self._calculate_file_hash(file_path)
        
        self.stats.invalidations += len(keys_to_remove)
        logger.info(f"Invalidated {len(keys_to_remove)} entries due to file changes")
    
    def _is_entry_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is valid."""
        # Check expiration
        if entry.is_expired:
            return False
        
        # Check file dependencies
        for dep_file in entry.file_dependencies:
            current_hash = self._calculate_file_hash(dep_file)
            if current_hash != self.file_hashes.get(dep_file, ""):
                return False
        
        return True
    
    def _remove_entry(self, cache_key: str):
        """Remove cache entry."""
        if cache_key in self.memory_cache:
            # Remove from memory
            del self.memory_cache[cache_key]
            
            # Remove cache file
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")
    
    def _cleanup_if_needed(self):
        """Cleanup cache if it exceeds size limits."""
        # Calculate current size (approximate)
        current_size = 0
        for entry in self.memory_cache.values():
            cache_file = self._get_cache_file_path(entry.key)
            if cache_file.exists():
                current_size += cache_file.stat().st_size
        
        self.stats.size_bytes = current_size
        
        if current_size > self.max_size_bytes:
            # Remove oldest entries first
            entries_by_age = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            removed_count = 0
            for key, entry in entries_by_age:
                self._remove_entry(key)
                removed_count += 1
                
                # Recalculate size
                current_size = sum(
                    self._get_cache_file_path(e.key).stat().st_size
                    for e in self.memory_cache.values()
                    if self._get_cache_file_path(e.key).exists()
                )
                
                if current_size <= self.max_size_bytes * 0.8:  # Leave some headroom
                    break
            
            logger.info(f"Cleaned up {removed_count} cache entries to reduce size")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        # Update current stats
        self.stats.total_entries = len(self.memory_cache)
        
        current_size = 0
        for entry in self.memory_cache.values():
            cache_file = self._get_cache_file_path(entry.key)
            if cache_file.exists():
                current_size += cache_file.stat().st_size
        
        self.stats.size_bytes = current_size
        return self.stats
    
    def clear(self):
        """Clear all cache."""
        # Remove all cache files
        for entry in self.memory_cache.values():
            cache_file = self._get_cache_file_path(entry.key)
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        # Clear memory cache
        self.memory_cache.clear()
        self.file_hashes.clear()
        
        # Reset stats
        self.stats = CacheStats()
        
        logger.info("Cleared all cache")
    
    def save(self):
        """Save cache state to disk."""
        self._save_cache_index()
        self._save_file_hashes()
        logger.info("Saved cache state to disk")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.save()
