"""
Session isolation system for AI Code Audit System.

This module provides comprehensive session isolation including:
- Independent session contexts
- Resource isolation boundaries
- Shared resource management
- Session lifecycle management
"""

import asyncio
import threading
import weakref
from typing import Dict, List, Optional, Set, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import os
import tempfile
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class IsolationLevel(Enum):
    """Levels of session isolation."""
    STRICT = "strict"      # Complete isolation, no shared resources
    MODERATE = "moderate"  # Shared read-only resources, isolated write operations
    RELAXED = "relaxed"    # Shared resources with synchronization


class ResourceType(Enum):
    """Types of resources that can be isolated."""
    MEMORY = "memory"
    CACHE = "cache"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    NETWORK = "network"
    TEMPORARY_FILES = "temporary_files"


@dataclass
class SessionContext:
    """Isolated context for a session."""
    session_id: str
    isolation_level: IsolationLevel
    created_at: datetime = field(default_factory=datetime.now)
    
    # Resource isolation
    memory_namespace: str = ""
    cache_namespace: str = ""
    temp_directory: Optional[Path] = None
    
    # Resource limits
    max_memory_mb: int = 1024
    max_cache_size_mb: int = 256
    max_temp_files: int = 1000
    max_execution_time_seconds: int = 3600
    
    # Shared resource access
    shared_resources: Set[str] = field(default_factory=set)
    resource_locks: Dict[str, threading.Lock] = field(default_factory=dict)
    
    # Session state
    is_active: bool = True
    is_suspended: bool = False
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Cleanup callbacks
    cleanup_callbacks: List[Callable] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceBoundary:
    """Defines isolation boundaries for resources."""
    resource_type: ResourceType
    isolation_level: IsolationLevel
    namespace_prefix: str
    max_size_mb: Optional[int] = None
    max_items: Optional[int] = None
    ttl_seconds: Optional[int] = None
    access_permissions: Set[str] = field(default_factory=lambda: {"read", "write"})
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedResource:
    """Represents a shared resource with access control."""
    resource_id: str
    resource_type: ResourceType
    data: Any
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    access_permissions: Dict[str, Set[str]] = field(default_factory=dict)  # session_id -> permissions
    lock: threading.RLock = field(default_factory=threading.RLock)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionIsolationManager:
    """Comprehensive session isolation management system."""
    
    def __init__(self, default_isolation_level: IsolationLevel = IsolationLevel.MODERATE):
        """Initialize session isolation manager."""
        self.default_isolation_level = default_isolation_level
        
        # Session management
        self.active_sessions: Dict[str, SessionContext] = {}
        self.suspended_sessions: Dict[str, SessionContext] = {}
        self.session_locks: Dict[str, threading.RLock] = {}
        
        # Resource management
        self.shared_resources: Dict[str, SharedResource] = {}
        self.resource_boundaries: Dict[ResourceType, ResourceBoundary] = {}
        self.global_resource_lock = threading.RLock()
        
        # Cleanup management
        self.cleanup_tasks: Set[asyncio.Task] = set()
        self.cleanup_interval = 300  # 5 minutes
        
        # Initialize default resource boundaries
        self._initialize_default_boundaries()
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    def _initialize_default_boundaries(self):
        """Initialize default resource boundaries."""
        self.resource_boundaries = {
            ResourceType.MEMORY: ResourceBoundary(
                resource_type=ResourceType.MEMORY,
                isolation_level=self.default_isolation_level,
                namespace_prefix="session_memory",
                max_size_mb=1024,
                ttl_seconds=3600
            ),
            ResourceType.CACHE: ResourceBoundary(
                resource_type=ResourceType.CACHE,
                isolation_level=self.default_isolation_level,
                namespace_prefix="session_cache",
                max_size_mb=256,
                max_items=10000,
                ttl_seconds=1800
            ),
            ResourceType.FILE_SYSTEM: ResourceBoundary(
                resource_type=ResourceType.FILE_SYSTEM,
                isolation_level=IsolationLevel.STRICT,  # Always strict for file system
                namespace_prefix="session_files",
                max_size_mb=512,
                max_items=1000
            ),
            ResourceType.TEMPORARY_FILES: ResourceBoundary(
                resource_type=ResourceType.TEMPORARY_FILES,
                isolation_level=IsolationLevel.STRICT,
                namespace_prefix="session_temp",
                max_size_mb=256,
                max_items=500,
                ttl_seconds=7200
            )
        }
    
    async def create_session(self, session_id: str, 
                           isolation_level: Optional[IsolationLevel] = None,
                           **kwargs) -> SessionContext:
        """Create a new isolated session."""
        if session_id in self.active_sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        isolation_level = isolation_level or self.default_isolation_level
        
        # Create session context
        context = SessionContext(
            session_id=session_id,
            isolation_level=isolation_level,
            **kwargs
        )
        
        # Initialize resource isolation
        await self._initialize_session_resources(context)
        
        # Register session
        self.active_sessions[session_id] = context
        self.session_locks[session_id] = threading.RLock()
        
        logger.info(f"Created isolated session {session_id} with {isolation_level.value} isolation")
        return context
    
    async def _initialize_session_resources(self, context: SessionContext):
        """Initialize isolated resources for a session."""
        session_id = context.session_id
        
        # Initialize memory namespace
        context.memory_namespace = f"session_{session_id}_memory"
        
        # Initialize cache namespace
        context.cache_namespace = f"session_{session_id}_cache"
        
        # Initialize temporary directory
        if context.isolation_level in [IsolationLevel.STRICT, IsolationLevel.MODERATE]:
            temp_base = tempfile.gettempdir()
            context.temp_directory = Path(temp_base) / f"ai_audit_session_{session_id}"
            context.temp_directory.mkdir(parents=True, exist_ok=True)
            
            # Add cleanup callback for temp directory
            context.cleanup_callbacks.append(
                lambda: shutil.rmtree(context.temp_directory, ignore_errors=True)
            )
        
        # Initialize resource locks
        for resource_type in ResourceType:
            lock_key = f"{session_id}_{resource_type.value}"
            context.resource_locks[lock_key] = threading.Lock()
    
    async def suspend_session(self, session_id: str) -> bool:
        """Suspend a session, preserving its state."""
        if session_id not in self.active_sessions:
            return False
        
        with self.session_locks[session_id]:
            context = self.active_sessions[session_id]
            context.is_suspended = True
            context.is_active = False
            
            # Move to suspended sessions
            self.suspended_sessions[session_id] = context
            del self.active_sessions[session_id]
            
            logger.info(f"Suspended session {session_id}")
            return True
    
    async def resume_session(self, session_id: str) -> bool:
        """Resume a suspended session."""
        if session_id not in self.suspended_sessions:
            return False
        
        with self.session_locks[session_id]:
            context = self.suspended_sessions[session_id]
            context.is_suspended = False
            context.is_active = True
            context.last_activity = datetime.now()
            
            # Move back to active sessions
            self.active_sessions[session_id] = context
            del self.suspended_sessions[session_id]
            
            logger.info(f"Resumed session {session_id}")
            return True
    
    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session and clean up its resources."""
        context = None
        
        # Find the session
        if session_id in self.active_sessions:
            context = self.active_sessions[session_id]
            del self.active_sessions[session_id]
        elif session_id in self.suspended_sessions:
            context = self.suspended_sessions[session_id]
            del self.suspended_sessions[session_id]
        
        if not context:
            return False
        
        # Clean up session resources
        await self._cleanup_session_resources(context)
        
        # Remove session lock
        if session_id in self.session_locks:
            del self.session_locks[session_id]
        
        logger.info(f"Destroyed session {session_id}")
        return True
    
    async def _cleanup_session_resources(self, context: SessionContext):
        """Clean up resources for a session."""
        session_id = context.session_id
        
        # Execute cleanup callbacks
        for callback in context.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.warning(f"Cleanup callback failed for session {session_id}: {e}")
        
        # Clean up shared resource access
        with self.global_resource_lock:
            for resource_id, resource in self.shared_resources.items():
                if session_id in resource.access_permissions:
                    del resource.access_permissions[session_id]
        
        # Clean up temporary files
        if context.temp_directory and context.temp_directory.exists():
            try:
                shutil.rmtree(context.temp_directory, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory for session {session_id}: {e}")
    
    def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """Get session context by ID."""
        return self.active_sessions.get(session_id) or self.suspended_sessions.get(session_id)
    
    def create_shared_resource(self, resource_id: str, resource_type: ResourceType, 
                             data: Any, permissions: Optional[Dict[str, Set[str]]] = None) -> SharedResource:
        """Create a shared resource with access control."""
        with self.global_resource_lock:
            if resource_id in self.shared_resources:
                raise ValueError(f"Shared resource {resource_id} already exists")
            
            resource = SharedResource(
                resource_id=resource_id,
                resource_type=resource_type,
                data=data,
                access_permissions=permissions or {}
            )
            
            self.shared_resources[resource_id] = resource
            logger.debug(f"Created shared resource {resource_id}")
            return resource
    
    def access_shared_resource(self, session_id: str, resource_id: str, 
                             permission: str = "read") -> Optional[Any]:
        """Access a shared resource with permission checking."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} is not active")
        
        with self.global_resource_lock:
            if resource_id not in self.shared_resources:
                return None
            
            resource = self.shared_resources[resource_id]
            
            # Check permissions
            session_permissions = resource.access_permissions.get(session_id, set())
            if permission not in session_permissions:
                raise PermissionError(f"Session {session_id} does not have {permission} permission for resource {resource_id}")
            
            # Access the resource
            with resource.lock:
                resource.access_count += 1
                resource.last_accessed = datetime.now()
                return resource.data
    
    def update_shared_resource(self, session_id: str, resource_id: str, data: Any) -> bool:
        """Update a shared resource."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} is not active")
        
        with self.global_resource_lock:
            if resource_id not in self.shared_resources:
                return False
            
            resource = self.shared_resources[resource_id]
            
            # Check write permission
            session_permissions = resource.access_permissions.get(session_id, set())
            if "write" not in session_permissions:
                raise PermissionError(f"Session {session_id} does not have write permission for resource {resource_id}")
            
            # Update the resource
            with resource.lock:
                resource.data = data
                resource.last_accessed = datetime.now()
                return True
    
    def grant_resource_access(self, session_id: str, resource_id: str, permissions: Set[str]) -> bool:
        """Grant resource access permissions to a session."""
        with self.global_resource_lock:
            if resource_id not in self.shared_resources:
                return False
            
            resource = self.shared_resources[resource_id]
            resource.access_permissions[session_id] = permissions
            return True
    
    def revoke_resource_access(self, session_id: str, resource_id: str) -> bool:
        """Revoke resource access permissions from a session."""
        with self.global_resource_lock:
            if resource_id not in self.shared_resources:
                return False
            
            resource = self.shared_resources[resource_id]
            if session_id in resource.access_permissions:
                del resource.access_permissions[session_id]
                return True
            return False
    
    def get_session_temp_directory(self, session_id: str) -> Optional[Path]:
        """Get the temporary directory for a session."""
        context = self.get_session_context(session_id)
        return context.temp_directory if context else None
    
    def get_session_namespace(self, session_id: str, resource_type: ResourceType) -> Optional[str]:
        """Get the namespace for a session resource type."""
        context = self.get_session_context(session_id)
        if not context:
            return None
        
        if resource_type == ResourceType.MEMORY:
            return context.memory_namespace
        elif resource_type == ResourceType.CACHE:
            return context.cache_namespace
        else:
            return f"session_{session_id}_{resource_type.value}"
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired resources and sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
                await self._cleanup_expired_resources()
            except Exception as e:
                logger.error(f"Periodic cleanup failed: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        now = datetime.now()
        expired_sessions = []
        
        # Check suspended sessions for expiration
        for session_id, context in self.suspended_sessions.items():
            if context.last_activity + timedelta(hours=24) < now:
                expired_sessions.append(session_id)
        
        # Clean up expired sessions
        for session_id in expired_sessions:
            await self.destroy_session(session_id)
            logger.info(f"Cleaned up expired session {session_id}")
    
    async def _cleanup_expired_resources(self):
        """Clean up expired shared resources."""
        now = datetime.now()
        expired_resources = []
        
        with self.global_resource_lock:
            for resource_id, resource in self.shared_resources.items():
                # Check if resource has TTL and is expired
                boundary = self.resource_boundaries.get(resource.resource_type)
                if boundary and boundary.ttl_seconds:
                    if resource.last_accessed + timedelta(seconds=boundary.ttl_seconds) < now:
                        expired_resources.append(resource_id)
        
        # Remove expired resources
        for resource_id in expired_resources:
            with self.global_resource_lock:
                if resource_id in self.shared_resources:
                    del self.shared_resources[resource_id]
                    logger.debug(f"Cleaned up expired resource {resource_id}")
    
    def get_isolation_stats(self) -> Dict[str, Any]:
        """Get isolation system statistics."""
        return {
            "active_sessions": len(self.active_sessions),
            "suspended_sessions": len(self.suspended_sessions),
            "shared_resources": len(self.shared_resources),
            "resource_boundaries": len(self.resource_boundaries),
            "default_isolation_level": self.default_isolation_level.value,
            "cleanup_interval": self.cleanup_interval
        }
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific session."""
        context = self.get_session_context(session_id)
        if not context:
            return None
        
        return {
            "session_id": session_id,
            "isolation_level": context.isolation_level.value,
            "is_active": context.is_active,
            "is_suspended": context.is_suspended,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "memory_namespace": context.memory_namespace,
            "cache_namespace": context.cache_namespace,
            "temp_directory": str(context.temp_directory) if context.temp_directory else None,
            "shared_resources": len(context.shared_resources),
            "resource_locks": len(context.resource_locks),
            "cleanup_callbacks": len(context.cleanup_callbacks)
        }
