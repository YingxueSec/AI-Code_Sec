"""
Unit tests for database operations.

This module tests:
- Database connection management
- SQLAlchemy model operations
- Database service layer
- Transaction handling
- Error handling and recovery
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from datetime import datetime
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.database.connection import DatabaseManager, get_database_manager
from ai_code_audit.database.models import (
    AuditSession, AuditResult, SecurityIssue, ProjectInfo as DBProjectInfo
)
from ai_code_audit.database.services import (
    AuditSessionService, AuditResultService, SecurityIssueService
)
from ai_code_audit.core.models import ProjectInfo, FileInfo, AuditResult as CoreAuditResult
from ai_code_audit.core.exceptions import DatabaseError


class TestDatabaseConnection:
    """Test database connection management."""
    
    @pytest.fixture
    def test_db_url(self):
        """Fixture providing test database URL."""
        # Use SQLite for testing
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        return f"sqlite:///{temp_db.name}"
    
    @pytest.mark.asyncio
    async def test_database_manager_initialization(self, test_db_url):
        """Test database manager initialization."""
        manager = DatabaseManager(test_db_url)
        
        assert manager.database_url == test_db_url
        assert manager.engine is None
        assert not manager.is_connected
    
    @pytest.mark.asyncio
    async def test_database_connection(self, test_db_url):
        """Test database connection establishment."""
        manager = DatabaseManager(test_db_url)
        
        await manager.connect()
        
        assert manager.engine is not None
        assert manager.is_connected
        
        await manager.disconnect()
        assert not manager.is_connected
    
    @pytest.mark.asyncio
    async def test_database_session_creation(self, test_db_url):
        """Test database session creation."""
        manager = DatabaseManager(test_db_url)
        await manager.connect()
        
        try:
            async with manager.get_session() as session:
                assert session is not None
                # Session should be usable
                result = await session.execute("SELECT 1")
                assert result is not None
        finally:
            await manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, test_db_url):
        """Test database health check."""
        manager = DatabaseManager(test_db_url)
        await manager.connect()
        
        try:
            is_healthy = await manager.health_check()
            assert is_healthy
        finally:
            await manager.disconnect()
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test database connection error handling."""
        # Invalid database URL
        manager = DatabaseManager("invalid://database/url")
        
        with pytest.raises(DatabaseError):
            await manager.connect()
    
    @pytest.mark.asyncio
    async def test_get_database_manager_singleton(self, test_db_url):
        """Test database manager singleton pattern."""
        with patch('ai_code_audit.core.config.get_config') as mock_config:
            mock_config.return_value.database.get_url.return_value = test_db_url
            
            manager1 = get_database_manager()
            manager2 = get_database_manager()
            
            assert manager1 is manager2


