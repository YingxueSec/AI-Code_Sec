"""
Unit tests for core data models.

This module tests all the Pydantic models to ensure proper validation
and serialization behavior.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from ai_code_audit.core.models import (
    ProjectType,
    SeverityLevel,
    VulnerabilityType,
    FileInfo,
    DependencyInfo,
    ProjectInfo,
    Module,
    SecurityFinding,
    AuditResult,
    CodeRequest,
    AuditContext,
    AuditRequest,
    AuditResponse,
)
from ai_code_audit.core.exceptions import ValidationError


class TestFileInfo:
    """Test FileInfo model."""
    
    def test_valid_file_info(self):
        """Test creating a valid FileInfo instance."""
        file_info = FileInfo(
            path="src/main.py",
            absolute_path="/project/src/main.py",
            language="python",
            size=1024,
            functions=["main", "helper"],
            classes=["MyClass"],
            imports=["os", "sys"]
        )
        
        assert file_info.path == "src/main.py"
        assert file_info.language == "python"
        assert file_info.size == 1024
        assert len(file_info.functions) == 2
        assert len(file_info.classes) == 1
        assert len(file_info.imports) == 2
    
    def test_empty_path_validation(self):
        """Test that empty path raises validation error."""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            FileInfo(path="", absolute_path="/test")
    
    def test_negative_size_validation(self):
        """Test that negative size raises validation error."""
        with pytest.raises(ValueError, match="File size cannot be negative"):
            FileInfo(path="test.py", absolute_path="/test.py", size=-1)
    
    def test_default_values(self):
        """Test default values are set correctly."""
        file_info = FileInfo(path="test.py", absolute_path="/test.py")
        
        assert file_info.size == 0
        assert file_info.language is None
        assert file_info.functions == []
        assert file_info.classes == []
        assert file_info.imports == []


class TestDependencyInfo:
    """Test DependencyInfo model."""
    
    def test_valid_dependency(self):
        """Test creating a valid DependencyInfo instance."""
        dep = DependencyInfo(
            name="requests",
            version="2.28.0",
            source="pip",
            vulnerabilities=["CVE-2023-1234"]
        )
        
        assert dep.name == "requests"
        assert dep.version == "2.28.0"
        assert dep.source == "pip"
        assert len(dep.vulnerabilities) == 1
    
    def test_empty_name_validation(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValueError, match="Dependency name cannot be empty"):
            DependencyInfo(name="", source="pip")


class TestProjectInfo:
    """Test ProjectInfo model."""
    
    def test_valid_project_info(self):
        """Test creating a valid ProjectInfo instance."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            project_info = ProjectInfo(
                path=temp_dir,
                name="Test Project",
                project_type=ProjectType.WEB_APPLICATION,
                languages=["python", "javascript"]
            )
            
            assert project_info.name == "Test Project"
            assert project_info.project_type == ProjectType.WEB_APPLICATION
            assert len(project_info.languages) == 2
            assert project_info.total_lines == 0
            assert isinstance(project_info.created_at, datetime)
    
    def test_empty_name_validation(self):
        """Test that empty name raises validation error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Project name cannot be empty"):
                ProjectInfo(path=temp_dir, name="")


class TestModule:
    """Test Module model."""
    
    def test_valid_module(self):
        """Test creating a valid Module instance."""
        module = Module(
            name="authentication",
            description="User authentication module",
            files=["auth.py", "login.py"],
            entry_points=["login"],
            business_logic="Handles user login and authentication",
            risk_level=SeverityLevel.HIGH
        )
        
        assert module.name == "authentication"
        assert module.risk_level == SeverityLevel.HIGH
        assert len(module.files) == 2
    
    def test_empty_name_validation(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValueError, match="Module name cannot be empty"):
            Module(name="")


class TestSecurityFinding:
    """Test SecurityFinding model."""
    
    def test_valid_security_finding(self):
        """Test creating a valid SecurityFinding instance."""
        finding = SecurityFinding(
            id="finding-001",
            type=VulnerabilityType.SQL_INJECTION,
            severity=SeverityLevel.HIGH,
            title="SQL Injection in login function",
            description="User input is not properly sanitized",
            file_path="auth.py",
            line_number=42,
            confidence=0.95,
            cwe_id="CWE-89"
        )
        
        assert finding.id == "finding-001"
        assert finding.type == VulnerabilityType.SQL_INJECTION
        assert finding.severity == SeverityLevel.HIGH
        assert finding.confidence == 0.95
        assert finding.line_number == 42
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Test invalid confidence > 1.0
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            SecurityFinding(
                id="test",
                type=VulnerabilityType.XSS,
                severity=SeverityLevel.MEDIUM,
                title="Test",
                description="Test",
                file_path="test.py",
                confidence=1.5
            )
        
        # Test invalid confidence < 0.0
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            SecurityFinding(
                id="test",
                type=VulnerabilityType.XSS,
                severity=SeverityLevel.MEDIUM,
                title="Test",
                description="Test",
                file_path="test.py",
                confidence=-0.1
            )
    
    def test_line_number_validation(self):
        """Test line number validation."""
        with pytest.raises(ValueError, match="Line number must be positive"):
            SecurityFinding(
                id="test",
                type=VulnerabilityType.XSS,
                severity=SeverityLevel.MEDIUM,
                title="Test",
                description="Test",
                file_path="test.py",
                line_number=0
            )


class TestCodeRequest:
    """Test CodeRequest model."""
    
    def test_valid_code_request(self):
        """Test creating a valid CodeRequest instance."""
        request = CodeRequest(
            file_pattern="*.py",
            reason="Need to analyze authentication logic",
            priority="high",
            context_depth=5
        )
        
        assert request.file_pattern == "*.py"
        assert request.priority == "high"
        assert request.context_depth == 5
    
    def test_context_depth_validation(self):
        """Test context depth validation."""
        with pytest.raises(ValueError, match="Context depth must be positive"):
            CodeRequest(
                file_pattern="test.py",
                reason="test",
                context_depth=0
            )


class TestAuditResult:
    """Test AuditResult model."""
    
    def test_valid_audit_result(self):
        """Test creating a valid AuditResult instance."""
        module = Module(name="test_module")
        
        result = AuditResult(
            module=module,
            model_used="qwen",
            session_id="session-123",
            confidence_score=0.85
        )
        
        assert result.module.name == "test_module"
        assert result.model_used == "qwen"
        assert result.confidence_score == 0.85
        assert isinstance(result.audit_timestamp, datetime)
    
    def test_confidence_score_validation(self):
        """Test confidence score validation."""
        module = Module(name="test_module")
        
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            AuditResult(
                module=module,
                model_used="qwen",
                session_id="session-123",
                confidence_score=1.5
            )


if __name__ == "__main__":
    pytest.main([__file__])
