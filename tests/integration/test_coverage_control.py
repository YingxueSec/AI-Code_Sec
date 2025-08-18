#!/usr/bin/env python3
"""
Test script for coverage control mechanisms.

This script tests:
- Coverage tracking system
- Task matrix management
- Coverage reporting
- Integration with audit engine
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_coverage_tracker():
    """Test coverage tracking system."""
    print("📊 Testing Coverage Tracking System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.coverage_tracker import CoverageTracker, Priority
        
        # Analyze current project
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        # Initialize coverage tracker
        tracker = CoverageTracker(project_info)
        
        print(f"1. Discovered code units:")
        print(f"   Total units: {len(tracker.code_units)}")
        print(f"   Files tracked: {len(tracker.file_units)}")
        
        # Show priority distribution
        priority_counts = {}
        for unit in tracker.code_units.values():
            priority_counts[unit.priority.name] = priority_counts.get(unit.priority.name, 0) + 1
        
        print(f"2. Priority distribution:")
        for priority, count in priority_counts.items():
            print(f"   {priority}: {count} units")
        
        # Test getting next units for analysis
        print(f"3. Getting next units for analysis:")
        next_units = tracker.get_next_units(count=5)
        for unit in next_units:
            print(f"   - {unit.name} ({unit.unit_type.value}) - Priority: {unit.priority.name}")
            print(f"     File: {unit.file_path}:{unit.start_line}-{unit.end_line}")
        
        # Simulate some analysis completion
        print(f"4. Simulating analysis completion...")
        for i, unit in enumerate(next_units[:3]):
            tracker.mark_unit_analyzed(unit.id, analysis_duration=30.0 + i * 10)
            print(f"   Marked {unit.name} as analyzed")
        
        # Get coverage statistics
        stats = tracker.get_coverage_stats()
        print(f"5. Coverage statistics:")
        print(f"   Total: {stats.total_units}")
        print(f"   Analyzed: {stats.analyzed_units}")
        print(f"   Coverage: {stats.coverage_percentage:.1f}%")
        print(f"   Success rate: {stats.success_rate:.1f}%")
        
        print("✅ Coverage tracking test passed")
        return tracker
        
    except Exception as e:
        print(f"❌ Coverage tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_task_matrix():
    """Test task matrix management."""
    print("\n🎯 Testing Task Matrix Management")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.task_matrix import TaskMatrix, AnalysisTask, TaskType
        from ai_code_audit.analysis.coverage_tracker import CodeUnit, CoverageLevel, Priority
        
        # Initialize task matrix
        matrix = TaskMatrix()
        
        # Create some test tasks
        print("1. Creating test tasks...")
        test_units = [
            CodeUnit(
                id="test_auth_func",
                name="authenticate_user",
                file_path="auth.py",
                start_line=10,
                end_line=25,
                unit_type=CoverageLevel.FUNCTION,
                priority=Priority.CRITICAL
            ),
            CodeUnit(
                id="test_util_func",
                name="format_string",
                file_path="utils.py",
                start_line=5,
                end_line=10,
                unit_type=CoverageLevel.FUNCTION,
                priority=Priority.LOW
            ),
            CodeUnit(
                id="test_api_func",
                name="handle_request",
                file_path="api.py",
                start_line=20,
                end_line=50,
                unit_type=CoverageLevel.FUNCTION,
                priority=Priority.HIGH
            )
        ]
        
        tasks = []
        for i, unit in enumerate(test_units):
            task = AnalysisTask(
                id=f"task_{i}",
                code_unit=unit,
                task_type=TaskType.FUNCTION_ANALYSIS,
                priority=unit.priority
            )
            tasks.append(task)
            matrix.add_task(task)
        
        print(f"   Added {len(tasks)} tasks to matrix")
        
        # Test task prioritization
        print("2. Testing task prioritization...")
        for i in range(3):
            next_task = matrix.get_next_task()
            if next_task:
                print(f"   Next task: {next_task.code_unit.name} (Priority: {next_task.priority.name}, Score: {next_task.priority_score:.3f})")
                
                # Simulate task completion
                matrix.complete_task(next_task.id, success=True, duration=45.0)
            else:
                print("   No more tasks available")
                break
        
        # Get queue statistics
        stats = matrix.get_queue_stats()
        print("3. Queue statistics:")
        for key, value in stats.items():
            if key != 'last_rebalance':
                print(f"   {key}: {value}")
        
        # Test priority distribution
        distribution = matrix.get_priority_distribution()
        print("4. Priority distribution:")
        for priority, count in distribution.items():
            print(f"   {priority}: {count} tasks")
        
        print("✅ Task matrix test passed")
        return matrix
        
    except Exception as e:
        print(f"❌ Task matrix test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_coverage_reporter():
    """Test coverage reporting system."""
    print("\n📋 Testing Coverage Reporting System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.coverage_tracker import CoverageTracker
        from ai_code_audit.analysis.coverage_reporter import CoverageReporter
        
        # Setup coverage tracker with some analyzed units
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        tracker = CoverageTracker(project_info)
        
        # Simulate some analysis
        units = tracker.get_next_units(count=5)
        for i, unit in enumerate(units[:3]):
            tracker.mark_unit_analyzed(unit.id, analysis_duration=30.0 + i * 10)
        
        # Mark one as failed
        if len(units) > 3:
            tracker.mark_unit_failed(units[3].id, "Syntax error")
        
        # Initialize reporter
        reporter = CoverageReporter(tracker)
        
        print("1. Generating coverage reports...")
        
        # Generate HTML report
        html_report = reporter.generate_html_report("test_coverage_report.html")
        print(f"   HTML report generated: {len(html_report)} characters")
        
        # Generate JSON report
        json_data = reporter.generate_json_report("test_coverage_report.json")
        print(f"   JSON report generated with {len(json_data)} keys")
        
        # Generate Markdown report
        md_report = reporter.generate_markdown_report("test_coverage_report.md")
        print(f"   Markdown report generated: {len(md_report)} characters")
        
        print("2. Report contents preview:")
        print(f"   Project: {json_data['project_path']}")
        print(f"   Coverage: {json_data['summary']['coverage_percentage']:.1f}%")
        print(f"   Insights: {len(json_data['insights'])} items")
        print(f"   High priority gaps: {len(json_data['high_priority_gaps'])} items")
        
        print("✅ Coverage reporting test passed")
        return reporter
        
    except Exception as e:
        print(f"❌ Coverage reporting test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_integrated_coverage_control():
    """Test integrated coverage control with audit engine."""
    print("\n🚀 Testing Integrated Coverage Control")
    print("-" * 40)
    
    try:
        from ai_code_audit.audit.engine import AuditEngine
        from ai_code_audit.llm.base import LLMModelType
        
        # Initialize audit engine with coverage control
        print("1. Initializing audit engine with coverage control...")
        audit_engine = AuditEngine(enable_caching=True)
        await audit_engine.initialize()
        
        # Start audit with coverage tracking
        print("2. Starting audit with coverage tracking...")
        session_id = await audit_engine.start_audit(
            project_path=".",
            template="security_audit",
            model=LLMModelType.QWEN_CODER_30B,
            max_files=3,
            use_advanced_context=True,
            use_caching=True
        )
        
        print(f"   Audit session started: {session_id}")
        
        # Monitor coverage during audit
        print("3. Monitoring coverage during audit...")
        for i in range(3):
            await asyncio.sleep(2)
            
            # Get coverage stats
            coverage_stats = audit_engine.get_coverage_stats()
            if coverage_stats:
                print(f"   Coverage: {coverage_stats['coverage_percentage']:.1f}% "
                      f"({coverage_stats['analyzed_units']}/{coverage_stats['total_units']} units)")
            
            # Check audit status
            audit_status = await audit_engine.get_audit_status(session_id)
            if audit_status and audit_status['status'] in ['completed', 'failed']:
                break
        
        # Generate coverage report
        print("4. Generating final coverage report...")
        coverage_report = await audit_engine.generate_coverage_report(
            "test_integrated_coverage.html",
            format="html"
        )
        
        if coverage_report:
            print(f"   Coverage report generated successfully")
        
        # Get final coverage statistics
        final_stats = audit_engine.get_coverage_stats()
        if final_stats:
            print("5. Final coverage statistics:")
            print(f"   Total units: {final_stats['total_units']}")
            print(f"   Analyzed: {final_stats['analyzed_units']}")
            print(f"   Coverage: {final_stats['coverage_percentage']:.1f}%")
            print(f"   Success rate: {final_stats['success_rate']:.1f}%")
        
        # Cleanup
        await audit_engine.shutdown()
        
        print("✅ Integrated coverage control test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integrated coverage control test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all coverage control tests."""
    print("🧪 Coverage Control Test Suite")
    print("=" * 60)
    
    tests = [
        ("Coverage Tracking System", test_coverage_tracker),
        ("Task Matrix Management", test_task_matrix),
        ("Coverage Reporting", test_coverage_reporter),
        ("Integrated Coverage Control", test_integrated_coverage_control),
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
    print(f"📊 Coverage Control Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All coverage control features are working correctly!")
        print("\n✨ Coverage Control Features Summary:")
        print("   📊 Coverage Tracking - Unit-level analysis tracking with priority")
        print("   🎯 Task Matrix - Intelligent task prioritization and scheduling")
        print("   📋 Coverage Reporting - Visual HTML/JSON/Markdown reports")
        print("   🚀 Engine Integration - Seamless integration with audit engine")
        return 0
    else:
        print("⚠️  Some coverage control features need attention.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
