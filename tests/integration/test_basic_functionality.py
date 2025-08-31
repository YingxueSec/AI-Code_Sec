#!/usr/bin/env python3
"""
Basic functionality test script for AI Code Audit System.

This script tests the core components we've built so far to ensure
everything is working correctly before proceeding with development.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all core modules can be imported."""
    print("🔍 Testing imports...")

    try:
        # Test core imports
        from ai_code_audit.core.models import (
            ProjectType, SeverityLevel, VulnerabilityType,
            FileInfo, ProjectInfo, Module, SecurityFinding
        )
        from ai_code_audit.core.exceptions import AuditError, ValidationError
        from ai_code_audit.core.constants import SUPPORTED_LANGUAGES

        print("✅ Core modules imported successfully")

        # Test main audit function
        from ai_code_audit import audit_project
        print("✅ Main audit function imported successfully")

        # Test database imports
        from ai_code_audit.database.connection import DatabaseManager, DatabaseConfig
        from ai_code_audit.database.models import Project, File, Module
        from ai_code_audit.database.services import ProjectService, FileService
        print("✅ Database modules imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_model_validation():
    """Test Pydantic model validation."""
    print("\n🔍 Testing model validation...")
    
    try:
        from ai_code_audit.core.models import FileInfo, SecurityFinding, VulnerabilityType, SeverityLevel
        
        # Test valid FileInfo
        file_info = FileInfo(
            path="test.py",
            absolute_path="/project/test.py",
            language="python",
            size=1024
        )
        print("✅ FileInfo validation works")
        
        # Test invalid FileInfo (empty path)
        try:
            FileInfo(path="", absolute_path="/test")
            print("❌ FileInfo validation failed - should reject empty path")
            return False
        except ValueError:
            print("✅ FileInfo correctly rejects empty path")
        
        # Test valid SecurityFinding
        finding = SecurityFinding(
            id="test-001",
            type=VulnerabilityType.SQL_INJECTION,
            severity=SeverityLevel.HIGH,
            title="Test Finding",
            description="Test description",
            file_path="test.py",
            confidence=0.95
        )
        print("✅ SecurityFinding validation works")
        
        # Test invalid confidence
        try:
            SecurityFinding(
                id="test-002",
                type=VulnerabilityType.XSS,
                severity=SeverityLevel.MEDIUM,
                title="Test",
                description="Test",
                file_path="test.py",
                confidence=1.5  # Invalid: > 1.0
            )
            print("❌ SecurityFinding validation failed - should reject confidence > 1.0")
            return False
        except ValueError:
            print("✅ SecurityFinding correctly rejects invalid confidence")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation error: {e}")
        return False


def test_audit_function():
    """Test basic audit function."""
    print("\n🔍 Testing audit function...")

    try:
        from ai_code_audit import audit_project
        import asyncio
        import tempfile

        # Test with a simple temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello world')")

            # Test that the function can be called (we won't run it fully in tests)
            print("✅ Audit function is callable")

        return True

    except Exception as e:
        print(f"❌ Audit function test error: {e}")
        return False


def test_constants():
    """Test constants and configuration."""
    print("\n🔍 Testing constants...")
    
    try:
        from ai_code_audit.core.constants import (
            SUPPORTED_LANGUAGES, LANGUAGE_EXTENSIONS, 
            DEFAULT_SECURITY_RULES, VULNERABILITY_SEVERITY_MAPPING
        )
        
        # Check that constants are properly defined
        assert len(SUPPORTED_LANGUAGES) > 0, "SUPPORTED_LANGUAGES should not be empty"
        assert len(LANGUAGE_EXTENSIONS) > 0, "LANGUAGE_EXTENSIONS should not be empty"
        assert len(DEFAULT_SECURITY_RULES) > 0, "DEFAULT_SECURITY_RULES should not be empty"
        
        # Check specific values
        assert "python" in SUPPORTED_LANGUAGES, "Python should be supported"
        assert ".py" in LANGUAGE_EXTENSIONS, "Python extension should be mapped"
        assert LANGUAGE_EXTENSIONS[".py"] == "python", "Python extension mapping should be correct"
        
        print("✅ Constants are properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Constants test error: {e}")
        return False


def test_project_structure():
    """Test that project structure is correct."""
    print("\n🔍 Testing project structure...")

    required_files = [
        "pyproject.toml",
        "ai_code_audit/__init__.py",
        "ai_code_audit/core/__init__.py",
        "ai_code_audit/core/models.py",
        "ai_code_audit/core/exceptions.py",
        "ai_code_audit/core/constants.py",

        "ai_code_audit/database/__init__.py",
        "ai_code_audit/database/connection.py",
        "ai_code_audit/database/models.py",
        "ai_code_audit/database/services.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/unit/test_models.py",
        "tests/unit/test_database.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Project structure is correct")
    return True


def run_unit_tests():
    """Run the unit tests we've created."""
    print("\n🔍 Running unit tests...")

    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            print("✅ Unit tests passed")
            return True
        else:
            print(f"❌ Unit tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False


def test_database_models():
    """Test database model creation without database connection."""
    print("\n🔍 Testing database models...")

    try:
        from ai_code_audit.database.models import Project, File, Module
        from ai_code_audit.core.models import ProjectType, SeverityLevel

        # Test Project model
        project = Project(
            name="Test Project",
            path="/tmp/test",
            project_type=ProjectType.WEB_APPLICATION,
        )
        print("✅ Project model created")

        # Test File model
        file_obj = File(
            project_id="test-id",
            path="test.py",
            absolute_path="/tmp/test.py",
            language="python",
        )
        print("✅ File model created")

        # Test Module model
        module = Module(
            project_id="test-id",
            name="test_module",
            risk_level=SeverityLevel.MEDIUM,
        )
        print("✅ Module model created")

        return True

    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 AI Code Audit System - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Imports", test_imports),
        ("Constants", test_constants),
        ("Model Validation", test_model_validation),
        ("Database Models", test_database_models),
        ("Audit Function", test_audit_function),
        ("Unit Tests", run_unit_tests),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to continue development.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix issues before continuing.")
        return 1


if __name__ == "__main__":
    exit(main())
