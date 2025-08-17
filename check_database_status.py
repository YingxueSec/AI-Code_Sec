#!/usr/bin/env python3
"""
Quick database status check script.

This script provides a simple way to check if the database is properly
set up and working.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    """Check database status."""
    print("🔍 AI Code Audit System - Database Status Check")
    print("=" * 50)
    
    try:
        from ai_code_audit.database.connection import DatabaseConfig, DatabaseManager
        
        # Create configuration
        config = DatabaseConfig()
        print(f"📋 Database: {config.database}")
        print(f"📋 Host: {config.host}:{config.port}")
        
        # Test connection
        print("\n🔧 Testing database connection...")
        manager = DatabaseManager(config)
        await manager.initialize()
        print("✅ Database connection successful")
        
        # Check tables
        print("\n🔍 Checking tables...")
        tables_exist = await manager.check_tables_exist()
        if tables_exist:
            print("✅ Tables exist")
        else:
            print("❌ Tables do not exist")
            print("   Run: python scripts/init_database.py")
            return 1
        
        # Test basic operations
        print("\n🔧 Testing basic operations...")
        async with manager.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT COUNT(*) FROM projects"))
            count = result.scalar()
            print(f"✅ Projects table accessible (count: {count})")
        
        await manager.close()
        print("\n✅ Database is ready for use!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Database check failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure MySQL is running")
        print("2. Check database credentials")
        print("3. Run: python scripts/init_database.py")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
