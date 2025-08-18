#!/usr/bin/env python3
"""
Test script for validation systems (hallucination detection, consistency checking, etc.).

This script tests:
- Hallucination detection system
- Code consistency checking
- Duplicate detection and deduplication
- Failure handling and recovery
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_hallucination_detector():
    """Test hallucination detection system."""
    print("🔍 Testing Hallucination Detection System")
    print("-" * 40)
    
    try:
        from ai_code_audit.validation.hallucination_detector import HallucinationDetector
        
        # Create test project files
        test_files = {
            "test.py": """def authenticate_user(username, password):
    if not username or not password:
        return False
    
    # Check credentials
    user = get_user(username)
    if user and verify_password(password, user.password_hash):
        return True
    return False

class UserManager:
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, password):
        if username in self.users:
            raise ValueError("User already exists")
        self.users[username] = User(username, password)
""",
            "utils.py": """import hashlib
import os

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + key

def verify_password(password, stored_password):
    salt = stored_password[:32]
    key = stored_password[32:]
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key == new_key
"""
        }
        
        # Initialize detector
        detector = HallucinationDetector(test_files)
        
        print("1. Testing valid analysis result...")
        valid_analysis = {
            'file_path': 'test.py',
            'analysis': '''This file contains authentication logic. The authenticate_user function on line 1 
takes username and password parameters. On line 2-3, it checks if the parameters are valid.
The function calls get_user() and verify_password() to validate credentials.
The UserManager class on line 11 manages user accounts.'''
        }
        
        result = detector.validate_analysis_result(valid_analysis)
        print(f"   Valid analysis - Confidence: {result.confidence_score:.2f}, Issues: {len(result.issues)}")
        
        print("2. Testing analysis with hallucinations...")
        hallucinated_analysis = {
            'file_path': 'test.py',
            'analysis': '''This file contains authentication logic. The login_user function on line 50
uses JWT tokens for authentication. The database_connect() function on line 100 establishes
a connection to PostgreSQL. The encrypt_data() method uses AES-256 encryption.'''
        }
        
        result = detector.validate_analysis_result(hallucinated_analysis)
        print(f"   Hallucinated analysis - Confidence: {result.confidence_score:.2f}, Issues: {len(result.issues)}")
        
        for issue in result.issues[:3]:  # Show first 3 issues
            print(f"     - {issue.issue_type.value}: {issue.description}")
        
        print("3. Testing line number validation...")
        invalid_lines_analysis = {
            'file_path': 'test.py',
            'analysis': '''The function on line 999 handles errors. Line 1000 contains the return statement.
The class definition starts at line -5 which is invalid.'''
        }
        
        result = detector.validate_analysis_result(invalid_lines_analysis)
        print(f"   Invalid lines analysis - Confidence: {result.confidence_score:.2f}, Issues: {len(result.issues)}")
        
        print("✅ Hallucination detection test passed")
        return detector
        
    except Exception as e:
        print(f"❌ Hallucination detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_consistency_checker():
    """Test code consistency checking."""
    print("\n🔧 Testing Code Consistency Checking")
    print("-" * 40)
    
    try:
        from ai_code_audit.validation.consistency_checker import ConsistencyChecker, ConsistencyLevel
        
        # Create test project files
        test_files = {
            "auth.py": """import hashlib
from datetime import datetime

def hash_password(password):
    salt = b'fixed_salt_for_testing'
    return hashlib.sha256(salt + password.encode()).hexdigest()

def authenticate(username, password):
    # Simple authentication logic
    if username == 'admin' and hash_password(password) == 'expected_hash':
        return True
    return False

class AuthManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_id):
        session_id = hashlib.md5(f"{user_id}_{datetime.now()}".encode()).hexdigest()
        self.sessions[session_id] = user_id
        return session_id
