"""
Unit tests for analysis components.

This module tests:
- Semantic analyzer functionality
- Taint analysis system
- Code slicing algorithms
- Path validation
- Call graph construction
"""

import pytest
import pytest_asyncio
import tempfile
import ast
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_code_audit.analysis.semantic_analyzer import SemanticAnalyzer, Variable, DataFlow, VariableType, DataFlowType
from ai_code_audit.analysis.taint_analyzer import TaintAnalyzer, TaintSource, TaintSink, TaintType
from ai_code_audit.analysis.code_slicer import CodeSlicer, SlicePoint, SliceCriterion, CodeSlice
from ai_code_audit.analysis.call_graph import CallGraphBuilder, FunctionNode, CallGraphResult
from ai_code_audit.analysis.path_validator import PathValidator, VulnerabilityPath, ValidationResult
from ai_code_audit.core.models import ProjectInfo, FileInfo


class TestSemanticAnalyzer:
    """Test semantic analyzer functionality."""
    
    @pytest.fixture
    def sample_code(self):
        """Fixture providing sample Python code."""
        return '''
import os
import subprocess

def vulnerable_function(user_input):
    # Variable assignment
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Function call with tainted data
    result = execute_query(query)
    
    # Command execution
    subprocess.call(f"echo {user_input}", shell=True)
    
    return result

def execute_query(sql):
    return "mock_result"

class UserManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
'''
    
    @pytest.fixture
    def temp_file(self, sample_code):
        """Fixture providing temporary file with sample code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_code)
            f.flush()
            yield f.name
        Path(f.name).unlink()
    
    @pytest.fixture
    def project_info(self, temp_file):
        """Fixture providing project info."""
        return ProjectInfo(
            name="test_project",
            path=str(Path(temp_file).parent),
            language="python",
            files=[FileInfo(
                path=Path(temp_file).name,
                absolute_path=temp_file,
                size=1000,
                language="python"
            )]
        )
    
    def test_semantic_analyzer_initialization(self, project_info):
        """Test semantic analyzer initialization."""
        analyzer = SemanticAnalyzer(project_info)
        
        assert analyzer.project_info == project_info
        assert len(analyzer.file_asts) == 1  # Should load the test file
        assert len(analyzer.analysis_results) == 0
    
    def test_analyze_file(self, project_info, temp_file):
        """Test analyzing a single file."""
        analyzer = SemanticAnalyzer(project_info)
        
        result = analyzer.analyze_file(temp_file)
        
        assert result is not None
        assert len(result.variables) > 0
        assert len(result.function_definitions) > 0
        assert len(result.class_definitions) > 0
        
        # Check for specific variables
        variable_names = [var.name for var in result.variables.values()]
        assert "user_input" in variable_names
        assert "query" in variable_names
        assert "result" in variable_names
    
    def test_variable_detection(self, project_info, temp_file):
        """Test variable detection and classification."""
        analyzer = SemanticAnalyzer(project_info)
        result = analyzer.analyze_file(temp_file)
        
        # Find specific variables
        user_input_vars = [var for var in result.variables.values() if var.name == "user_input"]
        query_vars = [var for var in result.variables.values() if var.name == "query"]
        
        assert len(user_input_vars) > 0
        assert len(query_vars) > 0
        
        # Check variable types
        user_input_var = user_input_vars[0]
        assert user_input_var.var_type == VariableType.PARAMETER
        
        query_var = query_vars[0]
        assert query_var.var_type == VariableType.LOCAL
    
    def test_data_flow_analysis(self, project_info, temp_file):
        """Test data flow analysis."""
        analyzer = SemanticAnalyzer(project_info)
        result = analyzer.analyze_file(temp_file)
        
        assert len(result.data_flows) > 0
        
        # Check for specific data flows
        flow_descriptions = [(flow.source.name, flow.target.name, flow.flow_type) 
                           for flow in result.data_flows]
        
        # Should have parameter passing flows
        param_flows = [flow for flow in flow_descriptions if flow[2] == FlowType.PARAMETER_PASSING]
        assert len(param_flows) > 0
        
        # Should have assignment flows
        assignment_flows = [flow for flow in flow_descriptions if flow[2] == FlowType.ASSIGNMENT]
        assert len(assignment_flows) > 0
    
    def test_function_detection(self, project_info, temp_file):
        """Test function detection."""
        analyzer = SemanticAnalyzer(project_info)
        result = analyzer.analyze_file(temp_file)
        
        function_names = [func.name for func in result.function_definitions.values()]
        
        assert "vulnerable_function" in function_names
        assert "execute_query" in function_names
    
    def test_class_detection(self, project_info, temp_file):
        """Test class detection."""
        analyzer = SemanticAnalyzer(project_info)
        result = analyzer.analyze_file(temp_file)
        
        class_names = [cls.name for cls in result.class_definitions.values()]
        
        assert "UserManager" in class_names
    
    def test_analyze_all_files(self, project_info):
        """Test analyzing all files in project."""
        analyzer = SemanticAnalyzer(project_info)
        
        results = analyzer.analyze_all_files()
        
        assert len(results) == len(project_info.files)
        assert all(file_info.path in results for file_info in project_info.files)


class TestTaintAnalyzer:
    """Test taint analyzer functionality."""
    
    @pytest.fixture
    def semantic_analyzer(self, project_info, temp_file):
        """Fixture providing semantic analyzer with analyzed file."""
        analyzer = SemanticAnalyzer(project_info)
        analyzer.analyze_file(temp_file)
        return analyzer
    
    @pytest.fixture
    def call_graph_builder(self, project_info):
        """Fixture providing call graph builder."""
        return CallGraphBuilder(project_info)
    
    def test_taint_analyzer_initialization(self, semantic_analyzer, call_graph_builder):
        """Test taint analyzer initialization."""
        analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        
        assert analyzer.semantic_analyzer == semantic_analyzer
        assert analyzer.call_graph_builder == call_graph_builder
        assert len(analyzer.analysis_results) == 0
    
    def test_identify_taint_sources(self, semantic_analyzer, call_graph_builder, temp_file):
        """Test identification of taint sources."""
        analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        
        result = analyzer.analyze_file(temp_file)
        
        assert len(result.taint_sources) > 0
        
        # Should identify user_input as a taint source
        source_names = [source.name for source in result.taint_sources]
        assert any("user_input" in name for name in source_names)
    
    def test_identify_taint_sinks(self, semantic_analyzer, call_graph_builder, temp_file):
        """Test identification of taint sinks."""
        analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        
        result = analyzer.analyze_file(temp_file)
        
        assert len(result.taint_sinks) > 0
        
        # Should identify dangerous function calls as sinks
        sink_functions = [sink.function_name for sink in result.taint_sinks]
        assert any("subprocess" in func for func in sink_functions)
    
    def test_taint_flow_detection(self, semantic_analyzer, call_graph_builder, temp_file):
        """Test taint flow detection."""
        analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        
        result = analyzer.analyze_file(temp_file)
        
        # Should detect taint flows from sources to sinks
        assert len(result.taint_flows) > 0
        
        # Check for specific vulnerability types
        vulnerability_types = [flow.vulnerability_type for flow in result.taint_flows]
        assert TaintType.COMMAND_INJECTION in vulnerability_types or TaintType.SQL_INJECTION in vulnerability_types
    
    def test_vulnerability_detection(self, semantic_analyzer, call_graph_builder, temp_file):
        """Test vulnerability detection."""
        analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        
        result = analyzer.analyze_file(temp_file)
        
        assert len(result.vulnerabilities) > 0
        
        # Check vulnerability details
        vuln_types = [vuln["type"] for vuln in result.vulnerabilities]
        assert any("injection" in vtype.lower() for vtype in vuln_types)


class TestCodeSlicer:
    """Test code slicing functionality."""
    
    @pytest.fixture
    def code_slicer(self, semantic_analyzer, call_graph_builder):
        """Fixture providing code slicer."""
        return CodeSlicer(semantic_analyzer, call_graph_builder)
    
    def test_code_slicer_initialization(self, semantic_analyzer, call_graph_builder):
        """Test code slicer initialization."""
        slicer = CodeSlicer(semantic_analyzer, call_graph_builder)
        
        assert slicer.semantic_analyzer == semantic_analyzer
        assert slicer.call_graph_builder == call_graph_builder
    
    def test_backward_slicing(self, code_slicer, temp_file):
        """Test backward slicing."""
        slice_point = SlicePoint(
            file_path=temp_file,
            line_number=10,
            variable_name="query",
            criterion=SliceCriterion.VARIABLE_USE
        )
        
        slice_result = code_slicer.slice_backward(slice_point)
        
        assert isinstance(slice_result, CodeSlice)
        assert slice_result.line_count > 0
        assert slice_result.file_count >= 1
    
    def test_forward_slicing(self, code_slicer, temp_file):
        """Test forward slicing."""
        slice_point = SlicePoint(
            file_path=temp_file,
            line_number=5,
            variable_name="user_input",
            criterion=SliceCriterion.VARIABLE_DEF
        )
        
        slice_result = code_slicer.slice_forward(slice_point)
        
        assert isinstance(slice_result, CodeSlice)
        assert slice_result.line_count > 0
    
    def test_security_focused_slicing(self, code_slicer, temp_file):
        """Test security-focused slicing."""
        slice_point = SlicePoint(
            file_path=temp_file,
            line_number=8,
            criterion=SliceCriterion.SECURITY_SINK
        )
        
        slice_result = code_slicer.slice_security_focused(slice_point)
        
        assert isinstance(slice_result, CodeSlice)
        assert slice_result.security_score >= 0.0
    
    def test_minimal_sufficient_set_extraction(self, code_slicer, temp_file):
        """Test minimal sufficient set extraction."""
        slice_point = SlicePoint(
            file_path=temp_file,
            line_number=10,
            criterion=SliceCriterion.VULNERABILITY
        )
        
        minimal_set = code_slicer.extract_minimal_sufficient_set(slice_point)
        
        assert isinstance(minimal_set, CodeSlice)
        assert minimal_set.completeness_score >= 0.0
        assert len(minimal_set.entry_points) >= 0
        assert len(minimal_set.exit_points) >= 0


class TestCallGraphBuilder:
    """Test call graph construction."""
    
    def test_call_graph_builder_initialization(self, project_info):
        """Test call graph builder initialization."""
        builder = CallGraphBuilder(project_info)
        
        assert builder.project_info == project_info
        assert len(builder.file_asts) == 0
    
    def test_build_call_graph(self, project_info, temp_file):
        """Test building call graph."""
        builder = CallGraphBuilder(project_info)
        
        call_graph = builder.build_call_graph()
        
        assert isinstance(call_graph, CallGraph)
        assert len(call_graph.functions) > 0
        assert len(call_graph.call_edges) >= 0
    
    def test_function_node_creation(self, project_info, temp_file):
        """Test function node creation."""
        builder = CallGraphBuilder(project_info)
        call_graph = builder.build_call_graph()
        
        # Check for specific functions
        function_names = [func.name for func in call_graph.functions.values()]
        assert "vulnerable_function" in function_names
        assert "execute_query" in function_names
    
    def test_call_edge_detection(self, project_info, temp_file):
        """Test call edge detection."""
        builder = CallGraphBuilder(project_info)
        call_graph = builder.build_call_graph()
        
        # Should detect function calls
        if call_graph.call_edges:
            edge = call_graph.call_edges[0]
            assert hasattr(edge, 'caller')
            assert hasattr(edge, 'callee')
    
    def test_get_call_chain(self, project_info, temp_file):
        """Test call chain analysis."""
        builder = CallGraphBuilder(project_info)
        call_graph = builder.build_call_graph()
        
        if len(call_graph.functions) >= 2:
            func_names = list(call_graph.functions.keys())
            chains = builder.get_call_chain(func_names[0], func_names[1])
            
            assert isinstance(chains, list)


class TestPathValidator:
    """Test path validation functionality."""
    
    @pytest.fixture
    def path_validator(self, semantic_analyzer, call_graph_builder):
        """Fixture providing path validator."""
        taint_analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        code_slicer = CodeSlicer(semantic_analyzer, call_graph_builder)
        
        return PathValidator(semantic_analyzer, call_graph_builder, taint_analyzer, code_slicer)
    
    def test_path_validator_initialization(self, path_validator):
        """Test path validator initialization."""
        assert path_validator.semantic_analyzer is not None
        assert path_validator.call_graph_builder is not None
        assert path_validator.taint_analyzer is not None
        assert path_validator.code_slicer is not None
    
    def test_validate_vulnerability_paths(self, path_validator, temp_file):
        """Test vulnerability path validation."""
        result = path_validator.validate_vulnerability_paths(temp_file)
        
        assert result is not None
        assert result.file_path == temp_file
        assert result.total_paths_analyzed >= 0
        assert result.validation_coverage >= 0.0
        assert result.analysis_confidence >= 0.0
    
    def test_get_validation_summary(self, path_validator):
        """Test getting validation summary."""
        summary = path_validator.get_validation_summary()
        
        assert "total_vulnerabilities" in summary
        assert isinstance(summary["total_vulnerabilities"], int)


class TestAnalysisIntegration:
    """Test integration between analysis components."""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_pipeline(self, project_info, temp_file):
        """Test complete analysis pipeline integration."""
        # Initialize all components
        semantic_analyzer = SemanticAnalyzer(project_info)
        call_graph_builder = CallGraphBuilder(project_info)
        taint_analyzer = TaintAnalyzer(semantic_analyzer, call_graph_builder)
        code_slicer = CodeSlicer(semantic_analyzer, call_graph_builder)
        path_validator = PathValidator(semantic_analyzer, call_graph_builder, taint_analyzer, code_slicer)
        
        # Run complete analysis
        semantic_result = semantic_analyzer.analyze_file(temp_file)
        call_graph = call_graph_builder.build_call_graph()
        taint_result = taint_analyzer.analyze_file(temp_file)
        validation_result = path_validator.validate_vulnerability_paths(temp_file)
        
        # Verify integration
        assert semantic_result is not None
        assert call_graph is not None
        assert taint_result is not None
        assert validation_result is not None
        
        # Check data consistency
        assert len(semantic_result.variables) > 0
        assert len(call_graph.functions) > 0
        assert taint_result.file_path == temp_file
        assert validation_result.file_path == temp_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
