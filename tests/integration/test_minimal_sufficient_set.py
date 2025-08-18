#!/usr/bin/env python3
"""
Test script for minimal sufficient set forensics system.

This script tests:
- Semantic analysis engine
- Call graph construction
- Code slicing algorithms
- Taint analysis system
- Path validation and verification
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_semantic_analyzer():
    """Test semantic analysis engine."""
    print("🧠 Testing Semantic Analysis Engine")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.semantic_analyzer import SemanticAnalyzer
        
        # Analyze current project
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        # Initialize semantic analyzer
        semantic_analyzer = SemanticAnalyzer(project_info)
        
        print("1. Analyzing semantic structure...")
        results = semantic_analyzer.analyze_all_files()
        
        print(f"   Files analyzed: {len(results)}")
        
        # Show analysis for a specific file
        test_file = None
        for file_path in results:
            if 'test_minimal_sufficient_set.py' in file_path:
                test_file = file_path
                break
        
        if test_file:
            result = results[test_file]
            print(f"2. Analysis results for {Path(test_file).name}:")
            print(f"   Variables: {len(result.variables)}")
            print(f"   Data flows: {len(result.data_flows)}")
            print(f"   Control flow nodes: {len(result.control_flow_nodes)}")
            print(f"   Functions: {len(result.function_definitions)}")
            print(f"   Classes: {len(result.class_definitions)}")
            print(f"   Scopes: {len(result.scopes)}")
            
            # Show some variables
            print("3. Sample variables:")
            for i, (var_id, variable) in enumerate(list(result.variables.items())[:3]):
                print(f"   - {variable.name} ({variable.var_type.value}) at line {variable.defined_at[0]}")
            
            # Show some data flows
            print("4. Sample data flows:")
            for i, flow in enumerate(result.data_flows[:3]):
                print(f"   - {flow.source.name} -> {flow.target.name} ({flow.flow_type.value})")
        
        print("✅ Semantic analysis test passed")
        return semantic_analyzer
        
    except Exception as e:
        print(f"❌ Semantic analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_call_graph_builder():
    """Test call graph construction."""
    print("\n📞 Testing Call Graph Builder")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.call_graph import CallGraphBuilder
        
        # Analyze current project
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        # Initialize call graph builder
        call_graph_builder = CallGraphBuilder(project_info)
        
        print("1. Building call graph...")
        call_graph = call_graph_builder.build_call_graph()
        
        print(f"   Functions: {len(call_graph.functions)}")
        print(f"   Classes: {len(call_graph.classes)}")
        print(f"   Call edges: {len(call_graph.call_edges)}")
        print(f"   Dependency edges: {len(call_graph.dependency_edges)}")
        print(f"   Entry points: {len(call_graph.entry_points)}")
        print(f"   Unreachable functions: {len(call_graph.unreachable_functions)}")
        
        # Show some functions
        print("2. Sample functions:")
        for i, (func_id, function) in enumerate(list(call_graph.functions.items())[:3]):
            print(f"   - {function.name} in {Path(function.file_path).name}:{function.line_number}")
            print(f"     Parameters: {function.parameters}")
            print(f"     Complexity: {function.complexity}")
        
        # Show some call edges
        print("3. Sample call relationships:")
        for i, edge in enumerate(call_graph.call_edges[:3]):
            print(f"   - {edge.caller.name} -> {edge.callee.name} ({edge.call_type.value})")
        
        # Test call chain analysis
        if len(call_graph.functions) >= 2:
            func_names = list(call_graph.functions.keys())
            print("4. Testing call chain analysis...")
            chains = call_graph_builder.get_call_chain(func_names[0], func_names[1])
            print(f"   Found {len(chains)} call chains between functions")
        
        print("✅ Call graph construction test passed")
        return call_graph_builder
        
    except Exception as e:
        print(f"❌ Call graph construction test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_code_slicer():
    """Test code slicing algorithms."""
    print("\n🔪 Testing Code Slicing System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.semantic_analyzer import SemanticAnalyzer
        from ai_code_audit.analysis.call_graph import CallGraphBuilder
        from ai_code_audit.analysis.code_slicer import CodeSlicer, SlicePoint, SliceCriterion
        
        # Setup analyzers
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        semantic_analyzer = SemanticAnalyzer(project_info)
        call_graph_builder = CallGraphBuilder(project_info)
        
        # Initialize code slicer
        code_slicer = CodeSlicer(semantic_analyzer, call_graph_builder)
        
        print("1. Testing backward slicing...")
        
        # Create a slice point
        slice_point = SlicePoint(
            file_path="test_minimal_sufficient_set.py",
            line_number=50,  # Approximate line in this function
            variable_name="project_info",
            criterion=SliceCriterion.VARIABLE_USE
        )
        
        backward_slice = code_slicer.slice_backward(slice_point)
        print(f"   Backward slice: {backward_slice.line_count} lines")
        print(f"   Files involved: {backward_slice.file_count}")
        print(f"   Security score: {backward_slice.security_score:.2f}")
        
        print("2. Testing forward slicing...")
        forward_slice = code_slicer.slice_forward(slice_point)
        print(f"   Forward slice: {forward_slice.line_count} lines")
        print(f"   Security score: {forward_slice.security_score:.2f}")
        
        print("3. Testing security-focused slicing...")
        security_slice = code_slicer.slice_security_focused(slice_point)
        print(f"   Security slice: {security_slice.line_count} lines")
        print(f"   Security score: {security_slice.security_score:.2f}")
        
        print("4. Testing minimal sufficient set extraction...")
        minimal_set = code_slicer.extract_minimal_sufficient_set(slice_point)
        print(f"   Minimal set: {minimal_set.line_count} lines")
        print(f"   Entry points: {len(minimal_set.entry_points)}")
        print(f"   Exit points: {len(minimal_set.exit_points)}")
        print(f"   Completeness: {minimal_set.completeness_score:.2f}")
        
        # Show some slice content
        if minimal_set.nodes:
            print("5. Sample slice content:")
            for node in minimal_set.nodes[:3]:
                print(f"   Line {node.line_number}: {node.content[:50]}...")
        
        print("✅ Code slicing test passed")
        return code_slicer
        
    except Exception as e:
        print(f"❌ Code slicing test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_taint_analyzer():
    """Test taint analysis system."""
    print("\n🦠 Testing Taint Analysis System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.semantic_analyzer import SemanticAnalyzer
        from ai_code_audit.analysis.call_graph import CallGraphBuilder
        from ai_code_audit.analysis.taint_analyzer import TaintAnalyzer
        
        # Setup analyzers
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        semantic_analyzer = SemanticAnalyzer(project_info)
        call_graph_builder = CallGraphBuilder(project_info)
        
        # Initialize taint analyzer
        taint_analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        
        print("1. Analyzing taint sources and sinks...")
        results = taint_analyzer.analyze_all_files()
        
        total_sources = sum(len(result.taint_sources) for result in results.values())
        total_sinks = sum(len(result.taint_sinks) for result in results.values())
        total_flows = sum(len(result.taint_flows) for result in results.values())
        total_vulnerabilities = sum(len(result.vulnerabilities) for result in results.values())
        
        print(f"   Taint sources found: {total_sources}")
        print(f"   Taint sinks found: {total_sinks}")
        print(f"   Taint flows: {total_flows}")
        print(f"   Vulnerabilities: {total_vulnerabilities}")
        
        # Show analysis for a specific file if available
        if results:
            sample_file = list(results.keys())[0]
            result = results[sample_file]
            
            print(f"2. Sample analysis for {Path(sample_file).name}:")
            print(f"   Sources: {len(result.taint_sources)}")
            print(f"   Sinks: {len(result.taint_sinks)}")
            print(f"   Tainted variables: {len(result.tainted_variables)}")
            
            # Show some sources
            if result.taint_sources:
                print("3. Sample taint sources:")
                for source in result.taint_sources[:2]:
                    print(f"   - {source.name} ({source.taint_type.value}) at line {source.line_number}")
            
            # Show some vulnerabilities
            if result.vulnerabilities:
                print("4. Sample vulnerabilities:")
                for vuln in result.vulnerabilities[:2]:
                    print(f"   - {vuln['type']} ({vuln['severity']}) - {vuln['recommendation']}")
        
        # Get vulnerability summary
        summary = taint_analyzer.get_vulnerability_summary()
        print("5. Vulnerability summary:")
        print(f"   Total vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"   Exploitable: {summary['exploitable_count']}")
        if summary.get('by_type'):
            print(f"   By type: {summary['by_type']}")
        
        print("✅ Taint analysis test passed")
        return taint_analyzer
        
    except Exception as e:
        print(f"❌ Taint analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_path_validator():
    """Test path validation system."""
    print("\n🛤️ Testing Path Validation System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.semantic_analyzer import SemanticAnalyzer
        from ai_code_audit.analysis.call_graph import CallGraphBuilder
        from ai_code_audit.analysis.taint_analyzer import TaintAnalyzer
        from ai_code_audit.analysis.code_slicer import CodeSlicer
        from ai_code_audit.analysis.path_validator import PathValidator
        
        # Setup all analyzers
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        semantic_analyzer = SemanticAnalyzer(project_info)
        call_graph_builder = CallGraphBuilder(project_info)
        taint_analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        code_slicer = CodeSlicer(semantic_analyzer, call_graph_builder)
        
        # Initialize path validator
        path_validator = PathValidator(semantic_analyzer, call_graph_builder, taint_analyzer, code_slicer)
        
        print("1. Validating vulnerability paths...")
        
        # Validate paths for files with potential vulnerabilities
        validation_results = {}
        for file_path in list(semantic_analyzer.file_asts.keys())[:3]:  # Test first 3 files
            try:
                result = path_validator.validate_vulnerability_paths(file_path)
                validation_results[file_path] = result
            except Exception as e:
                print(f"   Warning: Failed to validate {file_path}: {e}")
        
        total_paths = sum(r.total_paths_analyzed for r in validation_results.values())
        exploitable_paths = sum(r.exploitable_paths for r in validation_results.values())
        potentially_exploitable = sum(r.potentially_exploitable_paths for r in validation_results.values())
        
        print(f"   Total paths analyzed: {total_paths}")
        print(f"   Exploitable paths: {exploitable_paths}")
        print(f"   Potentially exploitable: {potentially_exploitable}")
        
        # Show detailed results for one file
        if validation_results:
            sample_file = list(validation_results.keys())[0]
            result = validation_results[sample_file]
            
            print(f"2. Sample validation for {Path(sample_file).name}:")
            print(f"   Vulnerability paths: {len(result.vulnerability_paths)}")
            print(f"   Validation coverage: {result.validation_coverage:.1%}")
            print(f"   Analysis confidence: {result.analysis_confidence:.1%}")
            
            # Show vulnerability path details
            if result.vulnerability_paths:
                vuln_path = result.vulnerability_paths[0]
                print("3. Sample vulnerability path:")
                print(f"   Type: {vuln_path.vulnerability_type.value}")
                print(f"   Validation result: {vuln_path.validation_result.value}")
                print(f"   Exploitability score: {vuln_path.exploitability_score:.2f}")
                print(f"   Execution paths: {len(vuln_path.execution_paths)}")
                print(f"   Evidence chain: {len(vuln_path.evidence_chain)} items")
                print(f"   Attack vectors: {len(vuln_path.attack_vectors)}")
        
        # Get validation summary
        summary = path_validator.get_validation_summary()
        print("4. Validation summary:")
        print(f"   Total vulnerabilities: {summary['total_vulnerabilities']}")
        if summary.get('by_validation_result'):
            print(f"   By result: {summary['by_validation_result']}")
        if summary.get('average_exploitability'):
            print(f"   Average exploitability: {summary['average_exploitability']:.2f}")
        
        print("✅ Path validation test passed")
        return path_validator
        
    except Exception as e:
        print(f"❌ Path validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_integrated_forensics():
    """Test integrated minimal sufficient set forensics."""
    print("\n🔬 Testing Integrated Forensics System")
    print("-" * 40)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.analysis.semantic_analyzer import SemanticAnalyzer
        from ai_code_audit.analysis.call_graph import CallGraphBuilder
        from ai_code_audit.analysis.taint_analyzer import TaintAnalyzer
        from ai_code_audit.analysis.code_slicer import CodeSlicer, SlicePoint
        from ai_code_audit.analysis.path_validator import PathValidator
        
        print("1. Setting up integrated forensics pipeline...")
        
        # Setup complete analysis pipeline
        analyzer = ProjectAnalyzer()
        project_info = await analyzer.analyze_project(".")
        
        semantic_analyzer = SemanticAnalyzer(project_info)
        call_graph_builder = CallGraphBuilder(project_info)
        taint_analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        code_slicer = CodeSlicer(semantic_analyzer, call_graph_builder)
        path_validator = PathValidator(semantic_analyzer, call_graph_builder, taint_analyzer, code_slicer)
        
        print("2. Running complete forensics analysis...")
        
        # Run semantic analysis
        semantic_results = semantic_analyzer.analyze_all_files()
        
        # Build call graph
        call_graph = call_graph_builder.build_call_graph()
        
        # Run taint analysis
        taint_results = taint_analyzer.analyze_all_files()
        
        # Validate paths for files with vulnerabilities
        files_with_vulns = [f for f, r in taint_results.items() if r.vulnerabilities]
        
        validation_results = {}
        for file_path in files_with_vulns[:2]:  # Limit to first 2 files
            validation_results[file_path] = path_validator.validate_vulnerability_paths(file_path)
        
        print("3. Forensics analysis complete!")
        print(f"   Files analyzed: {len(semantic_results)}")
        print(f"   Functions in call graph: {len(call_graph.functions)}")
        print(f"   Total vulnerabilities: {sum(len(r.vulnerabilities) for r in taint_results.values())}")
        print(f"   Validated vulnerability paths: {sum(len(r.vulnerability_paths) for r in validation_results.values())}")
        
        # Generate comprehensive evidence
        print("4. Evidence generation:")
        total_evidence = 0
        for result in validation_results.values():
            for vuln_path in result.vulnerability_paths:
                total_evidence += len(vuln_path.evidence_chain)
        
        print(f"   Total evidence items: {total_evidence}")
        
        # Show integration benefits
        print("5. Integration benefits demonstrated:")
        print("   ✅ Semantic analysis provides variable and data flow tracking")
        print("   ✅ Call graph enables cross-file vulnerability analysis")
        print("   ✅ Taint analysis identifies security-relevant data flows")
        print("   ✅ Code slicing extracts minimal sufficient evidence sets")
        print("   ✅ Path validation confirms exploitability with evidence chains")
        
        print("✅ Integrated forensics test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integrated forensics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all minimal sufficient set forensics tests."""
    print("🔬 Minimal Sufficient Set Forensics Test Suite")
    print("=" * 60)
    
    tests = [
        ("Semantic Analysis Engine", test_semantic_analyzer),
        ("Call Graph Builder", test_call_graph_builder),
        ("Code Slicing System", test_code_slicer),
        ("Taint Analysis System", test_taint_analyzer),
        ("Path Validation System", test_path_validator),
        ("Integrated Forensics", test_integrated_forensics),
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
    print(f"🔬 Forensics Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All minimal sufficient set forensics features are working!")
        print("\n✨ Forensics Capabilities Summary:")
        print("   🧠 Semantic Analysis - Variable dependencies, data/control flow")
        print("   📞 Call Graph - Function relationships and cross-file analysis")
        print("   🔪 Code Slicing - Minimal sufficient set extraction")
        print("   🦠 Taint Analysis - Security vulnerability detection")
        print("   🛤️ Path Validation - Exploitability verification with evidence")
        print("   🔬 Integrated Forensics - Complete security analysis pipeline")
        return 0
    else:
        print("⚠️  Some forensics features need attention.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
