#!/usr/bin/env python3
"""
Database initialization script for AI Code Audit System.

This script creates the database, tables, and performs initial setup.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def main():
    """Initialize the database."""
    print("🚀 AI Code Audit System - Database Initialization")
    print("=" * 50)
    
    try:
        from ai_code_audit.database.connection import (
            DatabaseConfig, DatabaseManager, ensure_database_exists
        )
        
        # Create configuration
        config = DatabaseConfig()
        print(f"📋 Database: {config.database}")
        print(f"📋 Host: {config.host}:{config.port}")
        print(f"📋 User: {config.username}")
        
        # Ensure database exists
        print("\n🔧 Ensuring database exists...")
        await ensure_database_exists(config)
        print("✅ Database ensured to exist")
        
        # Initialize database manager
        print("\n🔧 Initializing database manager...")
        manager = DatabaseManager(config)
        await manager.initialize()
        print("✅ Database manager initialized")
        
        # Create tables
        print("\n🔧 Creating database tables...")
        await manager.create_tables()
        print("✅ Database tables created")
        
        # Verify tables
        print("\n🔍 Verifying table creation...")
        tables_exist = await manager.check_tables_exist()
        if tables_exist:
            print("✅ Tables verified successfully")
        else:
            print("❌ Table verification failed")
            return 1
        
        # Test basic operations
        print("\n🔍 Testing basic database operations...")
        async with manager.get_session() as session:
            from ai_code_audit.database.services import ProjectService
            from ai_code_audit.core.models import ProjectType
            
            # Create a test project
            project = await ProjectService.create_project(
                session,
                name="Database Test Project",
                path="/tmp/db_test",
                project_type=ProjectType.LIBRARY,
            )
            print(f"✅ Test project created: {project.id}")
            
            # Retrieve the project
            retrieved = await ProjectService.get_project_by_id(session, project.id)
            if retrieved and retrieved.name == "Database Test Project":
                print("✅ Test project retrieved successfully")
            else:
                print("❌ Test project retrieval failed")
                return 1
        
        # Clean up
        await manager.close()
        print("\n✅ Database initialization completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Run: python test_database_functionality.py")
        print("   2. Test with: ai-audit init sample_project")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
