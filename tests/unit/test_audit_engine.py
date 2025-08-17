"""
Unit tests for the AuditEngine core functionality.

This module tests the main audit engine including:
- Engine initialization and configuration
- Audit session creation and management
- File analysis workflow
- Error handling and recovery
- Session isolation integration
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.audit.engine import AuditEngine
from ai_code_audit.audit.session_isolation import IsolationLevel
from ai_code_audit.core.models import ProjectInfo, FileInfo, AuditResult
from ai_code_audit.core.exceptions import AuditError, ConfigurationError


class TestAuditEngineInitialization:
    """Test audit engine initialization and configuration."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization_default(self):
        """Test engine initialization with default settings."""
        engine = AuditEngine()
        
        # Should not be initialized yet
        assert not engine.is_initialized
        assert engine.session_manager is None
        assert engine.orchestrator is None
        
        # Initialize
        await engine.initialize()
        
        # Should be initialized now
        assert engine.is_initialized
        assert engine.session_manager is not None
        assert engine.orchestrator is not None
        assert engine.session_isolation is not None
        
        # Cleanup
        await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_engine_initialization_with_caching(self):
        """Test engine initialization with caching enabled."""
        engine = AuditEngine(enable_caching=True)
        await engine.initialize()
        
        assert engine.cache_manager is not None
        assert engine.is_initialized
        
        await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_engine_initialization_without_caching(self):
        """Test engine initialization with caching disabled."""
        engine = AuditEngine(enable_caching=False)
        await engine.initialize()
        
        assert engine.cache_manager is None
        assert engine.is_initialized
        
        await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_double_initialization_error(self):
        """Test that double initialization raises an error."""
        engine = AuditEngine()
        await engine.initialize()
        
        with pytest.raises(AuditError, match="already initialized"):
            await engine.initialize()
        
        await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_shutdown_before_initialization(self):
        """Test shutdown before initialization."""
        engine = AuditEngine()
        
        # Should not raise an error
        await engine.shutdown()
        assert not engine.is_initialized


class TestAuditEngineSessionManagement:
    """Test audit engine session management functionality."""
    
    @pytest.fixture
    async def initialized_engine(self):
        """Fixture providing an initialized audit engine."""
        engine = AuditEngine(enable_caching=True)
        await engine.initialize()
        yield engine
        await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_create_isolated_session(self, initialized_engine):
        """Test creating an isolated session."""
        engine = initialized_engine
        
        success = await engine.create_isolated_session("test_session_1")
        assert success
        
        # Verify session exists
        stats = engine.get_session_stats("test_session_1")
        assert stats is not None
        assert stats["session_id"] == "test_session_1"
        assert stats["is_active"]
        assert not stats["is_suspended"]
    
    @pytest.mark.asyncio
    async def test_create_session_with_isolation_level(self, initialized_engine):
        """Test creating session with specific isolation level."""
        engine = initialized_engine
        
        success = await engine.create_isolated_session(
            "test_session_strict", 
            IsolationLevel.STRICT
        )
        assert success
        
        stats = engine.get_session_stats("test_session_strict")
        assert stats["isolation_level"] == "strict"
    
    @pytest.mark.asyncio
    async def test_suspend_and_resume_session(self, initialized_engine):
        """Test session suspension and resumption."""
        engine = initialized_engine
        
        # Create session
        await engine.create_isolated_session("test_session_suspend")
        
        # Suspend session
        success = await engine.suspend_session("test_session_suspend")
        assert success
        
        stats = engine.get_session_stats("test_session_suspend")
        assert stats["is_suspended"]
        assert not stats["is_active"]
        
        # Resume session
        success = await engine.resume_session("test_session_suspend")
        assert success
        
        stats = engine.get_session_stats("test_session_suspend")
        assert not stats["is_suspended"]
        assert stats["is_active"]
    
    @pytest.mark.asyncio
    async def test_destroy_session(self, initialized_engine):
        """Test session destruction."""
        engine = initialized_engine
        
        # Create session
        await engine.create_isolated_session("test_session_destroy")
        
        # Verify session exists
        stats = engine.get_session_stats("test_session_destroy")
        assert stats is not None
        
        # Destroy session
        success = await engine.destroy_session("test_session_destroy")
        assert success
        
        # Verify session no longer exists
        stats = engine.get_session_stats("test_session_destroy")
        assert stats is None
    
    @pytest.mark.asyncio
    async def test_get_isolation_stats(self, initialized_engine):
        """Test getting isolation system statistics."""
        engine = initialized_engine
        
        stats = engine.get_isolation_stats()
        assert stats is not None
        assert "active_sessions" in stats
        assert "suspended_sessions" in stats
        assert "shared_resources" in stats
        assert "default_isolation_level" in stats


