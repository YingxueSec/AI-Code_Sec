#!/usr/bin/env python3
"""
Test script for session isolation system.

This script tests:
- Session context isolation
- Resource isolation boundaries
- Shared resource management
- Session lifecycle management
"""

import asyncio
import sys
import tempfile
import threading
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_session_context_isolation():
    """Test session context isolation."""
    print("🔒 Testing Session Context Isolation")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.session_isolation import SessionIsolationManager, IsolationLevel
        
        # Initialize isolation manager
        manager = SessionIsolationManager()
        
        print("1. Creating isolated sessions...")
        
        # Create sessions with different isolation levels
        session1 = await manager.create_session("session_1", IsolationLevel.STRICT)
        session2 = await manager.create_session("session_2", IsolationLevel.MODERATE)
        session3 = await manager.create_session("session_3", IsolationLevel.RELAXED)
        
        print(f"   Session 1: {session1.session_id} ({session1.isolation_level.value})")
        print(f"   Session 2: {session2.session_id} ({session2.isolation_level.value})")
        print(f"   Session 3: {session3.session_id} ({session3.isolation_level.value})")
        
        print("2. Verifying resource isolation...")
        
        # Check namespace isolation
        print(f"   Session 1 memory namespace: {session1.memory_namespace}")
        print(f"   Session 2 memory namespace: {session2.memory_namespace}")
        print(f"   Session 3 memory namespace: {session3.memory_namespace}")
        
        # Verify namespaces are different
        namespaces = {session1.memory_namespace, session2.memory_namespace, session3.memory_namespace}
        assert len(namespaces) == 3, "Memory namespaces should be unique"
        
        # Check temporary directory isolation
        print(f"   Session 1 temp dir: {session1.temp_directory}")
        print(f"   Session 2 temp dir: {session2.temp_directory}")
        print(f"   Session 3 temp dir: {session3.temp_directory}")
        
        # Verify temp directories exist and are different
        temp_dirs = {session1.temp_directory, session2.temp_directory, session3.temp_directory}
        assert len(temp_dirs) == 3, "Temp directories should be unique"
        
        for temp_dir in temp_dirs:
            if temp_dir:
                assert temp_dir.exists(), f"Temp directory {temp_dir} should exist"
        
        print("3. Testing session lifecycle...")
        
        # Suspend and resume session
        await manager.suspend_session("session_2")
        assert session2.is_suspended, "Session 2 should be suspended"
        assert not session2.is_active, "Session 2 should not be active"
        
        await manager.resume_session("session_2")
        assert not session2.is_suspended, "Session 2 should not be suspended"
        assert session2.is_active, "Session 2 should be active"
        
        # Destroy session
        await manager.destroy_session("session_3")
        context = manager.get_session_context("session_3")
        assert context is None, "Session 3 should be destroyed"
        
        print("✅ Session context isolation test passed")
        return manager
        
    except Exception as e:
        print(f"❌ Session context isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_resource_isolation_boundaries():
    """Test resource isolation boundaries."""
    print("\n🚧 Testing Resource Isolation Boundaries")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.session_isolation import SessionIsolationManager, IsolationLevel, ResourceType
        
        # Initialize isolation manager
        manager = SessionIsolationManager()
        
        print("1. Testing resource boundary configuration...")
        
        # Check default boundaries
        boundaries = manager.resource_boundaries
        print(f"   Configured boundaries: {len(boundaries)}")
        
        for resource_type, boundary in boundaries.items():
            print(f"   {resource_type.value}: {boundary.isolation_level.value}, "
                  f"max_size: {boundary.max_size_mb}MB, "
                  f"max_items: {boundary.max_items}")
        
        print("2. Testing namespace generation...")
        
        # Create sessions
        session1 = await manager.create_session("boundary_test_1")
        session2 = await manager.create_session("boundary_test_2")
        
        # Test namespace generation
        for resource_type in ResourceType:
            ns1 = manager.get_session_namespace("boundary_test_1", resource_type)
            ns2 = manager.get_session_namespace("boundary_test_2", resource_type)
            
            print(f"   {resource_type.value}: {ns1} vs {ns2}")
            
            if ns1 and ns2:
                assert ns1 != ns2, f"Namespaces for {resource_type.value} should be different"
        
        print("3. Testing temporary directory isolation...")
        
        # Get temp directories
        temp_dir1 = manager.get_session_temp_directory("boundary_test_1")
        temp_dir2 = manager.get_session_temp_directory("boundary_test_2")
        
        print(f"   Session 1 temp: {temp_dir1}")
        print(f"   Session 2 temp: {temp_dir2}")
        
        # Verify isolation
        assert temp_dir1 != temp_dir2, "Temp directories should be different"
        assert temp_dir1.exists(), "Session 1 temp directory should exist"
        assert temp_dir2.exists(), "Session 2 temp directory should exist"
        
        # Test file creation in isolated directories
        test_file1 = temp_dir1 / "test_file.txt"
        test_file2 = temp_dir2 / "test_file.txt"
        
        test_file1.write_text("Session 1 data")
        test_file2.write_text("Session 2 data")
        
        assert test_file1.read_text() == "Session 1 data"
        assert test_file2.read_text() == "Session 2 data"
        
        print("4. Testing cleanup...")
        
        # Destroy sessions and verify cleanup
        await manager.destroy_session("boundary_test_1")
        await manager.destroy_session("boundary_test_2")
        
        # Temp directories should be cleaned up
        assert not temp_dir1.exists(), "Session 1 temp directory should be cleaned up"
        assert not temp_dir2.exists(), "Session 2 temp directory should be cleaned up"
        
        print("✅ Resource isolation boundaries test passed")
        return True
        
    except Exception as e:
        print(f"❌ Resource isolation boundaries test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_shared_resource_management():
    """Test shared resource management."""
    print("\n🤝 Testing Shared Resource Management")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.session_isolation import SessionIsolationManager, ResourceType
        
        # Initialize isolation manager
        manager = SessionIsolationManager()
        
        print("1. Creating sessions and shared resources...")
        
        # Create sessions
        await manager.create_session("shared_test_1")
        await manager.create_session("shared_test_2")
        await manager.create_session("shared_test_3")
        
        # Create shared resources
        shared_data = {"key1": "value1", "key2": "value2"}
        resource = manager.create_shared_resource(
            "test_resource", ResourceType.MEMORY, shared_data
        )
        
        print(f"   Created shared resource: {resource.resource_id}")
        print(f"   Resource type: {resource.resource_type.value}")
        print(f"   Initial data: {resource.data}")
        
        print("2. Testing access control...")
        
        # Grant permissions
        manager.grant_resource_access("shared_test_1", "test_resource", {"read", "write"})
        manager.grant_resource_access("shared_test_2", "test_resource", {"read"})
        # shared_test_3 has no permissions
        
        # Test read access
        data1 = manager.access_shared_resource("shared_test_1", "test_resource", "read")
        data2 = manager.access_shared_resource("shared_test_2", "test_resource", "read")
        
        assert data1 == shared_data, "Session 1 should be able to read"
        assert data2 == shared_data, "Session 2 should be able to read"
        
        print("   Read access working correctly")
        
        # Test write access
        new_data = {"key1": "updated_value1", "key3": "value3"}
        success = manager.update_shared_resource("shared_test_1", "test_resource", new_data)
        assert success, "Session 1 should be able to write"
        
        # Verify update
        updated_data = manager.access_shared_resource("shared_test_1", "test_resource", "read")
        assert updated_data == new_data, "Data should be updated"
        
        print("   Write access working correctly")
        
        # Test permission denial
        try:
            manager.update_shared_resource("shared_test_2", "test_resource", {"denied": "data"})
            assert False, "Session 2 should not be able to write"
        except PermissionError:
            print("   Permission denial working correctly")
        
        try:
            manager.access_shared_resource("shared_test_3", "test_resource", "read")
            assert False, "Session 3 should not be able to read"
        except PermissionError:
            print("   Access control working correctly")
        
        print("3. Testing concurrent access...")
        
        # Test concurrent access with threading
        access_results = []
        
        def concurrent_access(session_id, resource_id):
            try:
                data = manager.access_shared_resource(session_id, resource_id, "read")
                access_results.append((session_id, "success", data))
            except Exception as e:
                access_results.append((session_id, "error", str(e)))
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_access, args=("shared_test_1", "test_resource"))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        successful_accesses = [r for r in access_results if r[1] == "success"]
        print(f"   Concurrent accesses: {len(successful_accesses)}/5 successful")
        
        assert len(successful_accesses) == 5, "All concurrent accesses should succeed"
        
        print("4. Testing resource cleanup...")
        
        # Revoke access and destroy sessions
        manager.revoke_resource_access("shared_test_1", "test_resource")
        manager.revoke_resource_access("shared_test_2", "test_resource")
        
        await manager.destroy_session("shared_test_1")
        await manager.destroy_session("shared_test_2")
        await manager.destroy_session("shared_test_3")
        
        # Check that resource permissions are cleaned up
        resource = manager.shared_resources["test_resource"]
        assert len(resource.access_permissions) == 0, "Resource permissions should be cleaned up"
        
        print("✅ Shared resource management test passed")
        return True
        
    except Exception as e:
        print(f"❌ Shared resource management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_lifecycle_management():
    """Test session lifecycle management."""
    print("\n♻️ Testing Session Lifecycle Management")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.session_isolation import SessionIsolationManager, IsolationLevel
        
        # Initialize isolation manager
        manager = SessionIsolationManager()
        
        print("1. Testing session creation and tracking...")
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = await manager.create_session(f"lifecycle_test_{i}")
            sessions.append(session)
        
        print(f"   Created {len(sessions)} sessions")
        
        # Check active sessions
        stats = manager.get_isolation_stats()
        assert stats["active_sessions"] == 3, "Should have 3 active sessions"
        assert stats["suspended_sessions"] == 0, "Should have 0 suspended sessions"
        
        print("2. Testing session suspension and resumption...")
        
        # Suspend sessions
        await manager.suspend_session("lifecycle_test_0")
        await manager.suspend_session("lifecycle_test_1")
        
        stats = manager.get_isolation_stats()
        assert stats["active_sessions"] == 1, "Should have 1 active session"
        assert stats["suspended_sessions"] == 2, "Should have 2 suspended sessions"
        
        # Resume one session
        await manager.resume_session("lifecycle_test_0")
        
        stats = manager.get_isolation_stats()
        assert stats["active_sessions"] == 2, "Should have 2 active sessions"
        assert stats["suspended_sessions"] == 1, "Should have 1 suspended session"
        
        print("   Suspension and resumption working correctly")
        
        print("3. Testing session statistics...")
        
        # Get session stats
        for i in range(3):
            session_id = f"lifecycle_test_{i}"
            session_stats = manager.get_session_stats(session_id)
            
            if session_stats:
                print(f"   Session {session_id}:")
                print(f"     Active: {session_stats['is_active']}")
                print(f"     Suspended: {session_stats['is_suspended']}")
                print(f"     Isolation: {session_stats['isolation_level']}")
                print(f"     Memory namespace: {session_stats['memory_namespace']}")
        
        print("4. Testing session destruction...")
        
        # Destroy all sessions
        for i in range(3):
            session_id = f"lifecycle_test_{i}"
            success = await manager.destroy_session(session_id)
            assert success, f"Should be able to destroy session {session_id}"
        
        # Verify all sessions are destroyed
        stats = manager.get_isolation_stats()
        assert stats["active_sessions"] == 0, "Should have 0 active sessions"
        assert stats["suspended_sessions"] == 0, "Should have 0 suspended sessions"
        
        print("   Session destruction working correctly")
        
        print("✅ Session lifecycle management test passed")
        return True
        
    except Exception as e:
        print(f"❌ Session lifecycle management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integrated_session_isolation():
    """Test integrated session isolation with audit engine."""
    print("\n🚀 Testing Integrated Session Isolation")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.engine import AuditEngine
        from ai_code_audit.audit.session_isolation import IsolationLevel
        
        print("1. Initializing audit engine with session isolation...")
        
        # Initialize audit engine
        audit_engine = AuditEngine(enable_caching=True)
        await audit_engine.initialize()
        
        # Check if session isolation is initialized
        assert audit_engine.session_isolation is not None, "Session isolation should be initialized"
        
        print("2. Testing isolated session creation...")
        
        # Create isolated sessions
        success1 = await audit_engine.create_isolated_session("audit_session_1", IsolationLevel.STRICT)
        success2 = await audit_engine.create_isolated_session("audit_session_2", IsolationLevel.MODERATE)
        
        assert success1, "Should be able to create session 1"
        assert success2, "Should be able to create session 2"
        
        print("   Created 2 isolated audit sessions")
        
        print("3. Testing session statistics...")
        
        # Get isolation stats
        isolation_stats = audit_engine.get_isolation_stats()
        print(f"   Active sessions: {isolation_stats['active_sessions']}")
        print(f"   Default isolation: {isolation_stats['default_isolation_level']}")
        
        # Get session-specific stats
        session1_stats = audit_engine.get_session_stats("audit_session_1")
        session2_stats = audit_engine.get_session_stats("audit_session_2")
        
        assert session1_stats is not None, "Should get stats for session 1"
        assert session2_stats is not None, "Should get stats for session 2"
        
        print(f"   Session 1 isolation: {session1_stats['isolation_level']}")
        print(f"   Session 2 isolation: {session2_stats['isolation_level']}")
        
        print("4. Testing session lifecycle through engine...")
        
        # Suspend and resume through engine
        suspend_success = await audit_engine.suspend_session("audit_session_1")
        assert suspend_success, "Should be able to suspend session"
        
        resume_success = await audit_engine.resume_session("audit_session_1")
        assert resume_success, "Should be able to resume session"
        
        # Destroy sessions
        destroy1 = await audit_engine.destroy_session("audit_session_1")
        destroy2 = await audit_engine.destroy_session("audit_session_2")
        
        assert destroy1, "Should be able to destroy session 1"
        assert destroy2, "Should be able to destroy session 2"
        
        print("   Session lifecycle management working through engine")
        
        # Cleanup
        await audit_engine.shutdown()
        
        print("✅ Integrated session isolation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integrated session isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all session isolation tests."""
    print("🔒 Session Isolation Test Suite")
    print("=" * 60)
    
    tests = [
        ("Session Context Isolation", test_session_context_isolation),
        ("Resource Isolation Boundaries", test_resource_isolation_boundaries),
        ("Shared Resource Management", test_shared_resource_management),
        ("Session Lifecycle Management", test_session_lifecycle_management),
        ("Integrated Session Isolation", test_integrated_session_isolation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result is not None and result is not False:
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🔒 Session Isolation Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All session isolation features are working correctly!")
        print("\n✨ Session Isolation Features Summary:")
        print("   🔒 Context Isolation - Independent session contexts with unique namespaces")
        print("   🚧 Resource Boundaries - Memory, cache, and file system isolation")
        print("   🤝 Shared Resources - Controlled access to shared data with permissions")
        print("   ♻️ Lifecycle Management - Session creation, suspension, resumption, destruction")
        print("   🚀 Engine Integration - Seamless integration with audit engine")
        return 0
    else:
        print("⚠️  Some session isolation features need attention.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
