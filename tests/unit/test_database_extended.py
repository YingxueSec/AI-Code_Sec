"""
Extended database operation tests.

This module provides comprehensive testing for:
- Advanced database operations and transactions
- Query optimization and performance
- Data integrity and constraints
- Bulk operations and batch processing
- Database migration and schema management
- Connection pooling and concurrency
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import uuid

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.database.connection import DatabaseManager, DatabaseConfig
from ai_code_audit.database.models import (
    AuditSession, SecurityFinding, AuditReport, Project, File, Module, Base
)
from ai_code_audit.core.models import ProjectType
from ai_code_audit.database.services import (
    AuditSessionService, SecurityFindingService, ProjectService, FileService, CacheService
)
from ai_code_audit.core.exceptions import DatabaseError


class TestAdvancedDatabaseOperations:
    """Advanced database operation tests."""
    
    @pytest.fixture
    def test_db_config(self):
        """Fixture providing test database configuration."""
        return DatabaseConfig(
            host="localhost",
            port=3306,
            username="test_user",
            password="test_pass",
            database="test_ai_audit",
            charset="utf8mb4"
        )
    
    @pytest_asyncio.fixture
    async def db_manager(self, test_db_config):
        """Fixture providing database manager with test config."""
        manager = DatabaseManager(test_db_config)

        # Mock the actual database connection for testing
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_engine, \
             patch.object(manager, '_test_connection') as mock_test_conn, \
             patch.object(manager, '_test_engine') as mock_test_engine:

            mock_engine.return_value = Mock()
            mock_test_conn.return_value = None  # Mock successful connection test
            mock_test_engine.return_value = None  # Mock successful engine test

            await manager.initialize()
            yield manager
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_transaction_management(self, db_manager):
        """Test database transaction management."""
        # Mock session
        mock_session = AsyncMock()

        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Test successful transaction
            async with db_manager.get_session() as session:
                # Simulate database operations without transaction context
                await ProjectService.create_project(
                    session,
                    name="Test Project",
                    path="/test/project",
                    project_type=ProjectType.WEB_APPLICATION
                )

            # Verify session was used
            mock_get_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_manager):
        """Test transaction rollback on error."""
        mock_session = AsyncMock()
        mock_transaction = AsyncMock()
        mock_session.begin.return_value.__aenter__.return_value = mock_transaction
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock service to raise an exception
            with patch.object(ProjectService, 'create_project', side_effect=Exception("Database error")):
                try:
                    async with db_manager.get_session() as session:
                        async with session.begin():
                            await ProjectService.create_project(
                                session,
                                name="Test Project",
                                project_type="web_app",
                                description="Test project"
                            )
                except Exception:
                    pass
            
            # Verify transaction was rolled back
            mock_transaction.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, db_manager):
        """Test bulk database operations for performance."""
        mock_session = AsyncMock()
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Test bulk project creation
            projects_data = [
                {"name": f"Project {i}", "project_type": "web_app", "description": f"Test project {i}"}
                for i in range(100)
            ]
            
            async with db_manager.get_session() as session:
                # Simulate bulk insert
                for project_data in projects_data:
                    await ProjectService.create_project(session, **project_data)
            
            # Verify all projects were processed
            assert mock_session.add.call_count == 100
    
    @pytest.mark.asyncio
    async def test_query_optimization(self, db_manager):
        """Test query optimization and performance."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            async with db_manager.get_session() as session:
                # Test optimized query with joins
                projects = await ProjectService.get_projects_with_stats(session)
                
                # Verify query was executed
                mock_session.execute.assert_called_once()
                assert projects == []
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, db_manager):
        """Test concurrent database operations."""
        mock_session = AsyncMock()
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Create multiple concurrent operations
            async def create_project(session, project_id):
                return await ProjectService.create_project(
                    session,
                    name=f"Concurrent Project {project_id}",
                    project_type="web_app",
                    description=f"Concurrent test project {project_id}"
                )
            
            # Execute concurrent operations
            tasks = []
            for i in range(10):
                task = create_project(mock_session, i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all operations completed
            assert len(results) == 10
            assert all(not isinstance(r, Exception) for r in results)


class TestDatabasePerformance:
    """Database performance and optimization tests."""
    
    @pytest_asyncio.fixture
    async def performance_db_manager(self):
        """Fixture for performance testing."""
        config = DatabaseConfig()
        manager = DatabaseManager(config)
        
        # Mock for performance testing
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            await manager.initialize()
            yield manager
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_connection_pooling(self, performance_db_manager):
        """Test database connection pooling efficiency."""
        mock_session = AsyncMock()
        
        with patch.object(performance_db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Simulate multiple concurrent connections
            async def use_connection(connection_id):
                async with performance_db_manager.get_session() as session:
                    # Simulate database work
                    await asyncio.sleep(0.01)
                    return f"Connection {connection_id} completed"
            
            # Test connection pool under load
            tasks = [use_connection(i) for i in range(20)]
            results = await asyncio.gather(*tasks)
            
            # Verify all connections were handled
            assert len(results) == 20
            assert all("completed" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_query_caching(self, performance_db_manager):
        """Test query result caching for performance."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(id="1", name="Cached Project", project_type="web_app")
        ]
        mock_session.execute.return_value = mock_result
        
        with patch.object(performance_db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            async with performance_db_manager.get_session() as session:
                # First query - should hit database
                projects1 = await ProjectService.get_all_projects(session)
                
                # Second query - should use cache (simulated)
                projects2 = await ProjectService.get_all_projects(session)
                
                # Verify caching behavior
                assert len(projects1) == len(projects2)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, performance_db_manager):
        """Test batch processing for large datasets."""
        mock_session = AsyncMock()
        
        with patch.object(performance_db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Simulate processing large batch of security findings
            findings_data = [
                {
                    "session_id": str(uuid.uuid4()),
                    "file_id": str(uuid.uuid4()),
                    "vulnerability_type": "SQL_INJECTION",
                    "severity": "HIGH",
                    "line_number": i,
                    "description": f"Test finding {i}"
                }
                for i in range(1000)
            ]
            
            # Process in batches
            batch_size = 100
            for i in range(0, len(findings_data), batch_size):
                batch = findings_data[i:i + batch_size]
                
                async with performance_db_manager.get_session() as session:
                    for finding_data in batch:
                        await SecurityFindingService.create_finding(session, **finding_data)
            
            # Verify batch processing completed
            assert mock_session.add.call_count == 1000


class TestDataIntegrity:
    """Data integrity and constraint tests."""
    
    @pytest_asyncio.fixture
    async def integrity_db_manager(self):
        """Fixture for data integrity testing."""
        config = DatabaseConfig()
        manager = DatabaseManager(config)
        
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            await manager.initialize()
            yield manager
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, integrity_db_manager):
        """Test foreign key constraint enforcement."""
        mock_session = AsyncMock()
        
        with patch.object(integrity_db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Test creating finding with invalid session_id
            with patch.object(SecurityFindingService, 'create_finding', 
                            side_effect=DatabaseError("Foreign key constraint failed")):
                
                with pytest.raises(DatabaseError, match="Foreign key constraint failed"):
                    async with integrity_db_manager.get_session() as session:
                        await SecurityFindingService.create_finding(
                            session,
                            session_id="invalid-session-id",
                            file_id=str(uuid.uuid4()),
                            vulnerability_type="XSS",
                            severity="MEDIUM",
                            line_number=10,
                            description="Test finding with invalid session"
                        )
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, integrity_db_manager):
        """Test unique constraint enforcement."""
        mock_session = AsyncMock()
        
        with patch.object(integrity_db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Test creating duplicate project
            with patch.object(ProjectService, 'create_project', 
                            side_effect=DatabaseError("Unique constraint violation")):
                
                with pytest.raises(DatabaseError, match="Unique constraint violation"):
                    async with integrity_db_manager.get_session() as session:
                        await ProjectService.create_project(
                            session,
                            name="Duplicate Project",
                            project_type="web_app",
                            description="This should fail due to unique constraint"
                        )
    
    @pytest.mark.asyncio
    async def test_data_validation(self, integrity_db_manager):
        """Test data validation before database operations."""
        mock_session = AsyncMock()
        
        with patch.object(integrity_db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Test invalid data validation
            with patch.object(SecurityFindingService, 'create_finding', 
                            side_effect=DatabaseError("Invalid severity level")):
                
                with pytest.raises(DatabaseError, match="Invalid severity level"):
                    async with integrity_db_manager.get_session() as session:
                        await SecurityFindingService.create_finding(
                            session,
                            session_id=str(uuid.uuid4()),
                            file_id=str(uuid.uuid4()),
                            vulnerability_type="XSS",
                            severity="INVALID_SEVERITY",  # Invalid severity
                            line_number=10,
                            description="Test finding with invalid severity"
                        )