class TestAuditEngineFileAnalysis:
    """Test audit engine file analysis functionality."""
    
    @pytest.fixture
    async def engine_with_session(self):
        """Fixture providing engine with a test session."""
        engine = AuditEngine(enable_caching=True)
        await engine.initialize()
        await engine.create_isolated_session("test_analysis_session")
        yield engine
        await engine.shutdown()
    
    @pytest.fixture
    def sample_project_dir(self):
        """Fixture providing a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create sample files
        (project_path / "main.py").write_text("""
import os
import subprocess

def vulnerable_function(user_input):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command injection vulnerability
    subprocess.call(f"echo {user_input}", shell=True)
    
    return query
""")
        
        (project_path / "utils.py").write_text("""
def safe_function():
    return "This is safe"

def another_function(data):
    return data.upper()
""")
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_analyze_file_basic(self, engine_with_session, sample_project_dir):
        """Test basic file analysis."""
        engine = engine_with_session
        
        file_path = sample_project_dir / "main.py"
        
        with patch.object(engine, '_analyze_file_with_llm', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = AuditResult(
                file_path=str(file_path),
                issues_found=2,
                security_score=0.6,
                issues=[
                    {
                        "type": "SQL_INJECTION",
                        "severity": "HIGH",
                        "line": 6,
                        "description": "SQL injection vulnerability detected"
                    },
                    {
                        "type": "COMMAND_INJECTION", 
                        "severity": "HIGH",
                        "line": 9,
                        "description": "Command injection vulnerability detected"
                    }
                ]
            )
            
            result = await engine.analyze_file(str(file_path))
            
            assert result is not None
            assert result.issues_found == 2
            assert result.security_score == 0.6
            assert len(result.issues) == 2
            
            # Verify LLM was called
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_file_with_context(self, engine_with_session, sample_project_dir):
        """Test file analysis with context extraction."""
        engine = engine_with_session
        
        file_path = sample_project_dir / "main.py"
        
        with patch.object(engine, '_analyze_file_with_llm', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = AuditResult(
                file_path=str(file_path),
                issues_found=1,
                security_score=0.8
            )
            
            result = await engine.analyze_file(str(file_path), include_context=True)
            
            assert result is not None
            mock_analyze.assert_called_once()
            
            # Verify context was included in the call
            call_args = mock_analyze.call_args
            assert "context" in call_args.kwargs or len(call_args.args) > 2
    
    @pytest.mark.asyncio
    async def test_analyze_file_error_handling(self, engine_with_session):
        """Test file analysis error handling."""
        engine = engine_with_session
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            await engine.analyze_file("/non/existent/file.py")
    
    @pytest.mark.asyncio
    async def test_analyze_file_with_caching(self, engine_with_session, sample_project_dir):
        """Test file analysis with caching."""
        engine = engine_with_session
        
        file_path = sample_project_dir / "main.py"
        
        with patch.object(engine, '_analyze_file_with_llm', new_callable=AsyncMock) as mock_analyze:
            mock_result = AuditResult(
                file_path=str(file_path),
                issues_found=1,
                security_score=0.8
            )
            mock_analyze.return_value = mock_result
            
            # First analysis - should call LLM
            result1 = await engine.analyze_file(str(file_path))
            assert mock_analyze.call_count == 1
            
            # Second analysis - should use cache if available
            result2 = await engine.analyze_file(str(file_path))
            
            # Results should be the same
            assert result1.file_path == result2.file_path
            assert result1.security_score == result2.security_score


class TestAuditEngineErrorHandling:
    """Test audit engine error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_llm_failure_handling(self):
        """Test handling of LLM provider failures."""
        engine = AuditEngine()
        
        with patch('ai_code_audit.llm.manager.LLMManager') as mock_llm_manager:
            mock_llm_manager.return_value.analyze_code.side_effect = Exception("LLM API Error")
            
            await engine.initialize()
            
            # Should handle LLM errors gracefully
            with pytest.raises(AuditError):
                await engine.analyze_file("test_file.py")
            
            await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_database_failure_handling(self):
        """Test handling of database failures."""
        engine = AuditEngine()
        
        with patch('ai_code_audit.database.services.AuditSessionService') as mock_service:
            mock_service.return_value.create_session.side_effect = Exception("Database Error")
            
            await engine.initialize()
            
            # Should handle database errors gracefully
            with pytest.raises(AuditError):
                await engine.create_audit_session("test_project")
            
            await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_isolation_failure_handling(self):
        """Test handling of session isolation failures."""
        engine = AuditEngine()
        await engine.initialize()
        
        with patch.object(engine.session_isolation, 'create_session', side_effect=Exception("Isolation Error")):
            success = await engine.create_isolated_session("test_session")
            assert not success
        
        await engine.shutdown()


