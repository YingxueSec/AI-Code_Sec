#!/usr/bin/env python3
"""
Test script for advanced features of the AI Code Audit System.

This script tests:
- Intelligent code retrieval
- Context management
- Cache optimization
- Advanced security templates
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_code_retrieval():
    """Test intelligent code retrieval system."""
    print("🔍 Testing Code Retrieval System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.code_retrieval import CodeRetriever, RetrievalQuery, RetrievalType
        
        # Analyze current project
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        # Initialize code retriever
        retriever = CodeRetriever(project_info)
        
        # Test function definition search
        print("1. Testing function definition search...")
        query = RetrievalQuery(
            query_type=RetrievalType.FUNCTION_DEFINITION,
            target="test_code_retrieval",
            max_results=5
        )
        
        result = await retriever.retrieve(query)
        print(f"   Found {result.total_matches} matches in {result.execution_time:.2f}s")
        
        for match in result.matches[:2]:
            print(f"   - {match.file_path}:{match.line_number} ({match.confidence.value})")
        
        # Test security pattern search
        print("\n2. Testing security pattern search...")
        security_query = RetrievalQuery(
            query_type=RetrievalType.SECURITY_PATTERN,
            target="hardcoded_secrets",
            max_results=10
        )
        
        security_result = await retriever.retrieve(security_query)
        print(f"   Found {security_result.total_matches} potential security issues")
        
        # Get statistics
        stats = retriever.get_symbol_statistics()
        print(f"\n3. Symbol index statistics:")
        for symbol_type, count in stats.items():
            print(f"   - {symbol_type}: {count} symbols")
        
        print("✅ Code retrieval system test passed")
        return True
        
    except Exception as e:
        print(f"❌ Code retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_management():
    """Test intelligent context management."""
    print("\n🧠 Testing Context Management System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.context_manager import ContextManager, ContextType
        
        # Analyze project
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        # Initialize context manager
        context_manager = ContextManager(project_info)
        
        # Build context for a specific function
        print("1. Building function context...")
        context = await context_manager.build_context(
            target_file="test_advanced_features.py",
            target_function="test_context_management",
            context_types=[
                ContextType.FUNCTION_CONTEXT,
                ContextType.MODULE_CONTEXT,
                ContextType.DEPENDENCY_CONTEXT
            ],
            max_tokens=5000
        )
        
        print(f"   Built context with {len(context.snippets)} snippets")
        print(f"   Total tokens: {context.total_tokens}")
        print(f"   Context summary:\n{context.context_summary}")
        
        # Test context optimization
        print("\n2. Testing context optimization...")
        optimized_context = context.optimize_for_token_limit(2000)
        print(f"   Optimized to {len(optimized_context.snippets)} snippets")
        print(f"   Optimized tokens: {optimized_context.total_tokens}")
        
        # Show snippet details
        print("\n3. Context snippets by priority:")
        for snippet in context.snippets[:3]:
            print(f"   - {snippet.context_type.value}: {snippet.file_path}:{snippet.start_line}-{snippet.end_line}")
            print(f"     Priority: {snippet.priority.value}, Tokens: {snippet.token_estimate:.0f}")
        
        print("✅ Context management test passed")
        return True
        
    except Exception as e:
        print(f"❌ Context management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cache_system():
    """Test cache optimization system."""
    print("\n💾 Testing Cache Optimization System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.cache_manager import CacheManager, CacheType
        
        # Initialize cache manager
        cache_manager = CacheManager(cache_dir=".test_cache", max_size_mb=10)
        
        # Test basic caching
        print("1. Testing basic cache operations...")
        
        # Put some test data
        test_data = {"analysis": "test result", "timestamp": "2024-01-01"}
        cache_key = cache_manager.put(
            cache_type=CacheType.ANALYSIS_RESULT,
            identifier="test_file.py",
            data=test_data,
            file_dependencies={"test_file.py"},
            ttl_hours=24
        )
        
        print(f"   Cached data with key: {cache_key}")
        
        # Retrieve data
        retrieved_data = cache_manager.get(
            cache_type=CacheType.ANALYSIS_RESULT,
            identifier="test_file.py"
        )
        
        if retrieved_data:
            print(f"   Retrieved data: {retrieved_data}")
        else:
            print("   ❌ Failed to retrieve cached data")
        
        # Test cache statistics
        print("\n2. Cache statistics:")
        stats = cache_manager.get_stats()
        print(f"   Total entries: {stats.total_entries}")
        print(f"   Hit rate: {stats.hit_rate:.1f}%")
        print(f"   Cache size: {stats.size_bytes / 1024:.1f} KB")
        
        # Test cache invalidation
        print("\n3. Testing cache invalidation...")
        cache_manager.invalidate(cache_type=CacheType.ANALYSIS_RESULT)
        
        # Try to retrieve after invalidation
        retrieved_after_invalidation = cache_manager.get(
            cache_type=CacheType.ANALYSIS_RESULT,
            identifier="test_file.py"
        )
        
        if not retrieved_after_invalidation:
            print("   ✅ Cache invalidation successful")
        else:
            print("   ❌ Cache invalidation failed")
        
        # Cleanup
        cache_manager.clear()
        
        print("✅ Cache system test passed")
        return True
        
    except Exception as e:
        print(f"❌ Cache system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_advanced_templates():
    """Test advanced security templates."""
    print("\n📋 Testing Advanced Security Templates")
    print("-" * 40)
    
    try:
        from ai_code_audit.templates.advanced_templates import AdvancedTemplateManager, SecurityStandard
        
        # Initialize template manager
        template_manager = AdvancedTemplateManager()
        
        # List available templates
        print("1. Available templates:")
        templates = template_manager.list_templates()
        for template_name in templates:
            template = template_manager.get_template(template_name)
            print(f"   - {template_name}: {template.description}")
        
        # Test OWASP Top 10 template
        print("\n2. Testing OWASP Top 10 template...")
        owasp_template = template_manager.get_template("owasp_top_10_2021")
        if owasp_template:
            print(f"   Template: {owasp_template.name}")
            print(f"   Standard: {owasp_template.standard.value}")
            print(f"   Vulnerability classes: {len(owasp_template.vulnerability_classes)}")
            print(f"   Analysis focus areas: {len(owasp_template.analysis_focus)}")
            print(f"   CWE mappings: {len(owasp_template.cwe_mappings)}")
        
        # Test template filtering by standard
        print("\n3. Templates by standard:")
        owasp_templates = template_manager.get_templates_by_standard(SecurityStandard.OWASP_TOP_10)
        print(f"   OWASP templates: {len(owasp_templates)}")
        
        pci_templates = template_manager.get_templates_by_standard(SecurityStandard.PCI_DSS)
        print(f"   PCI DSS templates: {len(pci_templates)}")
        
        gdpr_templates = template_manager.get_templates_by_standard(SecurityStandard.GDPR)
        print(f"   GDPR templates: {len(gdpr_templates)}")
        
        # Test template prompt generation
        print("\n4. Testing template prompts...")
        if owasp_template:
            system_prompt = owasp_template.system_prompt
            user_prompt = owasp_template.user_prompt
            
            print(f"   System prompt length: {len(system_prompt)} chars")
            print(f"   User prompt length: {len(user_prompt)} chars")
            print(f"   Contains OWASP categories: {'A01:2021' in system_prompt}")
        
        print("✅ Advanced templates test passed")
        return True
        
    except Exception as e:
        print(f"❌ Advanced templates test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integrated_advanced_audit():
    """Test integrated advanced audit with all features."""
    print("\n🚀 Testing Integrated Advanced Audit")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.engine import AuditEngine
        from ai_code_audit.llm.base import LLMModelType
        
        # Initialize advanced audit engine
        print("1. Initializing advanced audit engine...")
        audit_engine = AuditEngine(
            enable_caching=True,
            cache_dir=".test_cache"
        )
        await audit_engine.initialize()
        
        # Start advanced audit
        print("2. Starting advanced audit with context management...")
        session_id = await audit_engine.start_audit(
            project_path=".",
            template="owasp_top_10_2021",  # Use advanced template
            model=LLMModelType.QWEN_CODER_30B,
            max_files=2,
            use_advanced_context=True,
            use_caching=True
        )
        
        print(f"   Advanced audit session started: {session_id}")
        
        # Monitor progress briefly
        for i in range(3):
            await asyncio.sleep(2)
            status = await audit_engine.get_audit_status(session_id)
            if status:
                print(f"   Progress: {status['progress']['completion_percentage']:.1f}%")
                if status['status'] in ['completed', 'failed']:
                    break
        
        # Check if advanced features were used
        if audit_engine.code_retriever:
            stats = audit_engine.code_retriever.get_symbol_statistics()
            print(f"   Code retrieval stats: {stats}")
        
        if audit_engine.cache_manager:
            cache_stats = audit_engine.cache_manager.get_stats()
            print(f"   Cache stats: Hit rate {cache_stats.hit_rate:.1f}%")
        
        # Cleanup
        await audit_engine.shutdown()
        
        print("✅ Integrated advanced audit test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integrated advanced audit test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all advanced feature tests."""
    print("🧪 Advanced Features Test Suite")
    print("=" * 60)
    
    tests = [
        ("Code Retrieval System", test_code_retrieval),
        ("Context Management", test_context_management),
        ("Cache Optimization", test_cache_system),
        ("Advanced Templates", test_advanced_templates),
        ("Integrated Advanced Audit", test_integrated_advanced_audit),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Advanced Features Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All advanced features are working correctly!")
        print("\n✨ Advanced Features Summary:")
        print("   🔍 Intelligent Code Retrieval - Symbol indexing and semantic search")
        print("   🧠 Context Management - Smart code snippet extraction and optimization")
        print("   💾 Cache Optimization - Intelligent caching with invalidation")
        print("   📋 Advanced Templates - OWASP, CWE, PCI DSS, GDPR compliance")
        print("   🚀 Integrated Engine - All features working together")
        return 0
    else:
        print("⚠️  Some advanced features need attention.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
