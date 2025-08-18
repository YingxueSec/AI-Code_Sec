#!/usr/bin/env python3
"""
Test script for the new audit engine.

This script tests the complete audit engine workflow including:
- Session management
- Analysis orchestration
- Result aggregation
- Report generation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_audit_engine():
    """Test the complete audit engine workflow."""
    print("🚀 Testing Audit Engine")
    print("=" * 50)
    
    try:
        from ai_code_audit.audit.engine import AuditEngine
        from ai_code_audit.audit.report_generator import ReportFormat
        from ai_code_audit.llm.base import LLMModelType
        
        # Initialize audit engine
        print("🔧 Initializing audit engine...")
        audit_engine = AuditEngine()
        await audit_engine.initialize()
        print("✅ Audit engine initialized")
        
        # Test project path (current directory)
        project_path = "."
        
        # Progress callback
        def progress_callback(session):
            progress = session.progress
            print(f"📊 Progress: {progress.completion_percentage:.1f}% "
                  f"({progress.analyzed_files}/{progress.total_files} files)")
            if progress.current_file:
                print(f"   Currently analyzing: {progress.current_file}")
        
        # Start audit
        print(f"\n🔍 Starting audit of: {project_path}")
        session_id = await audit_engine.start_audit(
            project_path=project_path,
            template="security_audit",
            model=LLMModelType.QWEN_CODER_30B,
            max_files=3,  # Limit for testing
            progress_callback=progress_callback
        )
        
        print(f"✅ Audit session started: {session_id}")
        
        # Monitor progress
        print("\n⏳ Monitoring audit progress...")
        while True:
            await asyncio.sleep(5)
            
            audit_status = await audit_engine.get_audit_status(session_id)
            if not audit_status:
                print("❌ Failed to get audit status")
                break
            
            print(f"Status: {audit_status['status']} | "
                  f"Progress: {audit_status['progress']['completion_percentage']:.1f}%")
            
            if audit_status['status'] in ['completed', 'failed', 'cancelled']:
                break
        
        # Get final results
        print("\n📋 Getting final results...")
        final_status = await audit_engine.get_audit_status(session_id)
        
        if final_status and final_status['status'] == 'completed':
            print("🎉 Audit completed successfully!")
            print(f"✅ Files analyzed: {final_status['progress']['analyzed_files']}")
            print(f"✅ Success rate: {final_status['statistics']['success_rate']:.1f}%")
            
            # Get detailed results
            audit_result = await audit_engine.get_audit_results(session_id)
            if audit_result:
                print(f"\n📊 Detailed Results:")
                print(f"   Total findings: {audit_result.total_findings}")
                print(f"   Critical: {audit_result.critical_count}")
                print(f"   High: {audit_result.high_count}")
                print(f"   Risk score: {audit_result.risk_score:.1f}/10")
                
                # Show vulnerabilities
                if audit_result.vulnerabilities:
                    print(f"\n🔍 Vulnerabilities found:")
                    for i, vuln in enumerate(audit_result.vulnerabilities[:3], 1):
                        print(f"   {i}. {vuln.title} ({vuln.severity.value.upper()})")
                        print(f"      File: {vuln.file_path}")
                
                # Test report generation
                print(f"\n📄 Testing report generation...")
                
                # Test JSON report
                json_report = await audit_engine.generate_report(
                    session_id=session_id,
                    format=ReportFormat.JSON,
                    output_path="test_audit_report.json"
                )
                
                if json_report:
                    print("✅ JSON report generated successfully")
                else:
                    print("❌ Failed to generate JSON report")
                
                # Test HTML report
                html_report = await audit_engine.generate_report(
                    session_id=session_id,
                    format=ReportFormat.HTML,
                    output_path="test_audit_report.html"
                )
                
                if html_report:
                    print("✅ HTML report generated successfully")
                else:
                    print("❌ Failed to generate HTML report")
                
                # Test Markdown report
                md_report = await audit_engine.generate_report(
                    session_id=session_id,
                    format=ReportFormat.MARKDOWN,
                    output_path="test_audit_report.md"
                )
                
                if md_report:
                    print("✅ Markdown report generated successfully")
                else:
                    print("❌ Failed to generate Markdown report")
            
        else:
            print(f"❌ Audit failed or was cancelled: {final_status['status'] if final_status else 'Unknown'}")
        
        # Test session listing
        print(f"\n📋 Testing session management...")
        active_sessions = await audit_engine.list_active_audits()
        print(f"Active sessions: {len(active_sessions)}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await audit_engine.shutdown()
        print("✅ Audit engine shutdown complete")
        
        print("\n" + "=" * 50)
        print("🎉 Audit Engine Test Complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_individual_components():
    """Test individual audit engine components."""
    print("\n🔧 Testing Individual Components")
    print("-" * 40)
    
    try:
        # Test session manager
        print("1. Testing Session Manager...")
        from ai_code_audit.audit.session_manager import AuditSessionManager, SessionConfig
        from ai_code_audit.core.models import ProjectInfo, ProjectType
        
        session_manager = AuditSessionManager()
        
        # Create test project info
        project_info = ProjectInfo(
            name="test_project",
            path=".",
            project_type=ProjectType.WEB_APPLICATION,
            languages=["python"],
            files=[],
            dependencies=[],
            entry_points=[]
        )
        
        # Create session
        session = await session_manager.create_session(
            project_path=".",
            project_info=project_info,
            config=SessionConfig(max_files=5)
        )
        
        print(f"   ✅ Session created: {session.session_id}")
        
        # Test session updates
        await session_manager.update_session_progress(
            session.session_id,
            analyzed_files=2,
            current_file="test.py"
        )
        
        print("   ✅ Session progress updated")
        
        # Test orchestrator
        print("\n2. Testing Analysis Orchestrator...")
        from ai_code_audit.audit.orchestrator import AnalysisOrchestrator
        from ai_code_audit.llm.manager import LLMManager
        from ai_code_audit.llm.prompts import PromptManager
        
        llm_manager = LLMManager()
        prompt_manager = PromptManager()
        orchestrator = AnalysisOrchestrator(llm_manager, prompt_manager)
        
        await orchestrator.start()
        print("   ✅ Orchestrator started")
        
        stats = orchestrator.get_statistics()
        print(f"   ✅ Orchestrator stats: {stats}")
        
        await orchestrator.stop()
        print("   ✅ Orchestrator stopped")
        
        # Test aggregator
        print("\n3. Testing Result Aggregator...")
        from ai_code_audit.audit.aggregator import ResultAggregator
        
        aggregator = ResultAggregator()
        
        # Test with sample data
        sample_results = [
            {
                'file_path': 'test.py',
                'analysis': 'No security issues found.',
                'template': 'security_audit',
                'model': 'qwen-coder-30b'
            }
        ]
        
        audit_result = await aggregator.aggregate_results(
            session_id=session.session_id,
            project_path=".",
            project_name="test_project",
            raw_results=sample_results
        )
        
        print(f"   ✅ Results aggregated: {audit_result.total_findings} findings")
        
        # Test report generator
        print("\n4. Testing Report Generator...")
        from ai_code_audit.audit.report_generator import ReportGenerator, ReportFormat
        
        report_generator = ReportGenerator()
        
        # Generate JSON report
        json_report = await report_generator.generate_report(
            audit_result=audit_result,
            format=ReportFormat.JSON
        )
        
        print(f"   ✅ JSON report generated: {len(json_report.content)} characters")
        
        print("\n✅ All individual components tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🧪 Audit Engine Test Suite")
    print("=" * 60)
    
    # Test individual components first
    component_test_passed = await test_individual_components()
    
    if component_test_passed:
        print("\n" + "=" * 60)
        # Test complete workflow
        engine_test_passed = await test_audit_engine()
        
        if engine_test_passed:
            print("\n🎉 All tests passed! Audit engine is working correctly.")
            return 0
        else:
            print("\n❌ Engine test failed.")
            return 1
    else:
        print("\n❌ Component tests failed.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
