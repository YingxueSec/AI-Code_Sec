#!/usr/bin/env python3
"""
Database functionality test script for AI Code Audit System.

This script tests the database connection, table creation, and basic
CRUD operations to ensure the database integration is working correctly.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_database_connection():
    """Test basic database connectivity."""
    print("🔍 Testing database connection...")
    
    try:
        from ai_code_audit.database.connection import DatabaseConfig, ensure_database_exists
        
        # Test configuration
        config = DatabaseConfig()
        print(f"✅ Database config created: {config.database}")
        
        # Ensure database exists
        await ensure_database_exists(config)
        print("✅ Database existence ensured")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


async def test_database_manager():
    """Test database manager initialization."""
    print("\n🔍 Testing database manager...")
    
    try:
        from ai_code_audit.database.connection import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig()
        manager = DatabaseManager(config)
        
        # Initialize database
        await manager.initialize()
        print("✅ Database manager initialized")
        
        # Test table creation
        await manager.create_tables()
        print("✅ Database tables created")
        
        # Test table existence check
        tables_exist = await manager.check_tables_exist()
        if tables_exist:
            print("✅ Tables existence verified")
        else:
            print("⚠️  Tables existence check failed")
        
        # Test session creation
        async with manager.get_session() as session:
            print("✅ Database session created successfully")
        
        # Clean up
        await manager.close()
        print("✅ Database manager closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database manager test failed: {e}")
        return False


async def test_database_models():
    """Test database models and relationships."""
    print("\n🔍 Testing database models...")
    
    try:
        from ai_code_audit.database.models import Project, File, Module, AuditSession, SecurityFinding
        from ai_code_audit.core.models import ProjectType, SeverityLevel, VulnerabilityType
        
        # Test Project model
        project = Project(
            name="Test Project",
            path="/tmp/test",
            project_type=ProjectType.WEB_APPLICATION,
            languages=["python", "javascript"],
        )
        print("✅ Project model created")
        
        # Test File model
        file_obj = File(
            project_id="test-id",
            path="test.py",
            absolute_path="/tmp/test/test.py",
            language="python",
            size=1024,
        )
        print("✅ File model created")
        
        # Test Module model
        module = Module(
            project_id="test-id",
            name="authentication",
            description="Auth module",
            risk_level=SeverityLevel.HIGH,
        )
        print("✅ Module model created")
        
        # Test AuditSession model
        session = AuditSession(
            project_id="test-id",
            llm_model="qwen",
            status="pending",
        )
        print("✅ AuditSession model created")
        
        # Test SecurityFinding model
        finding = SecurityFinding(
            session_id="test-session",
            project_id="test-id",
            file_path="test.py",
            vulnerability_type=VulnerabilityType.SQL_INJECTION,
            severity=SeverityLevel.HIGH,
            title="Test Finding",
            description="Test description",
            confidence=0.95,
        )
        print("✅ SecurityFinding model created")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


async def test_database_services():
    """Test database service layer."""
    print("\n🔍 Testing database services...")
    
    try:
        from ai_code_audit.database.connection import init_database, close_database
        from ai_code_audit.database.services import ProjectService, FileService
        from ai_code_audit.core.models import ProjectType
        
        # Initialize database
        db_manager = await init_database()
        await db_manager.create_tables()
        
        # Test project service
        async with db_manager.get_session() as session:
            # Create a project
            project = await ProjectService.create_project(
                session,
                name="Test Service Project",
                path="/tmp/test_service",
                project_type=ProjectType.API_SERVICE,
                languages=["python"],
            )
            print(f"✅ Project created via service: {project.id}")
            
            # Get project by ID
            retrieved_project = await ProjectService.get_project_by_id(session, project.id)
            if retrieved_project and retrieved_project.name == "Test Service Project":
                print("✅ Project retrieved via service")
            else:
                print("❌ Project retrieval failed")
                return False
            
            # Create a file
            file_obj = await FileService.create_file(
                session,
                project_id=project.id,
                path="main.py",
                absolute_path="/tmp/test_service/main.py",
                language="python",
                size=2048,
            )
            print(f"✅ File created via service: {file_obj.id}")
            
            # Get files by project
            files = await FileService.get_files_by_project(session, project.id)
            if files and len(files) == 1 and files[0].path == "main.py":
                print("✅ Files retrieved via service")
            else:
                print("❌ File retrieval failed")
                return False
        
        # Clean up
        await close_database()
        print("✅ Database services test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database services test failed: {e}")
        return False


async def test_database_crud_operations():
    """Test complete CRUD operations."""
    print("\n🔍 Testing CRUD operations...")
    
    try:
        from ai_code_audit.database.connection import init_database, close_database
        from ai_code_audit.database.services import (
            ProjectService, AuditSessionService, SecurityFindingService
        )
        from ai_code_audit.core.models import ProjectType, VulnerabilityType, SeverityLevel
        
        # Initialize database
        db_manager = await init_database()
        await db_manager.create_tables()
        
        async with db_manager.get_session() as session:
            # CREATE operations
            project = await ProjectService.create_project(
                session,
                name="CRUD Test Project",
                path="/tmp/crud_test",
                project_type=ProjectType.LIBRARY,
            )
            print("✅ CREATE: Project created")
            
            audit_session = await AuditSessionService.create_audit_session(
                session,
                project_id=project.id,
                llm_model="qwen",
                config={"temperature": 0.1},
            )
            print("✅ CREATE: Audit session created")
            
            finding = await SecurityFindingService.create_finding(
                session,
                session_id=audit_session.id,
                project_id=project.id,
                vulnerability_type=VulnerabilityType.XSS,
                severity=SeverityLevel.MEDIUM,
                title="XSS Vulnerability",
                description="Cross-site scripting issue",
                file_path="index.html",
                line_number=25,
                confidence=0.85,
            )
            print("✅ CREATE: Security finding created")
            
            # READ operations
            retrieved_project = await ProjectService.get_project_by_id(session, project.id)
            if retrieved_project:
                print("✅ READ: Project retrieved")
            
            findings = await SecurityFindingService.get_findings_by_project(
                session, project.id
            )
            if findings and len(findings) == 1:
                print("✅ READ: Findings retrieved")
            
            summary = await SecurityFindingService.get_findings_summary(
                session, project.id
            )
            if summary and summary.get('medium', 0) == 1:
                print("✅ READ: Findings summary generated")
            
            # UPDATE operations
            await AuditSessionService.update_session_status(
                session, audit_session.id, "completed", datetime.now()
            )
            print("✅ UPDATE: Session status updated")
            
            await ProjectService.update_project_stats(
                session, project.id, total_files=5, total_lines=1000
            )
            print("✅ UPDATE: Project stats updated")
        
        # Clean up
        await close_database()
        print("✅ CRUD operations test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations test failed: {e}")
        return False


async def main():
    """Run all database tests."""
    print("🚀 AI Code Audit System - Database Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Manager", test_database_manager),
        ("Database Models", test_database_models),
        ("Database Services", test_database_services),
        ("CRUD Operations", test_database_crud_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Database Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All database tests passed! Database integration is working.")
        return 0
    else:
        print("⚠️  Some database tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