class TestDatabaseModels:
    """Test SQLAlchemy model operations."""
    
    @pytest_asyncio.fixture
    async def db_session(self, test_db_url):
        """Fixture providing database session."""
        manager = DatabaseManager(test_db_url)
        await manager.connect()

        # Create tables
        from ai_code_audit.database.models import Base
        async with manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with manager.get_session() as session:
            yield session

        await manager.disconnect()
    
    @pytest.fixture
    def test_db_url(self):
        """Fixture providing test database URL."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        return f"sqlite:///{temp_db.name}"
    
    @pytest.mark.asyncio
    async def test_audit_session_model(self, db_session):
        """Test AuditSession model operations."""
        # Create audit session
        session_data = AuditSession(
            session_id="test_session_123",
            project_name="test_project",
            project_path="/test/path",
            status="running",
            created_at=datetime.utcnow()
        )
        
        db_session.add(session_data)
        await db_session.commit()
        
        # Query session
        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditSession).where(AuditSession.session_id == "test_session_123")
        )
        retrieved_session = result.scalar_one_or_none()
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == "test_session_123"
        assert retrieved_session.project_name == "test_project"
        assert retrieved_session.status == "running"
    
    @pytest.mark.asyncio
    async def test_audit_result_model(self, db_session):
        """Test AuditResult model operations."""
        # Create audit result
        result_data = AuditResult(
            session_id="test_session_123",
            file_path="/test/file.py",
            issues_found=2,
            security_score=0.7,
            analysis_result={"issues": []},
            created_at=datetime.utcnow()
        )
        
        db_session.add(result_data)
        await db_session.commit()
        
        # Query result
        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditResult).where(AuditResult.file_path == "/test/file.py")
        )
        retrieved_result = result.scalar_one_or_none()
        
        assert retrieved_result is not None
        assert retrieved_result.session_id == "test_session_123"
        assert retrieved_result.issues_found == 2
        assert retrieved_result.security_score == 0.7
    
    @pytest.mark.asyncio
    async def test_security_issue_model(self, db_session):
        """Test SecurityIssue model operations."""
        # Create security issue
        issue_data = SecurityIssue(
            session_id="test_session_123",
            file_path="/test/file.py",
            issue_type="SQL_INJECTION",
            severity="HIGH",
            line_number=10,
            description="SQL injection vulnerability",
            recommendation="Use parameterized queries",
            created_at=datetime.utcnow()
        )
        
        db_session.add(issue_data)
        await db_session.commit()
        
        # Query issue
        from sqlalchemy import select
        result = await db_session.execute(
            select(SecurityIssue).where(SecurityIssue.issue_type == "SQL_INJECTION")
        )
        retrieved_issue = result.scalar_one_or_none()
        
        assert retrieved_issue is not None
        assert retrieved_issue.severity == "HIGH"
        assert retrieved_issue.line_number == 10
        assert "SQL injection" in retrieved_issue.description
    
    @pytest.mark.asyncio
    async def test_project_info_model(self, db_session):
        """Test ProjectInfo model operations."""
        # Create project info
        project_data = DBProjectInfo(
            name="test_project",
            path="/test/path",
            language="python",
            total_files=10,
            total_lines=1000,
            created_at=datetime.utcnow()
        )
        
        db_session.add(project_data)
        await db_session.commit()
        
        # Query project
        from sqlalchemy import select
        result = await db_session.execute(
            select(DBProjectInfo).where(DBProjectInfo.name == "test_project")
        )
        retrieved_project = result.scalar_one_or_none()
        
        assert retrieved_project is not None
        assert retrieved_project.language == "python"
        assert retrieved_project.total_files == 10
        assert retrieved_project.total_lines == 1000


class TestDatabaseServices:
    """Test database service layer."""
    
    @pytest_asyncio.fixture
    async def db_manager(self, test_db_url):
        """Fixture providing database manager."""
        manager = DatabaseManager(test_db_url)
        await manager.connect()

        # Create tables
        from ai_code_audit.database.models import Base
        async with manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield manager
        await manager.disconnect()
    
    @pytest.fixture
    def test_db_url(self):
        """Fixture providing test database URL."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        return f"sqlite:///{temp_db.name}"
    
    @pytest.mark.asyncio
    async def test_audit_session_service(self, db_manager):
        """Test AuditSessionService operations."""
        service = AuditSessionService(db_manager)
        
        # Create session
        session_id = await service.create_session(
            session_id="test_service_session",
            project_name="test_project",
            project_path="/test/path"
        )
        
        assert session_id == "test_service_session"
        
        # Get session
        session = await service.get_session(session_id)
        assert session is not None
        assert session.project_name == "test_project"
        
        # Update session status
        await service.update_session_status(session_id, "completed")
        
        updated_session = await service.get_session(session_id)
        assert updated_session.status == "completed"
        
        # List sessions
        sessions = await service.list_sessions()
        assert len(sessions) >= 1
        assert any(s.session_id == session_id for s in sessions)
    
    @pytest.mark.asyncio
    async def test_audit_result_service(self, db_manager):
        """Test AuditResultService operations."""
        service = AuditResultService(db_manager)
        
        # Create result
        result_data = CoreAuditResult(
            file_path="/test/file.py",
            issues_found=1,
            security_score=0.8,
            issues=[{
                "type": "XSS",
                "severity": "MEDIUM",
                "line": 5,
                "description": "XSS vulnerability"
            }]
        )
        
        result_id = await service.create_result(
            session_id="test_session",
            result=result_data
        )
        
        assert result_id is not None
        
        # Get result
        retrieved_result = await service.get_result(result_id)
        assert retrieved_result is not None
        assert retrieved_result.file_path == "/test/file.py"
        assert retrieved_result.security_score == 0.8
        
        # Get results by session
        session_results = await service.get_results_by_session("test_session")
        assert len(session_results) >= 1
        assert any(r.file_path == "/test/file.py" for r in session_results)
    
    @pytest.mark.asyncio
    async def test_security_issue_service(self, db_manager):
        """Test SecurityIssueService operations."""
        service = SecurityIssueService(db_manager)
        
        # Create issue
        issue_id = await service.create_issue(
            session_id="test_session",
            file_path="/test/file.py",
            issue_type="COMMAND_INJECTION",
            severity="HIGH",
            line_number=15,
            description="Command injection vulnerability",
            recommendation="Validate user input"
        )
        
        assert issue_id is not None
        
        # Get issue
        issue = await service.get_issue(issue_id)
        assert issue is not None
        assert issue.issue_type == "COMMAND_INJECTION"
        assert issue.severity == "HIGH"
        
        # Get issues by session
        session_issues = await service.get_issues_by_session("test_session")
        assert len(session_issues) >= 1
        
        # Get issues by file
        file_issues = await service.get_issues_by_file("/test/file.py")
        assert len(file_issues) >= 1
        
        # Get issues by type
        type_issues = await service.get_issues_by_type("COMMAND_INJECTION")
        assert len(type_issues) >= 1


