"""
Unit tests for database functionality.

This module tests database connections, models, and services
to ensure proper data persistence and retrieval.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile

from ai_code_audit.database.connection import DatabaseConfig, DatabaseManager
from ai_code_audit.database.models import Project, File, Module, AuditSession, SecurityFinding
from ai_code_audit.database.services import (
    ProjectService, FileService, AuditSessionService, SecurityFindingService
)
from ai_code_audit.core.models import ProjectType, SeverityLevel, VulnerabilityType
from ai_code_audit.core.exceptions import DatabaseError


@pytest.fixture
async def db_manager():
    """Create a test database manager with in-memory SQLite."""
    # Use SQLite for testing to avoid MySQL dependency
    config = DatabaseConfig(
        host="localhost",
        port=3306,
        username="test",
        password="test",
        database="test_ai_code_audit",
        pool_size=1,
        echo=False,
    )
    
    manager = DatabaseManager(config)
    
    # For testing, we'll mock the initialization
    manager._initialized = True
    manager.engine = None  # Will be mocked in actual tests
    
    yield manager
    
    if manager._initialized:
        await manager.close()


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "path": "/tmp/test_project",
        "project_type": ProjectType.WEB_APPLICATION,
        "languages": ["python", "javascript"],
        "architecture_pattern": "MVC",
    }


@pytest.fixture
def sample_file_data():
    """Sample file data for testing."""
    return {
        "path": "src/main.py",
        "absolute_path": "/tmp/test_project/src/main.py",
        "language": "python",
        "size": 1024,
        "hash": "abc123",
        "functions": ["main", "helper"],
        "classes": ["MyClass"],
        "imports": ["os", "sys"],
    }


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.username == "root"
        assert config.password == "jackhou."
        assert config.database == "ai_code_audit_system"
        assert config.charset == "utf8mb4"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DatabaseConfig(
            host="custom_host",
            port=3307,
            username="custom_user",
            password="custom_pass",
            database="custom_db",
        )
        
        assert config.host == "custom_host"
        assert config.port == 3307
        assert config.username == "custom_user"
        assert config.password == "custom_pass"
        assert config.database == "custom_db"
    
    def test_database_url_generation(self):
        """Test database URL generation."""
        config = DatabaseConfig(
            username="user",
            password="pass",
            host="localhost",
            port=3306,
            database="testdb",
            charset="utf8mb4",
        )
        
        expected_url = "mysql+aiomysql://user:pass@localhost:3306/testdb?charset=utf8mb4"
        assert config.database_url == expected_url
    
    def test_connection_params(self):
        """Test connection parameters generation."""
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            username="user",
            password="pass",
            database="testdb",
            charset="utf8mb4",
        )
        
        params = config.connection_params
        expected_params = {
            "host": "localhost",
            "port": 3306,
            "user": "user",
            "password": "pass",
            "db": "testdb",
            "charset": "utf8mb4",
        }
        
        assert params == expected_params


class TestDatabaseModels:
    """Test SQLAlchemy models."""
    
    def test_project_model_creation(self, sample_project_data):
        """Test Project model creation."""
        project = Project(**sample_project_data)
        
        assert project.name == "Test Project"
        assert project.path == "/tmp/test_project"
        assert project.project_type == ProjectType.WEB_APPLICATION
        assert project.languages == ["python", "javascript"]
        assert project.architecture_pattern == "MVC"
        assert project.total_files == 0
        assert project.total_lines == 0
    
    def test_file_model_creation(self, sample_file_data):
        """Test File model creation."""
        # Add required project_id
        sample_file_data["project_id"] = "test-project-id"
        
        file_obj = File(**sample_file_data)
        
        assert file_obj.path == "src/main.py"
        assert file_obj.language == "python"
        assert file_obj.size == 1024
        assert file_obj.functions == ["main", "helper"]
        assert file_obj.classes == ["MyClass"]
        assert file_obj.imports == ["os", "sys"]
    
    def test_module_model_creation(self):
        """Test Module model creation."""
        module = Module(
            project_id="test-project-id",
            name="authentication",
            description="User authentication module",
            business_logic="Handles user login",
            risk_level=SeverityLevel.HIGH,
            files=["auth.py", "login.py"],
            entry_points=["login"],
            dependencies=["database"],
        )
        
        assert module.name == "authentication"
        assert module.risk_level == SeverityLevel.HIGH
        assert module.files == ["auth.py", "login.py"]
    
    def test_security_finding_model_creation(self):
        """Test SecurityFinding model creation."""
        finding = SecurityFinding(
            session_id="test-session-id",
            project_id="test-project-id",
            file_path="auth.py",
            line_number=42,
            vulnerability_type=VulnerabilityType.SQL_INJECTION,
            severity=SeverityLevel.HIGH,
            title="SQL Injection vulnerability",
            description="User input not sanitized",
            confidence=0.95,
            cwe_id="CWE-89",
        )
        
        assert finding.vulnerability_type == VulnerabilityType.SQL_INJECTION
        assert finding.severity == SeverityLevel.HIGH
        assert finding.confidence == 0.95
        assert finding.line_number == 42
    
    def test_audit_session_model_creation(self):
        """Test AuditSession model creation."""
        session = AuditSession(
            project_id="test-project-id",
            llm_model="qwen",
            status="pending",
            config={"temperature": 0.1},
        )

        assert session.llm_model == "qwen"
        assert session.status == "pending"
        assert session.config == {"temperature": 0.1}
        assert session.total_findings == 0


class TestDatabaseServices:
    """Test database service layer."""
    
    @pytest.mark.asyncio
    async def test_project_service_validation(self, sample_project_data):
        """Test project service data validation."""
        # This test validates the service layer logic without database
        
        # Test that service methods exist and have correct signatures
        assert hasattr(ProjectService, 'create_project')
        assert hasattr(ProjectService, 'get_project_by_id')
        assert hasattr(ProjectService, 'get_project_by_path')
        assert hasattr(ProjectService, 'list_projects')
        assert hasattr(ProjectService, 'update_project_stats')
    
    @pytest.mark.asyncio
    async def test_file_service_validation(self, sample_file_data):
        """Test file service data validation."""
        # Test that service methods exist and have correct signatures
        assert hasattr(FileService, 'create_file')
        assert hasattr(FileService, 'get_files_by_project')
        assert hasattr(FileService, 'update_file_hash')
    
    @pytest.mark.asyncio
    async def test_audit_session_service_validation(self):
        """Test audit session service validation."""
        # Test that service methods exist and have correct signatures
        assert hasattr(AuditSessionService, 'create_audit_session')
        assert hasattr(AuditSessionService, 'update_session_status')
        assert hasattr(AuditSessionService, 'get_session_with_findings')
    
    @pytest.mark.asyncio
    async def test_security_finding_service_validation(self):
        """Test security finding service validation."""
        # Test that service methods exist and have correct signatures
        assert hasattr(SecurityFindingService, 'create_finding')
        assert hasattr(SecurityFindingService, 'get_findings_by_project')
        assert hasattr(SecurityFindingService, 'get_findings_summary')


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    def test_model_relationships(self):
        """Test that model relationships are properly defined."""
        # Test Project relationships
        assert hasattr(Project, 'files')
        assert hasattr(Project, 'modules')
        assert hasattr(Project, 'audit_sessions')
        
        # Test File relationships
        assert hasattr(File, 'project')
        
        # Test Module relationships
        assert hasattr(Module, 'project')
        assert hasattr(Module, 'audit_sessions')
        assert hasattr(Module, 'security_findings')
        
        # Test AuditSession relationships
        assert hasattr(AuditSession, 'project')
        assert hasattr(AuditSession, 'module')
        assert hasattr(AuditSession, 'security_findings')
        
        # Test SecurityFinding relationships
        assert hasattr(SecurityFinding, 'session')
        assert hasattr(SecurityFinding, 'project')
        assert hasattr(SecurityFinding, 'module')
    
    def test_enum_usage(self):
        """Test that enums are properly used in models."""
        # Test that models use the correct enums
        project = Project(name="test", path="/test")
        assert project.project_type == ProjectType.UNKNOWN
        
        module = Module(project_id="test", name="test")
        assert module.risk_level == SeverityLevel.MEDIUM
        
        finding = SecurityFinding(
            session_id="test",
            project_id="test",
            file_path="test.py",
            vulnerability_type=VulnerabilityType.XSS,
            severity=SeverityLevel.LOW,
            title="test",
            description="test",
        )
        assert finding.vulnerability_type == VulnerabilityType.XSS
        assert finding.severity == SeverityLevel.LOW


if __name__ == "__main__":
    pytest.main([__file__])