class TestAuditEngineIntegration:
    """Test audit engine integration with other components."""
    
    @pytest.mark.asyncio
    async def test_full_audit_workflow(self):
        """Test complete audit workflow integration."""
        engine = AuditEngine(enable_caching=True)
        await engine.initialize()
        
        try:
            # Create isolated session
            session_success = await engine.create_isolated_session("integration_test")
            assert session_success
            
            # Mock project analysis
            with patch('ai_code_audit.analysis.project_analyzer.ProjectAnalyzer') as mock_analyzer:
                mock_project_info = ProjectInfo(
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
                mock_analyzer.return_value.analyze_project.return_value = mock_project_info
                
                # Mock LLM analysis
                with patch.object(engine, '_analyze_file_with_llm', new_callable=AsyncMock) as mock_llm:
                    mock_llm.return_value = AuditResult(
                        file_path="/test/path/main.py",
                        issues_found=1,
                        security_score=0.8
                    )
                    
                    # Run analysis
                    result = await engine.analyze_file("/test/path/main.py")
                    
                    assert result is not None
                    assert result.security_score == 0.8
            
            # Verify session stats
            stats = engine.get_session_stats("integration_test")
            assert stats is not None
            assert stats["is_active"]
            
            # Clean up session
            destroy_success = await engine.destroy_session("integration_test")
            assert destroy_success
            
        finally:
            await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """Test concurrent session handling."""
        engine = AuditEngine()
        await engine.initialize()
        
        try:
            # Create multiple sessions concurrently
            session_tasks = [
                engine.create_isolated_session(f"concurrent_session_{i}")
                for i in range(3)
            ]
            
            results = await asyncio.gather(*session_tasks)
            assert all(results)
            
            # Verify all sessions exist
            isolation_stats = engine.get_isolation_stats()
            assert isolation_stats["active_sessions"] >= 3
            
            # Clean up sessions
            cleanup_tasks = [
                engine.destroy_session(f"concurrent_session_{i}")
                for i in range(3)
            ]
            
            cleanup_results = await asyncio.gather(*cleanup_tasks)
            assert all(cleanup_results)
            
        finally:
            await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