class TestDatabaseErrorHandling:
    """Test database error handling."""
    
    @pytest.mark.asyncio
    async def test_connection_failure_handling(self):
        """Test handling of connection failures."""
        manager = DatabaseManager("invalid://url")
        
        with pytest.raises(DatabaseError):
            await manager.connect()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db_url):
        """Test transaction rollback on error."""
        manager = DatabaseManager(test_db_url)
        await manager.connect()
        
        try:
            async with manager.get_session() as session:
                # Create invalid data that should cause rollback
                invalid_session = AuditSession(
                    session_id=None,  # This should cause an error
                    project_name="test",
                    project_path="/test"
                )
                
                session.add(invalid_session)
                
                with pytest.raises(Exception):
                    await session.commit()
                
                # Session should be rolled back
                await session.rollback()
        finally:
            await manager.disconnect()
    
    @pytest.fixture
    def test_db_url(self):
        """Fixture providing test database URL."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        return f"sqlite:///{temp_db.name}"


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    @pytest_asyncio.fixture
    async def integrated_setup(self, test_db_url):
        """Fixture providing integrated database setup."""
        manager = DatabaseManager(test_db_url)
        await manager.connect()

        # Create tables
        from ai_code_audit.database.models import Base
        async with manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Initialize services
        session_service = AuditSessionService(manager)
        result_service = AuditResultService(manager)
        issue_service = SecurityIssueService(manager)

        yield manager, session_service, result_service, issue_service

        await manager.disconnect()
    
    @pytest.fixture
    def test_db_url(self):
        """Fixture providing test database URL."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        return f"sqlite:///{temp_db.name}"
    
    @pytest.mark.asyncio
    async def test_complete_audit_workflow(self, integrated_setup):
        """Test complete audit workflow through database."""
        manager, session_service, result_service, issue_service = integrated_setup
        
        # Create audit session
        session_id = await session_service.create_session(
            session_id="workflow_test",
            project_name="integration_project",
            project_path="/integration/path"
        )
        
        # Create audit results
        result_data = CoreAuditResult(
            file_path="/integration/path/main.py",
            issues_found=2,
            security_score=0.6,
            issues=[
                {
                    "type": "SQL_INJECTION",
                    "severity": "HIGH",
                    "line": 10,
                    "description": "SQL injection found"
                },
                {
                    "type": "XSS",
                    "severity": "MEDIUM", 
                    "line": 20,
                    "description": "XSS vulnerability"
                }
            ]
        )
        
        result_id = await result_service.create_result(session_id, result_data)
        
        # Create individual security issues
        for issue in result_data.issues:
            await issue_service.create_issue(
                session_id=session_id,
                file_path=result_data.file_path,
                issue_type=issue["type"],
                severity=issue["severity"],
                line_number=issue["line"],
                description=issue["description"],
                recommendation=f"Fix {issue['type']} vulnerability"
            )
        
        # Verify complete workflow
        session = await session_service.get_session(session_id)
        assert session.project_name == "integration_project"
        
        results = await result_service.get_results_by_session(session_id)
        assert len(results) == 1
        assert results[0].issues_found == 2
        
        issues = await issue_service.get_issues_by_session(session_id)
        assert len(issues) == 2
        assert any(issue.issue_type == "SQL_INJECTION" for issue in issues)
        assert any(issue.issue_type == "XSS" for issue in issues)
        
        # Update session status
        await session_service.update_session_status(session_id, "completed")
        
        final_session = await session_service.get_session(session_id)
        assert final_session.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
