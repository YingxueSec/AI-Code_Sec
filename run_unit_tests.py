#!/usr/bin/env python3
"""
Unit test runner for AI Code Audit System.

This script runs all unit tests and provides comprehensive test reporting.
"""

import pytest
import sys
import os
from pathlib import Path
import asyncio
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_test_suite():
    """Run the complete unit test suite."""
    print("🧪 AI Code Audit System - Unit Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test configuration
    test_args = [
        "tests/unit/",
        "-v",                    # Verbose output
        "--tb=short",           # Short traceback format
        "--strict-markers",     # Strict marker checking
        "--disable-warnings",   # Disable warnings for cleaner output
        "-x",                   # Stop on first failure (optional)
        "--durations=10",       # Show 10 slowest tests
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        test_args.extend([
            "--cov=ai_code_audit",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=70"
        ])
        print("📊 Coverage reporting enabled")
    except ImportError:
        print("⚠️  Coverage reporting not available (install pytest-cov)")
    
    print()
    
    # Run tests
    start_time = time.time()
    exit_code = pytest.main(test_args)
    end_time = time.time()
    
    # Test summary
    print()
    print("=" * 60)
    print(f"Test execution completed in {end_time - start_time:.2f} seconds")
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


def run_specific_test_module(module_name):
    """Run tests for a specific module."""
    print(f"🧪 Running tests for module: {module_name}")
    print("-" * 40)
    
    test_file = f"tests/unit/test_{module_name}.py"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    test_args = [
        test_file,
        "-v",
        "--tb=short"
    ]
    
    return pytest.main(test_args)


def check_test_environment():
    """Check if the test environment is properly set up."""
    print("🔍 Checking test environment...")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 9):
        issues.append(f"Python 3.9+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check required packages
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "aiohttp",
        "sqlalchemy",
        "pydantic"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            issues.append(f"Missing required package: {package}")
    
    # Check test files exist
    test_files = [
        "tests/unit/test_audit_engine.py",
        "tests/unit/test_session_management.py",
        "tests/unit/test_llm_integration.py",
        "tests/unit/test_database_operations.py",
        "tests/unit/test_analysis_components.py"
    ]
    
    for test_file in test_files:
        if not Path(test_file).exists():
            issues.append(f"Missing test file: {test_file}")
    
    if issues:
        print("❌ Environment issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Test environment is ready")
        return True


def run_quick_smoke_tests():
    """Run a quick smoke test to verify basic functionality."""
    print("💨 Running quick smoke tests...")
    print("-" * 30)
    
    smoke_tests = [
        # Test imports
        ("Import core models", lambda: __import__("ai_code_audit.core.models")),
        ("Import audit engine", lambda: __import__("ai_code_audit.audit.engine")),
        ("Import LLM manager", lambda: __import__("ai_code_audit.llm.manager")),
        ("Import database models", lambda: __import__("ai_code_audit.database.models")),
        ("Import analysis components", lambda: __import__("ai_code_audit.analysis.semantic_analyzer")),
    ]
    
    passed = 0
    total = len(smoke_tests)
    
    for test_name, test_func in smoke_tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
    
    print(f"\nSmoke tests: {passed}/{total} passed")
    return passed == total


def main():
    """Main test runner entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            # Check environment
            if check_test_environment():
                return 0
            else:
                return 1
        
        elif command == "smoke":
            # Run smoke tests
            if run_quick_smoke_tests():
                return 0
            else:
                return 1
        
        elif command == "module":
            # Run specific module tests
            if len(sys.argv) < 3:
                print("Usage: python run_unit_tests.py module <module_name>")
                print("Available modules:")
                print("  - audit_engine")
                print("  - session_management")
                print("  - llm_integration")
                print("  - database_operations")
                print("  - analysis_components")
                return 1
            
            module_name = sys.argv[2]
            return run_specific_test_module(module_name)
        
        elif command == "help":
            print("AI Code Audit System - Unit Test Runner")
            print()
            print("Usage:")
            print("  python run_unit_tests.py [command]")
            print()
            print("Commands:")
            print("  (no command)  - Run full test suite")
            print("  check         - Check test environment")
            print("  smoke         - Run quick smoke tests")
            print("  module <name> - Run tests for specific module")
            print("  help          - Show this help message")
            print()
            print("Examples:")
            print("  python run_unit_tests.py")
            print("  python run_unit_tests.py check")
            print("  python run_unit_tests.py smoke")
            print("  python run_unit_tests.py module audit_engine")
            return 0
        
        else:
            print(f"Unknown command: {command}")
            print("Use 'python run_unit_tests.py help' for usage information")
            return 1
    
    else:
        # Run full test suite
        if not check_test_environment():
            print("\n❌ Environment check failed. Please fix issues before running tests.")
            return 1
        
        print()
        return run_test_suite()


if __name__ == "__main__":
    exit(main())
