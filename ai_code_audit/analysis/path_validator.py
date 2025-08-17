"""
Path validation system for AI Code Audit System.

This module provides comprehensive path validation including:
- Vulnerability reachability analysis
- Exploitation path verification
- Evidence chain construction
- Attack vector validation
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .semantic_analyzer import SemanticAnalyzer, Variable, DataFlow
from .call_graph import CallGraphBuilder, FunctionNode, CallEdge
from .taint_analyzer import TaintAnalyzer, TaintFlow, TaintType
from .code_slicer import CodeSlicer, SlicePoint, CodeSlice

logger = logging.getLogger(__name__)


class PathType(Enum):
    """Types of execution paths."""
    DIRECT_PATH = "direct_path"
    CONDITIONAL_PATH = "conditional_path"
    LOOP_PATH = "loop_path"
    EXCEPTION_PATH = "exception_path"
    CALLBACK_PATH = "callback_path"


class ValidationResult(Enum):
    """Results of path validation."""
    EXPLOITABLE = "exploitable"
    POTENTIALLY_EXPLOITABLE = "potentially_exploitable"
    NOT_EXPLOITABLE = "not_exploitable"
    INSUFFICIENT_INFO = "insufficient_info"


@dataclass
class PathCondition:
    """Represents a condition that must be met for path execution."""
    condition_type: str  # 'if', 'while', 'for', 'try', 'assert'
    file_path: str
    line_number: int
    condition_expr: str
    is_satisfiable: Optional[bool] = None
    required_values: Dict[str, Any] = field(default_factory=dict)
    complexity_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPath:
    """Represents an execution path through the code."""
    path_id: str
    path_type: PathType
    start_location: Tuple[str, int]  # (file_path, line_number)
    end_location: Tuple[str, int]
    path_nodes: List[Tuple[str, int, str]] = field(default_factory=list)  # (file, line, description)
    conditions: List[PathCondition] = field(default_factory=list)
    function_calls: List[str] = field(default_factory=list)
    variables_involved: Set[str] = field(default_factory=set)
    complexity_score: float = 0.0
    feasibility_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VulnerabilityPath:
    """Represents a complete vulnerability exploitation path."""
    vulnerability_id: str
    vulnerability_type: TaintType
    source_location: Tuple[str, int]
    sink_location: Tuple[str, int]
    execution_paths: List[ExecutionPath] = field(default_factory=list)
    taint_flow: Optional[TaintFlow] = None
    code_slice: Optional[CodeSlice] = None
    validation_result: ValidationResult = ValidationResult.INSUFFICIENT_INFO
    exploitability_score: float = 0.0
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    attack_vectors: List[str] = field(default_factory=list)
    mitigation_suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PathValidationResult:
    """Result of path validation analysis."""
    file_path: str
    vulnerability_paths: List[VulnerabilityPath] = field(default_factory=list)
    total_paths_analyzed: int = 0
    exploitable_paths: int = 0
    potentially_exploitable_paths: int = 0
    validation_coverage: float = 0.0
    analysis_confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PathValidator:
    """Comprehensive path validation and verification system."""
    
    def __init__(self, semantic_analyzer: SemanticAnalyzer, call_graph_builder: CallGraphBuilder,
                 taint_analyzer: TaintAnalyzer, code_slicer: CodeSlicer):
        """Initialize path validator."""
        self.semantic_analyzer = semantic_analyzer
        self.call_graph_builder = call_graph_builder
        self.taint_analyzer = taint_analyzer
        self.code_slicer = code_slicer
        
        # Analysis state
        self.validation_results: Dict[str, PathValidationResult] = {}
        
        # Path analysis configuration
        self.max_path_depth = 20
        self.max_conditions_per_path = 10
        self.complexity_threshold = 0.8
    
    def validate_vulnerability_paths(self, file_path: str) -> PathValidationResult:
        """Validate all vulnerability paths in a file."""
        logger.info(f"Validating vulnerability paths in {file_path}")
        
        result = PathValidationResult(file_path=file_path)
        
        # Get taint analysis results
        if file_path not in self.taint_analyzer.analysis_results:
            self.taint_analyzer.analyze_file(file_path)
        
        taint_result = self.taint_analyzer.analysis_results[file_path]
        
        # Validate each taint flow
        for i, taint_flow in enumerate(taint_result.taint_flows):
            vuln_path = self._validate_taint_flow(taint_flow, f"{file_path}_vuln_{i}")
            result.vulnerability_paths.append(vuln_path)
        
        # Calculate summary statistics
        result.total_paths_analyzed = len(result.vulnerability_paths)
        result.exploitable_paths = len([p for p in result.vulnerability_paths 
                                      if p.validation_result == ValidationResult.EXPLOITABLE])
        result.potentially_exploitable_paths = len([p for p in result.vulnerability_paths 
                                                  if p.validation_result == ValidationResult.POTENTIALLY_EXPLOITABLE])
        
        result.validation_coverage = self._calculate_validation_coverage(result)
        result.analysis_confidence = self._calculate_analysis_confidence(result)
        
        self.validation_results[file_path] = result
        
        logger.info(f"Path validation complete: {result.exploitable_paths} exploitable, "
                   f"{result.potentially_exploitable_paths} potentially exploitable")
        
        return result
    
    def _validate_taint_flow(self, taint_flow: TaintFlow, vuln_id: str) -> VulnerabilityPath:
        """Validate a specific taint flow."""
        vuln_path = VulnerabilityPath(
            vulnerability_id=vuln_id,
            vulnerability_type=taint_flow.vulnerability_type,
            source_location=(taint_flow.source.file_path, taint_flow.source.line_number),
            sink_location=(taint_flow.sink.file_path, taint_flow.sink.line_number),
            taint_flow=taint_flow
        )
        
        # Find execution paths from source to sink
        execution_paths = self._find_execution_paths(
            taint_flow.source.file_path, taint_flow.source.line_number,
            taint_flow.sink.file_path, taint_flow.sink.line_number
        )
        
        vuln_path.execution_paths = execution_paths
        
        # Generate code slice for the vulnerability
        slice_point = SlicePoint(
            file_path=taint_flow.sink.file_path,
            line_number=taint_flow.sink.line_number,
            criterion=taint_flow.vulnerability_type.value
        )
        
        vuln_path.code_slice = self.code_slicer.extract_minimal_sufficient_set(slice_point)
        
        # Validate each execution path
        for path in execution_paths:
            self._validate_execution_path(path, vuln_path)
        
        # Determine overall validation result
        vuln_path.validation_result = self._determine_validation_result(vuln_path)
        vuln_path.exploitability_score = self._calculate_exploitability_score(vuln_path)
        
        # Build evidence chain
        vuln_path.evidence_chain = self._build_evidence_chain(vuln_path)
        
        # Generate attack vectors
        vuln_path.attack_vectors = self._generate_attack_vectors(vuln_path)
        
        # Generate mitigation suggestions
        vuln_path.mitigation_suggestions = self._generate_mitigation_suggestions(vuln_path)
        
        return vuln_path
    
    def _find_execution_paths(self, source_file: str, source_line: int,
                            sink_file: str, sink_line: int) -> List[ExecutionPath]:
        """Find all possible execution paths from source to sink."""
        paths = []
        
        # If source and sink are in the same file, analyze intra-file paths
        if source_file == sink_file:
            paths.extend(self._find_intra_file_paths(source_file, source_line, sink_line))
        else:
            # Analyze inter-file paths using call graph
            paths.extend(self._find_inter_file_paths(source_file, source_line, sink_file, sink_line))
        
        return paths
    
    def _find_intra_file_paths(self, file_path: str, start_line: int, end_line: int) -> List[ExecutionPath]:
        """Find execution paths within a single file."""
        paths = []
        
        # Get semantic analysis
        if file_path not in self.semantic_analyzer.analysis_results:
            self.semantic_analyzer.analyze_file(file_path)
        
        semantic_result = self.semantic_analyzer.analysis_results[file_path]
        
        # Simple path: direct execution from start to end
        if start_line < end_line:
            direct_path = ExecutionPath(
                path_id=f"direct_{start_line}_{end_line}",
                path_type=PathType.DIRECT_PATH,
                start_location=(file_path, start_line),
                end_location=(file_path, end_line)
            )
            
            # Analyze the path
            self._analyze_path_conditions(direct_path, file_path, start_line, end_line)
            paths.append(direct_path)
        
        return paths
    
    def _find_inter_file_paths(self, source_file: str, source_line: int,
                             sink_file: str, sink_line: int) -> List[ExecutionPath]:
        """Find execution paths across multiple files."""
        paths = []
        
        # Use call graph to find paths between files
        call_graph = self.call_graph_builder.build_call_graph()
        
        # Find functions in source and sink files
        source_functions = [f for f in call_graph.functions.values() if f.file_path == source_file]
        sink_functions = [f for f in call_graph.functions.values() if f.file_path == sink_file]
        
        # Find call chains between source and sink functions
        for source_func in source_functions:
            for sink_func in sink_functions:
                call_chains = self.call_graph_builder.get_call_chain(
                    source_func.qualified_name, sink_func.qualified_name
                )
                
                for chain in call_chains:
                    inter_file_path = ExecutionPath(
                        path_id=f"inter_file_{len(paths)}",
                        path_type=PathType.CALLBACK_PATH,
                        start_location=(source_file, source_line),
                        end_location=(sink_file, sink_line)
                    )
                    
                    # Build path nodes from call chain
                    for func in chain:
                        inter_file_path.path_nodes.append((
                            func.file_path, func.line_number, f"Function: {func.name}"
                        ))
                        inter_file_path.function_calls.append(func.qualified_name)
                    
                    paths.append(inter_file_path)
        
        return paths
    
    def _analyze_path_conditions(self, path: ExecutionPath, file_path: str, start_line: int, end_line: int):
        """Analyze conditions that must be met for path execution."""
        tree = self.semantic_analyzer.file_asts[file_path]
        
        # Find control flow statements between start and end lines
        for node in ast.walk(tree):
            if (hasattr(node, 'lineno') and start_line <= node.lineno <= end_line and
                isinstance(node, (ast.If, ast.While, ast.For, ast.Try))):
                
                condition = PathCondition(
                    condition_type=type(node).__name__.lower(),
                    file_path=file_path,
                    line_number=node.lineno,
                    condition_expr=self._extract_condition_expr(node),
                    complexity_score=self._calculate_condition_complexity(node)
                )
                
                path.conditions.append(condition)
        
        # Calculate overall path complexity
        path.complexity_score = sum(c.complexity_score for c in path.conditions) / max(len(path.conditions), 1)
    
    def _extract_condition_expr(self, node: ast.AST) -> str:
        """Extract condition expression from AST node."""
        try:
            if isinstance(node, ast.If):
                return ast.unparse(node.test)
            elif isinstance(node, ast.While):
                return ast.unparse(node.test)
            elif isinstance(node, ast.For):
                return f"{ast.unparse(node.target)} in {ast.unparse(node.iter)}"
            else:
                return str(type(node).__name__)
        except:
            return "complex_condition"
    
    def _calculate_condition_complexity(self, node: ast.AST) -> float:
        """Calculate complexity score for a condition."""
        complexity = 0.1  # Base complexity
        
        # Count logical operators
        for child in ast.walk(node):
            if isinstance(child, (ast.And, ast.Or)):
                complexity += 0.2
            elif isinstance(child, ast.Not):
                complexity += 0.1
            elif isinstance(child, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                complexity += 0.1
        
        return min(complexity, 1.0)
    
    def _validate_execution_path(self, path: ExecutionPath, vuln_path: VulnerabilityPath):
        """Validate if an execution path is feasible."""
        # Calculate feasibility based on conditions
        if not path.conditions:
            path.feasibility_score = 0.9  # High feasibility for unconditional paths
        else:
            # Analyze condition satisfiability
            satisfiable_conditions = 0
            for condition in path.conditions:
                if self._is_condition_satisfiable(condition, vuln_path):
                    satisfiable_conditions += 1
                    condition.is_satisfiable = True
                else:
                    condition.is_satisfiable = False
            
            path.feasibility_score = satisfiable_conditions / len(path.conditions)
    
    def _is_condition_satisfiable(self, condition: PathCondition, vuln_path: VulnerabilityPath) -> bool:
        """Check if a condition can be satisfied for exploitation."""
        # Simplified satisfiability check
        # In practice, this would involve more sophisticated analysis
        
        # Simple heuristics
        if condition.condition_type == 'if':
            # Most if conditions can be satisfied with appropriate input
            return condition.complexity_score < self.complexity_threshold
        elif condition.condition_type in ['while', 'for']:
            # Loops might be harder to control
            return condition.complexity_score < 0.5
        else:
            return True
    
    def _determine_validation_result(self, vuln_path: VulnerabilityPath) -> ValidationResult:
        """Determine the overall validation result for a vulnerability path."""
        if not vuln_path.execution_paths:
            return ValidationResult.INSUFFICIENT_INFO
        
        # Check if any path is highly feasible
        max_feasibility = max(path.feasibility_score for path in vuln_path.execution_paths)
        
        if max_feasibility >= 0.8:
            return ValidationResult.EXPLOITABLE
        elif max_feasibility >= 0.5:
            return ValidationResult.POTENTIALLY_EXPLOITABLE
        else:
            return ValidationResult.NOT_EXPLOITABLE
    
    def _calculate_exploitability_score(self, vuln_path: VulnerabilityPath) -> float:
        """Calculate overall exploitability score."""
        if not vuln_path.execution_paths:
            return 0.0
        
        # Base score from taint flow
        base_score = 0.5
        if vuln_path.taint_flow and vuln_path.taint_flow.is_exploitable:
            base_score = 0.7
        
        # Adjust based on path feasibility
        max_feasibility = max(path.feasibility_score for path in vuln_path.execution_paths)
        feasibility_bonus = max_feasibility * 0.3
        
        # Adjust based on vulnerability type severity
        severity_multiplier = {
            TaintType.COMMAND_INJECTION: 1.0,
            TaintType.SQL_INJECTION: 0.9,
            TaintType.XSS: 0.7,
            TaintType.PATH_TRAVERSAL: 0.8,
            TaintType.USER_INPUT: 0.6
        }.get(vuln_path.vulnerability_type, 0.5)
        
        return min((base_score + feasibility_bonus) * severity_multiplier, 1.0)
    
    def _build_evidence_chain(self, vuln_path: VulnerabilityPath) -> List[Dict[str, Any]]:
        """Build evidence chain for the vulnerability."""
        evidence = []
        
        # Source evidence
        evidence.append({
            "type": "source",
            "location": vuln_path.source_location,
            "description": f"Taint source: {vuln_path.vulnerability_type.value}",
            "evidence": "User-controlled input enters the system"
        })
        
        # Path evidence
        for i, path in enumerate(vuln_path.execution_paths):
            if path.feasibility_score > 0.5:
                evidence.append({
                    "type": "execution_path",
                    "path_id": path.path_id,
                    "feasibility": path.feasibility_score,
                    "description": f"Feasible execution path with {len(path.conditions)} conditions",
                    "evidence": f"Path can be executed with {path.feasibility_score:.1%} confidence"
                })
        
        # Sink evidence
        evidence.append({
            "type": "sink",
            "location": vuln_path.sink_location,
            "description": f"Vulnerable sink for {vuln_path.vulnerability_type.value}",
            "evidence": "Tainted data reaches dangerous function without proper sanitization"
        })
        
        return evidence
    
    def _generate_attack_vectors(self, vuln_path: VulnerabilityPath) -> List[str]:
        """Generate possible attack vectors."""
        vectors = []
        
        attack_patterns = {
            TaintType.COMMAND_INJECTION: [
                "Inject shell commands through user input",
                "Use command chaining with ; or &&",
                "Exploit subprocess calls with shell=True"
            ],
            TaintType.SQL_INJECTION: [
                "Inject SQL commands through user input",
                "Use UNION attacks to extract data",
                "Exploit dynamic query construction"
            ],
            TaintType.XSS: [
                "Inject JavaScript through user input",
                "Use script tags in form inputs",
                "Exploit reflected or stored XSS"
            ],
            TaintType.PATH_TRAVERSAL: [
                "Use ../ sequences to access parent directories",
                "Exploit file operations with user-controlled paths",
                "Access sensitive files outside intended directory"
            ]
        }
        
        return attack_patterns.get(vuln_path.vulnerability_type, ["Generic input manipulation"])
    
    def _generate_mitigation_suggestions(self, vuln_path: VulnerabilityPath) -> List[str]:
        """Generate mitigation suggestions."""
        suggestions = []
        
        mitigation_patterns = {
            TaintType.COMMAND_INJECTION: [
                "Use subprocess with shell=False",
                "Validate and sanitize all user inputs",
                "Use parameterized commands or whitelisting"
            ],
            TaintType.SQL_INJECTION: [
                "Use parameterized queries or prepared statements",
                "Validate and sanitize database inputs",
                "Use ORM frameworks with built-in protection"
            ],
            TaintType.XSS: [
                "Escape HTML output properly",
                "Use Content Security Policy (CSP)",
                "Validate and sanitize user inputs"
            ],
            TaintType.PATH_TRAVERSAL: [
                "Validate and normalize file paths",
                "Use os.path.normpath and check against whitelist",
                "Restrict file operations to specific directories"
            ]
        }
        
        return mitigation_patterns.get(vuln_path.vulnerability_type, ["Validate and sanitize all inputs"])
    
    def _calculate_validation_coverage(self, result: PathValidationResult) -> float:
        """Calculate validation coverage percentage."""
        if result.total_paths_analyzed == 0:
            return 0.0
        
        validated_paths = len([p for p in result.vulnerability_paths 
                             if p.validation_result != ValidationResult.INSUFFICIENT_INFO])
        
        return validated_paths / result.total_paths_analyzed
    
    def _calculate_analysis_confidence(self, result: PathValidationResult) -> float:
        """Calculate confidence in the analysis results."""
        if not result.vulnerability_paths:
            return 0.0
        
        # Base confidence from validation coverage
        base_confidence = result.validation_coverage
        
        # Adjust based on exploitability scores
        avg_exploitability = sum(p.exploitability_score for p in result.vulnerability_paths) / len(result.vulnerability_paths)
        
        # Higher exploitability scores generally indicate more confident analysis
        confidence_bonus = avg_exploitability * 0.2
        
        return min(base_confidence + confidence_bonus, 1.0)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results."""
        all_vuln_paths = []
        for result in self.validation_results.values():
            all_vuln_paths.extend(result.vulnerability_paths)
        
        if not all_vuln_paths:
            return {"total_vulnerabilities": 0}
        
        # Group by validation result
        by_result = {}
        for path in all_vuln_paths:
            result_type = path.validation_result.value
            by_result[result_type] = by_result.get(result_type, 0) + 1
        
        # Group by vulnerability type
        by_type = {}
        for path in all_vuln_paths:
            vuln_type = path.vulnerability_type.value
            by_type[vuln_type] = by_type.get(vuln_type, 0) + 1
        
        return {
            "total_vulnerabilities": len(all_vuln_paths),
            "by_validation_result": by_result,
            "by_vulnerability_type": by_type,
            "average_exploitability": sum(p.exploitability_score for p in all_vuln_paths) / len(all_vuln_paths),
            "files_analyzed": len(self.validation_results)
        }