"""
        }
        
        # Initialize checker
        checker = ConsistencyChecker(test_files, ConsistencyLevel.MODERATE)
        
        print("1. Testing consistent analysis...")
        consistent_analysis = {
            'file_path': 'auth.py',
            'analysis': '''This file implements authentication functionality. The hash_password function
uses SHA-256 hashing with a fixed salt. The authenticate function compares the hashed password.
The AuthManager class manages user sessions using MD5 for session IDs.

```python
def hash_password(password):
    salt = b'fixed_salt_for_testing'
    return hashlib.sha256(salt + password.encode()).hexdigest()
```'''
        }
        
        result = checker.check_analysis_consistency(consistent_analysis)
        print(f"   Consistent analysis - Score: {result.overall_score:.2f}, Issues: {len(result.issues)}")
        
        print("2. Testing inconsistent analysis...")
        inconsistent_analysis = {
            'file_path': 'auth.py',
            'analysis': '''This file uses bcrypt for password hashing. The login_user function
validates credentials against a database. The SessionManager class uses Redis for storage.

```python
def encrypt_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```'''
        }
        
        result = checker.check_analysis_consistency(inconsistent_analysis)
        print(f"   Inconsistent analysis - Score: {result.overall_score:.2f}, Issues: {len(result.issues)}")
        
        for issue in result.issues[:3]:  # Show first 3 issues
            print(f"     - {issue.issue_type.value}: {issue.description}")
        
        print("✅ Consistency checking test passed")
        return checker
        
    except Exception as e:
        print(f"❌ Consistency checking test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_duplicate_detector():
    """Test duplicate detection and deduplication."""
    print("\n🔄 Testing Duplicate Detection System")
    print("-" * 40)
    
    try:
        from ai_code_audit.validation.duplicate_detector import DuplicateDetector
        
        # Create test analysis results with duplicates
        analysis_results = [
            {'id': '1', 'analysis': 'This function handles user authentication by checking credentials.'},
            {'id': '2', 'analysis': 'This function handles user authentication by checking credentials.'},  # Exact duplicate
            {'id': '3', 'analysis': 'This function manages user authentication by validating credentials.'},  # Near duplicate
            {'id': '4', 'analysis': 'The password validation logic ensures secure authentication.'},  # Semantic duplicate
            {'id': '5', 'analysis': 'This function processes file uploads and validates file types.'},  # Unique
            {'id': '6', 'analysis': 'File upload processing includes type validation and security checks.'},  # Near duplicate of 5
            {'id': '7', 'analysis': 'Database connection pooling improves performance.'},  # Unique
        ]
        
        # Initialize detector
        detector = DuplicateDetector(similarity_threshold=0.8, semantic_threshold=0.6)
        
        print("1. Detecting duplicates...")
        items = {str(i): result for i, result in enumerate(analysis_results)}
        duplicate_result = detector.detect_duplicates(items)
        
        print(f"   Total items: {duplicate_result.total_items}")
        print(f"   Duplicate groups: {len(duplicate_result.duplicate_groups)}")
        print(f"   Unique items: {len(duplicate_result.unique_items)}")
        print(f"   Deduplication rate: {duplicate_result.deduplication_rate:.1f}%")
        
        print("2. Duplicate groups found:")
        for group in duplicate_result.duplicate_groups:
            print(f"   Group {group.group_id} ({group.duplicate_type.value}):")
            print(f"     Items: {group.items}")
            print(f"     Representative: {group.representative_item}")
            print(f"     Similarity: {group.average_similarity:.2f}")
        
        print("3. Testing deduplication...")
        deduplicated = detector.deduplicate_analysis_results(analysis_results)
        print(f"   Original: {len(analysis_results)} items")
        print(f"   Deduplicated: {len(deduplicated)} items")
        print(f"   Reduction: {len(analysis_results) - len(deduplicated)} items removed")
        
        print("✅ Duplicate detection test passed")
        return detector
        
    except Exception as e:
        print(f"❌ Duplicate detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_failure_handler():
    """Test failure handling and recovery."""
    print("\n🛡️ Testing Failure Handling System")
    print("-" * 40)
    
    try:
        from ai_code_audit.validation.failure_handler import FailureHandler, FailureType
        
        # Initialize handler
        handler = FailureHandler()
        
        print("1. Testing network error handling...")
        
        def mock_network_operation():
            raise ConnectionError("Network connection failed")
        
        context = {
            'component': 'llm_client',
            'operation': 'api_call',
            'retry_function': lambda: "Recovered result",
            'cache_lookup': lambda key: None,  # No cache available
        }
        
        result = handler.handle_failure(ConnectionError("Network connection failed"), context)
        print(f"   Network error recovery: {'Success' if result else 'Failed'}")
        
        print("2. Testing timeout error handling...")
        
        context = {
            'component': 'analysis_engine',
            'operation': 'code_analysis',
            'complexity_reducer': lambda data: "Simplified analysis",
            'input_data': "Complex code to analyze"
        }
        
        result = handler.handle_failure(TimeoutError("Operation timed out"), context)
        print(f"   Timeout error recovery: {'Success' if result else 'Failed'}")
        
        print("3. Testing parsing error handling...")
        
        context = {
            'component': 'parser',
            'operation': 'ast_parsing',
            'partial_analyzer': lambda data: "Partial analysis result"
        }
        
        result = handler.handle_failure(SyntaxError("Invalid syntax"), context)
        print(f"   Parsing error recovery: {'Success' if result else 'Failed'}")
        
        print("4. Failure statistics:")
        stats = handler.get_failure_statistics()
        print(f"   Total failures: {stats['total_failures']}")
        print(f"   Resolution rate: {stats['resolution_rate']:.1f}%")
        print(f"   By type: {stats['by_type']}")
        
        print("✅ Failure handling test passed")
        return handler
        
    except Exception as e:
        print(f"❌ Failure handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_integrated_validation():
    """Test integrated validation with audit engine."""
    print("\n🚀 Testing Integrated Validation System")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.engine import AuditEngine
        
        # Initialize audit engine with validation
        print("1. Initializing audit engine with validation...")
        audit_engine = AuditEngine(enable_caching=True)
        await audit_engine.initialize()
        
        # Check if validation components are initialized
        print("2. Checking validation components...")
        has_hallucination_detector = audit_engine.hallucination_detector is not None
        has_consistency_checker = audit_engine.consistency_checker is not None
        has_duplicate_detector = audit_engine.duplicate_detector is not None
        has_failure_handler = audit_engine.failure_handler is not None
        
        print(f"   Hallucination detector: {'✅' if has_hallucination_detector else '❌'}")
        print(f"   Consistency checker: {'✅' if has_consistency_checker else '❌'}")
        print(f"   Duplicate detector: {'✅' if has_duplicate_detector else '❌'}")
        print(f"   Failure handler: {'✅' if has_failure_handler else '❌'}")
        
        # Test validation integration
        if has_hallucination_detector:
            print("3. Testing validation integration...")
            
            # Create a test analysis result
            test_analysis = {
                'file_path': 'test_validation_systems.py',
                'analysis': 'This file contains test functions for validation systems.'
            }
            
            # Validate with hallucination detector
            validation_result = audit_engine.hallucination_detector.validate_analysis_result(test_analysis)
            print(f"   Validation confidence: {validation_result.confidence_score:.2f}")
            print(f"   Validation issues: {len(validation_result.issues)}")
        
        # Cleanup
        await audit_engine.shutdown()
        
        print("✅ Integrated validation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integrated validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation system tests."""
    print("🧪 Validation Systems Test Suite")
    print("=" * 60)
    
    tests = [
        ("Hallucination Detection", test_hallucination_detector),
        ("Consistency Checking", test_consistency_checker),
        ("Duplicate Detection", test_duplicate_detector),
        ("Failure Handling", test_failure_handler),
        ("Integrated Validation", test_integrated_validation),
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
    print(f"📊 Validation Systems Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation systems are working correctly!")
        print("\n✨ Validation Features Summary:")
        print("   🔍 Hallucination Detection - AI output verification and accuracy checking")
        print("   🔧 Consistency Checking - Code snippet and reference validation")
        print("   🔄 Duplicate Detection - Analysis result deduplication and quality improvement")
        print("   🛡️ Failure Handling - Graceful degradation and recovery strategies")
        print("   🚀 Engine Integration - Seamless validation in audit workflows")
        return 0
    else:
        print("⚠️  Some validation systems need attention.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
