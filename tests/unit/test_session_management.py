"""
Unit tests for session management functionality.

This module tests both SessionManager and SessionIsolationManager:
- Session lifecycle management
- Resource isolation and boundaries
- Shared resource access control
- Concurrent session handling
- Error handling and cleanup
"""

import pytest
import asyncio
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.audit.session_manager import (
    SessionManager, SessionStatus, SessionConfig, SessionProgress
)
from ai_code_audit.audit.session_isolation import (
    SessionIsolationManager, IsolationLevel, ResourceType, 
    SessionContext, ResourceBoundary, SharedResource
)
from ai_code_audit.core.models import ProjectInfo, FileInfo
from ai_code_audit.core.exceptions import AuditError


class TestSessionManager:
    """Test SessionManager functionality."""
    
    @pytest.fixture
    async def session_manager(self):
        """Fixture providing a session manager."""
        manager = SessionManager()
        yield manager
        # Cleanup any remaining sessions
        for session_id in list(manager.active_sessions.keys()):
            await manager.cleanup_session(session_id)
    
    @pytest.fixture
    def sample_project_info(self):
        """Fixture providing sample project info."""
        return ProjectInfo(
            name="test_project",
            path="/test/path",
            language="python",
            files=[
                FileInfo(
                    path="/test/path/main.py",
                    name="main.py",
                    size=1024,
                    language="python"
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, sample_project_info):
        """Test session creation."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        assert session_id is not None
        assert session_id in session_manager.active_sessions
        
        session = session_manager.active_sessions[session_id]
        assert session.status == SessionStatus.CREATED
        assert session.project_info == sample_project_info
        assert session.created_at is not None
    
    @pytest.mark.asyncio
    async def test_start_session(self, session_manager, sample_project_info):
        """Test session startup."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        await session_manager.start_session(session_id)
        
        session = session_manager.active_sessions[session_id]
        assert session.status == SessionStatus.RUNNING
        assert session.started_at is not None
    
    @pytest.mark.asyncio
    async def test_pause_and_resume_session(self, session_manager, sample_project_info):
        """Test session pause and resume."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        await session_manager.start_session(session_id)
        
        # Pause session
        await session_manager.pause_session(session_id)
        session = session_manager.active_sessions[session_id]
        assert session.status == SessionStatus.PAUSED
        
        # Resume session
        await session_manager.resume_session(session_id)
        session = session_manager.active_sessions[session_id]
        assert session.status == SessionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_complete_session(self, session_manager, sample_project_info):
        """Test session completion."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        await session_manager.start_session(session_id)
        await session_manager.complete_session(session_id)
        
        session = session_manager.active_sessions[session_id]
        assert session.status == SessionStatus.COMPLETED
        assert session.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_session_progress_tracking(self, session_manager, sample_project_info):
        """Test session progress tracking."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        # Update progress
        await session_manager.update_progress(session_id, files_processed=5, total_files=10)
        
        session = session_manager.active_sessions[session_id]
        assert session.progress.files_processed == 5
        assert session.progress.total_files == 10
        assert session.progress.percentage == 50.0
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, session_manager, sample_project_info):
        """Test session cleanup."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        assert session_id in session_manager.active_sessions
        
        await session_manager.cleanup_session(session_id)
        
        assert session_id not in session_manager.active_sessions
    
    @pytest.mark.asyncio
    async def test_get_session_status(self, session_manager, sample_project_info):
        """Test getting session status."""
        session_id = await session_manager.create_session(
            project_info=sample_project_info,
            config=SessionConfig()
        )
        
        status = session_manager.get_session_status(session_id)
        assert status == SessionStatus.CREATED
        
        await session_manager.start_session(session_id)
        status = session_manager.get_session_status(session_id)
        assert status == SessionStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_list_active_sessions(self, session_manager, sample_project_info):
        """Test listing active sessions."""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = await session_manager.create_session(
                project_info=sample_project_info,
                config=SessionConfig()
            )
            session_ids.append(session_id)
        
        active_sessions = session_manager.list_active_sessions()
        assert len(active_sessions) == 3
        
        for session_id in session_ids:
            assert session_id in active_sessions


class TestSessionIsolationManager:
    """Test SessionIsolationManager functionality."""
    
    @pytest.fixture
    def isolation_manager(self):
        """Fixture providing a session isolation manager."""
        manager = SessionIsolationManager()
        yield manager
        # Cleanup
        asyncio.create_task(manager._cleanup_expired_sessions())
    
    @pytest.mark.asyncio
    async def test_create_session_context(self, isolation_manager):
        """Test creating session context."""
        context = await isolation_manager.create_session("test_session_1")
        
        assert context.session_id == "test_session_1"
        assert context.isolation_level == isolation_manager.default_isolation_level
        assert context.memory_namespace == "session_test_session_1_memory"
        assert context.cache_namespace == "session_test_session_1_cache"
        assert context.is_active
        assert not context.is_suspended
    
    @pytest.mark.asyncio
    async def test_create_session_with_isolation_level(self, isolation_manager):
        """Test creating session with specific isolation level."""
        context = await isolation_manager.create_session(
            "test_session_strict", 
            IsolationLevel.STRICT
        )
        
        assert context.isolation_level == IsolationLevel.STRICT
        assert context.temp_directory is not None
        assert context.temp_directory.exists()
    
    @pytest.mark.asyncio
    async def test_suspend_and_resume_session(self, isolation_manager):
        """Test session suspension and resumption."""
        await isolation_manager.create_session("test_session_suspend")
        
        # Suspend
        success = await isolation_manager.suspend_session("test_session_suspend")
        assert success
        
        context = isolation_manager.get_session_context("test_session_suspend")
        assert context.is_suspended
        assert not context.is_active
        
        # Resume
        success = await isolation_manager.resume_session("test_session_suspend")
        assert success
        
        context = isolation_manager.get_session_context("test_session_suspend")
        assert not context.is_suspended
        assert context.is_active
    
    @pytest.mark.asyncio
    async def test_destroy_session(self, isolation_manager):
        """Test session destruction."""
        await isolation_manager.create_session("test_session_destroy")
        
        # Verify session exists
        context = isolation_manager.get_session_context("test_session_destroy")
        assert context is not None
        
        # Destroy session
        success = await isolation_manager.destroy_session("test_session_destroy")
        assert success
        
        # Verify session no longer exists
        context = isolation_manager.get_session_context("test_session_destroy")
        assert context is None
    
    @pytest.mark.asyncio
    async def test_resource_isolation(self, isolation_manager):
        """Test resource isolation between sessions."""
        # Create two sessions
        context1 = await isolation_manager.create_session("session_1")
        context2 = await isolation_manager.create_session("session_2")
        
        # Verify different namespaces
        assert context1.memory_namespace != context2.memory_namespace
        assert context1.cache_namespace != context2.cache_namespace
        
        # Verify different temp directories (if applicable)
        if context1.temp_directory and context2.temp_directory:
            assert context1.temp_directory != context2.temp_directory
    
    def test_create_shared_resource(self, isolation_manager):
        """Test creating shared resources."""
        test_data = {"key": "value", "number": 42}
        
        resource = isolation_manager.create_shared_resource(
            "test_resource", 
            ResourceType.MEMORY, 
            test_data
        )
        
        assert resource.resource_id == "test_resource"
        assert resource.resource_type == ResourceType.MEMORY
        assert resource.data == test_data
        assert resource.access_count == 0
    
    @pytest.mark.asyncio
    async def test_shared_resource_access_control(self, isolation_manager):
        """Test shared resource access control."""
        # Create session and resource
        await isolation_manager.create_session("test_session")
        
        test_data = {"shared": "data"}
        isolation_manager.create_shared_resource(
            "controlled_resource",
            ResourceType.MEMORY,
            test_data
        )
        
        # Grant read permission
        isolation_manager.grant_resource_access(
            "test_session", 
            "controlled_resource", 
            {"read"}
        )
        
        # Should be able to read
        data = isolation_manager.access_shared_resource(
            "test_session", 
            "controlled_resource", 
            "read"
        )
        assert data == test_data
        
        # Should not be able to write
        with pytest.raises(PermissionError):
            isolation_manager.update_shared_resource(
                "test_session",
                "controlled_resource", 
                {"new": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_concurrent_resource_access(self, isolation_manager):
        """Test concurrent access to shared resources."""
        # Create session and resource
        await isolation_manager.create_session("concurrent_session")
        
        test_data = {"concurrent": "access"}
        isolation_manager.create_shared_resource(
            "concurrent_resource",
            ResourceType.MEMORY,
            test_data
        )
        
        isolation_manager.grant_resource_access(
            "concurrent_session",
            "concurrent_resource",
            {"read"}
        )
        
        # Concurrent access function
        def access_resource():
            return isolation_manager.access_shared_resource(
                "concurrent_session",
                "concurrent_resource",
                "read"
            )
        
        # Run concurrent accesses
        threads = []
        results = []
        
        def thread_worker():
            result = access_resource()
            results.append(result)
        
        for _ in range(5):
            thread = threading.Thread(target=thread_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All accesses should succeed
        assert len(results) == 5
        assert all(result == test_data for result in results)
    
    def test_get_session_namespace(self, isolation_manager):
        """Test getting session namespaces."""
        session_id = "namespace_test_session"
        
        # Test different resource types
        memory_ns = isolation_manager.get_session_namespace(session_id, ResourceType.MEMORY)
        cache_ns = isolation_manager.get_session_namespace(session_id, ResourceType.CACHE)
        file_ns = isolation_manager.get_session_namespace(session_id, ResourceType.FILE_SYSTEM)
        
        assert memory_ns == f"session_{session_id}_memory"
        assert cache_ns == f"session_{session_id}_cache"
        assert file_ns == f"session_{session_id}_file_system"
    
    @pytest.mark.asyncio
    async def test_get_session_temp_directory(self, isolation_manager):
        """Test getting session temporary directory."""
        # Create session with strict isolation (should have temp directory)
        context = await isolation_manager.create_session(
            "temp_dir_session", 
            IsolationLevel.STRICT
        )
        
        temp_dir = isolation_manager.get_session_temp_directory("temp_dir_session")
        assert temp_dir is not None
        assert temp_dir == context.temp_directory
        assert temp_dir.exists()
    
    def test_get_isolation_stats(self, isolation_manager):
        """Test getting isolation statistics."""
        stats = isolation_manager.get_isolation_stats()
        
        assert "active_sessions" in stats
        assert "suspended_sessions" in stats
        assert "shared_resources" in stats
        assert "resource_boundaries" in stats
        assert "default_isolation_level" in stats
        assert "cleanup_interval" in stats
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, isolation_manager):
        """Test getting session-specific statistics."""
        context = await isolation_manager.create_session("stats_session")
        
        stats = isolation_manager.get_session_stats("stats_session")
        
        assert stats is not None
        assert stats["session_id"] == "stats_session"
        assert stats["isolation_level"] == context.isolation_level.value
        assert stats["is_active"] == context.is_active
        assert stats["is_suspended"] == context.is_suspended
        assert "created_at" in stats
        assert "last_activity" in stats
        assert "memory_namespace" in stats
        assert "cache_namespace" in stats


class TestSessionIntegration:
    """Test integration between SessionManager and SessionIsolationManager."""
    
    @pytest.fixture
    async def integrated_managers(self):
        """Fixture providing both managers."""
        session_manager = SessionManager()
        isolation_manager = SessionIsolationManager()
        
        yield session_manager, isolation_manager
        
        # Cleanup
        for session_id in list(session_manager.active_sessions.keys()):
            await session_manager.cleanup_session(session_id)
    
    @pytest.mark.asyncio
    async def test_integrated_session_lifecycle(self, integrated_managers):
        """Test integrated session lifecycle."""
        session_manager, isolation_manager = integrated_managers
        
        # Create project info
        project_info = ProjectInfo(
            name="integration_test",
            path="/test/path",
            language="python",
            files=[]
        )
        
        # Create session in session manager
        session_id = await session_manager.create_session(
            project_info=project_info,
            config=SessionConfig()
        )
        
        # Create corresponding isolation context
        isolation_context = await isolation_manager.create_session(session_id)
        
        # Verify integration
        assert session_id in session_manager.active_sessions
        assert isolation_context.session_id == session_id
        
        # Test lifecycle operations
        await session_manager.start_session(session_id)
        await session_manager.pause_session(session_id)
        await isolation_manager.suspend_session(session_id)
        
        # Verify states
        session = session_manager.active_sessions[session_id]
        context = isolation_manager.get_session_context(session_id)
        
        assert session.status == SessionStatus.PAUSED
        assert context.is_suspended
        
        # Resume both
        await session_manager.resume_session(session_id)
        await isolation_manager.resume_session(session_id)
        
        # Verify resumed states
        assert session.status == SessionStatus.RUNNING
        assert context.is_active
        
        # Cleanup
        await session_manager.cleanup_session(session_id)
        await isolation_manager.destroy_session(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
