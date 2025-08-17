"""
Code slicing system for AI Code Audit System.

This module provides high-precision code slicing including:
- Backward slicing for vulnerability analysis
- Forward slicing for impact analysis
- Minimal sufficient set extraction
- Security-focused slicing criteria
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .semantic_analyzer import SemanticAnalyzer, Variable, DataFlow
from .call_graph import CallGraphBuilder, FunctionNode, CallEdge

logger = logging.getLogger(__name__)


class SliceType(Enum):
    """Types of code slices."""
    BACKWARD = "backward"
    FORWARD = "forward"
    BIDIRECTIONAL = "bidirectional"
    SECURITY_FOCUSED = "security_focused"


class SliceCriterion(Enum):
    """Criteria for code slicing."""
    VARIABLE_USE = "variable_use"
    FUNCTION_CALL = "function_call"
    SECURITY_SINK = "security_sink"
    SECURITY_SOURCE = "security_source"
    CONTROL_DEPENDENCY = "control_dependency"
    DATA_DEPENDENCY = "data_dependency"


@dataclass
class SlicePoint:
    """Represents a point of interest for slicing."""
    file_path: str
    line_number: int
    variable_name: Optional[str] = None
    function_name: Optional[str] = None
    criterion: SliceCriterion = SliceCriterion.VARIABLE_USE
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SliceNode:
    """Represents a node in the code slice."""
    file_path: str
    line_number: int
    ast_node: ast.AST
    node_type: str
    content: str
    variables_defined: Set[str] = field(default_factory=set)
    variables_used: Set[str] = field(default_factory=set)
    functions_called: Set[str] = field(default_factory=set)
    control_dependencies: Set[int] = field(default_factory=set)  # Line numbers
    data_dependencies: Set[int] = field(default_factory=set)     # Line numbers
    security_relevance: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSlice:
    """Represents a code slice result."""
    slice_type: SliceType
    criterion: SlicePoint
    nodes: List[SliceNode] = field(default_factory=list)
    entry_points: List[SliceNode] = field(default_factory=list)
    exit_points: List[SliceNode] = field(default_factory=list)
    cross_file_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    security_score: float = 0.0
    completeness_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def line_count(self) -> int:
        """Get total number of lines in the slice."""
        return len(self.nodes)
    
    @property
    def file_count(self) -> int:
        """Get number of files involved in the slice."""
        return len(set(node.file_path for node in self.nodes))
    
    def get_code_content(self) -> str:
        """Get the actual code content of the slice."""
        # Group nodes by file and line number
        file_lines = {}
        for node in self.nodes:
            if node.file_path not in file_lines:
                file_lines[node.file_path] = {}
            file_lines[node.file_path][node.line_number] = node.content
        
        # Generate code content
        content_parts = []
        for file_path, lines in file_lines.items():
            content_parts.append(f"# File: {file_path}")
            for line_num in sorted(lines.keys()):
                content_parts.append(f"{line_num:4d}: {lines[line_num]}")
            content_parts.append("")
        
        return "\n".join(content_parts)


class CodeSlicer:
    """High-precision code slicing system."""
    
    def __init__(self, semantic_analyzer: SemanticAnalyzer, call_graph_builder: CallGraphBuilder):
        """Initialize code slicer."""
        self.semantic_analyzer = semantic_analyzer
        self.call_graph_builder = call_graph_builder
        self.file_contents = semantic_analyzer.file_contents
        self.file_asts = semantic_analyzer.file_asts
        
        # Security-relevant patterns
        self.security_sources = {
            'input', 'raw_input', 'request.args', 'request.form', 'request.json',
            'sys.argv', 'os.environ', 'request.GET', 'request.POST'
        }
        
        self.security_sinks = {
            'eval', 'exec', 'compile', 'os.system', 'subprocess.call',
            'subprocess.run', 'open', 'file', 'sql.execute', 'cursor.execute'
        }
        
        self.control_flow_statements = {
            ast.If, ast.While, ast.For, ast.Try, ast.With, ast.AsyncWith
        }
    
    def slice_backward(self, slice_point: SlicePoint) -> CodeSlice:
        """Perform backward slicing from a given point."""
        logger.info(f"Performing backward slice from {slice_point.file_path}:{slice_point.line_number}")
        
        slice_result = CodeSlice(
            slice_type=SliceType.BACKWARD,
            criterion=slice_point
        )
        
        # Get semantic analysis for the file
        if slice_point.file_path not in self.semantic_analyzer.analysis_results:
            self.semantic_analyzer.analyze_file(slice_point.file_path)
        
        analysis_result = self.semantic_analyzer.analysis_results[slice_point.file_path]
        
        # Find the target variable or statement
        target_nodes = self._find_target_nodes(slice_point, analysis_result)
        
        # Perform backward traversal
        visited_lines = set()
        slice_nodes = []
        
        for target_node in target_nodes:
            self._backward_traverse(
                target_node, slice_point, analysis_result, 
                visited_lines, slice_nodes
            )
        
        # Sort nodes by file and line number
        slice_nodes.sort(key=lambda n: (n.file_path, n.line_number))
        slice_result.nodes = slice_nodes
        
        # Calculate scores
        slice_result.security_score = self._calculate_security_score(slice_nodes)
        slice_result.completeness_score = self._calculate_completeness_score(slice_nodes, slice_point)
        
        logger.info(f"Backward slice complete: {len(slice_nodes)} nodes, "
                   f"security score: {slice_result.security_score:.2f}")
        
        return slice_result
    
    def slice_forward(self, slice_point: SlicePoint) -> CodeSlice:
        """Perform forward slicing from a given point."""
        logger.info(f"Performing forward slice from {slice_point.file_path}:{slice_point.line_number}")
        
        slice_result = CodeSlice(
            slice_type=SliceType.FORWARD,
            criterion=slice_point
        )
        
        # Get semantic analysis for the file
        if slice_point.file_path not in self.semantic_analyzer.analysis_results:
            self.semantic_analyzer.analyze_file(slice_point.file_path)
        
        analysis_result = self.semantic_analyzer.analysis_results[slice_point.file_path]
        
        # Find the target variable or statement
        target_nodes = self._find_target_nodes(slice_point, analysis_result)
        
        # Perform forward traversal
        visited_lines = set()
        slice_nodes = []
        
        for target_node in target_nodes:
            self._forward_traverse(
                target_node, slice_point, analysis_result,
                visited_lines, slice_nodes
            )
        
        # Sort nodes by file and line number
        slice_nodes.sort(key=lambda n: (n.file_path, n.line_number))
        slice_result.nodes = slice_nodes
        
        # Calculate scores
        slice_result.security_score = self._calculate_security_score(slice_nodes)
        slice_result.completeness_score = self._calculate_completeness_score(slice_nodes, slice_point)
        
        logger.info(f"Forward slice complete: {len(slice_nodes)} nodes, "
                   f"security score: {slice_result.security_score:.2f}")
        
        return slice_result
    
    def slice_security_focused(self, slice_point: SlicePoint) -> CodeSlice:
        """Perform security-focused slicing."""
        logger.info(f"Performing security-focused slice from {slice_point.file_path}:{slice_point.line_number}")
        
        # Perform both backward and forward slicing
        backward_slice = self.slice_backward(slice_point)
        forward_slice = self.slice_forward(slice_point)
        
        # Combine and deduplicate nodes
        all_nodes = {}
        for node in backward_slice.nodes + forward_slice.nodes:
            key = (node.file_path, node.line_number)
            if key not in all_nodes or node.security_relevance > all_nodes[key].security_relevance:
                all_nodes[key] = node
        
        # Filter for security-relevant nodes
        security_nodes = [
            node for node in all_nodes.values()
            if node.security_relevance > 0.3  # Threshold for security relevance
        ]
        
        # Sort nodes
        security_nodes.sort(key=lambda n: (n.file_path, n.line_number))
        
        slice_result = CodeSlice(
            slice_type=SliceType.SECURITY_FOCUSED,
            criterion=slice_point,
            nodes=security_nodes
        )
        
        # Calculate enhanced security score
        slice_result.security_score = self._calculate_security_score(security_nodes) * 1.2  # Boost for security focus
        slice_result.completeness_score = self._calculate_completeness_score(security_nodes, slice_point)
        
        logger.info(f"Security-focused slice complete: {len(security_nodes)} nodes, "
                   f"security score: {slice_result.security_score:.2f}")
        
        return slice_result
    
    def extract_minimal_sufficient_set(self, slice_point: SlicePoint) -> CodeSlice:
        """Extract minimal sufficient set for security analysis."""
        logger.info(f"Extracting minimal sufficient set for {slice_point.file_path}:{slice_point.line_number}")
        
        # Start with security-focused slice
        full_slice = self.slice_security_focused(slice_point)
        
        # Apply minimization algorithm
        minimal_nodes = self._minimize_slice(full_slice.nodes, slice_point)
        
        slice_result = CodeSlice(
            slice_type=SliceType.SECURITY_FOCUSED,
            criterion=slice_point,
            nodes=minimal_nodes
        )
        
        # Identify entry and exit points
        slice_result.entry_points = self._find_entry_points(minimal_nodes)
        slice_result.exit_points = self._find_exit_points(minimal_nodes)
        
        # Calculate scores
        slice_result.security_score = self._calculate_security_score(minimal_nodes)
        slice_result.completeness_score = self._calculate_completeness_score(minimal_nodes, slice_point)
        
        logger.info(f"Minimal sufficient set extracted: {len(minimal_nodes)} nodes, "
                   f"reduction: {len(full_slice.nodes) - len(minimal_nodes)} nodes")
        
        return slice_result
    
    def _find_target_nodes(self, slice_point: SlicePoint, analysis_result) -> List[ast.AST]:
        """Find AST nodes corresponding to the slice point."""
        target_nodes = []
        
        # Get the AST for the file
        tree = self.file_asts[slice_point.file_path]
        
        # Find nodes at the target line
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno == slice_point.line_number:
                target_nodes.append(node)
        
        return target_nodes
    
    def _backward_traverse(self, target_node: ast.AST, slice_point: SlicePoint, 
                          analysis_result, visited_lines: Set[int], slice_nodes: List[SliceNode]):
        """Perform backward traversal for slicing."""
        if not hasattr(target_node, 'lineno'):
            return
        
        line_num = target_node.lineno
        if line_num in visited_lines:
            return
        
        visited_lines.add(line_num)
        
        # Create slice node
        slice_node = self._create_slice_node(target_node, slice_point.file_path, analysis_result)
        slice_nodes.append(slice_node)
        
        # Find dependencies
        if slice_point.variable_name:
            # Find data dependencies for the variable
            dependencies = self.semantic_analyzer.get_variable_dependencies(
                slice_point.file_path, slice_point.variable_name
            )
            
            for dep_var in dependencies:
                # Find the AST node for this dependency
                dep_nodes = self._find_nodes_defining_variable(
                    dep_var.name, dep_var.defined_at[0], slice_point.file_path
                )
                
                for dep_node in dep_nodes:
                    self._backward_traverse(dep_node, slice_point, analysis_result, visited_lines, slice_nodes)
        
        # Find control dependencies
        control_deps = self._find_control_dependencies(target_node, slice_point.file_path)
        for control_line in control_deps:
            control_nodes = self._find_nodes_at_line(control_line, slice_point.file_path)
            for control_node in control_nodes:
                self._backward_traverse(control_node, slice_point, analysis_result, visited_lines, slice_nodes)
    
    def _forward_traverse(self, target_node: ast.AST, slice_point: SlicePoint,
                         analysis_result, visited_lines: Set[int], slice_nodes: List[SliceNode]):
        """Perform forward traversal for slicing."""
        if not hasattr(target_node, 'lineno'):
            return
        
        line_num = target_node.lineno
        if line_num in visited_lines:
            return
        
        visited_lines.add(line_num)
        
        # Create slice node
        slice_node = self._create_slice_node(target_node, slice_point.file_path, analysis_result)
        slice_nodes.append(slice_node)
        
        # Find uses of variables defined at this node
        if slice_point.variable_name:
            uses = self.semantic_analyzer.get_variable_uses(
                slice_point.file_path, slice_point.variable_name
            )
            
            for use_var in uses:
                use_nodes = self._find_nodes_using_variable(
                    use_var.name, use_var.defined_at[0], slice_point.file_path
                )
                
                for use_node in use_nodes:
                    self._forward_traverse(use_node, slice_point, analysis_result, visited_lines, slice_nodes)
    
    def _create_slice_node(self, ast_node: ast.AST, file_path: str, analysis_result) -> SliceNode:
        """Create a slice node from an AST node."""
        line_num = ast_node.lineno
        
        # Get the actual line content
        file_lines = self.file_contents[file_path].split('\n')
        content = file_lines[line_num - 1] if line_num <= len(file_lines) else ""
        
        # Analyze the node
        variables_defined = set()
        variables_used = set()
        functions_called = set()
        
        # Extract variables and function calls
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    variables_defined.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    variables_used.add(node.id)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    functions_called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    functions_called.add(node.func.attr)
        
        # Calculate security relevance
        security_relevance = self._calculate_node_security_relevance(
            ast_node, variables_used, functions_called
        )
        
        return SliceNode(
            file_path=file_path,
            line_number=line_num,
            ast_node=ast_node,
            node_type=type(ast_node).__name__,
            content=content.strip(),
            variables_defined=variables_defined,
            variables_used=variables_used,
            functions_called=functions_called,
            security_relevance=security_relevance
        )
    
    def _calculate_node_security_relevance(self, ast_node: ast.AST, 
                                         variables_used: Set[str], functions_called: Set[str]) -> float:
        """Calculate security relevance score for a node."""
        score = 0.0
        
        # Check for security sources
        for source in self.security_sources:
            if source in functions_called or any(source in var for var in variables_used):
                score += 0.8
        
        # Check for security sinks
        for sink in self.security_sinks:
            if sink in functions_called:
                score += 1.0
        
        # Check for control flow statements
        if type(ast_node) in self.control_flow_statements:
            score += 0.3
        
        # Check for assignments to security-relevant variables
        security_keywords = {'password', 'token', 'key', 'secret', 'auth', 'session'}
        for var in variables_used.union(getattr(ast_node, 'variables_defined', set())):
            if any(keyword in var.lower() for keyword in security_keywords):
                score += 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _minimize_slice(self, nodes: List[SliceNode], slice_point: SlicePoint) -> List[SliceNode]:
        """Apply minimization algorithm to reduce slice size."""
        # Sort nodes by security relevance (descending)
        sorted_nodes = sorted(nodes, key=lambda n: n.security_relevance, reverse=True)
        
        # Keep nodes with high security relevance
        essential_nodes = [n for n in sorted_nodes if n.security_relevance > 0.5]
        
        # Add nodes that are directly related to the slice criterion
        criterion_related = [
            n for n in sorted_nodes 
            if (slice_point.variable_name and slice_point.variable_name in n.variables_used.union(n.variables_defined))
            or (slice_point.function_name and slice_point.function_name in n.functions_called)
        ]
        
        # Combine and deduplicate
        minimal_nodes = list({n.line_number: n for n in essential_nodes + criterion_related}.values())
        
        return minimal_nodes
    
    def _find_entry_points(self, nodes: List[SliceNode]) -> List[SliceNode]:
        """Find entry points in the slice."""
        # Entry points are nodes with no dependencies within the slice
        line_numbers = {n.line_number for n in nodes}
        entry_points = []
        
        for node in nodes:
            has_internal_deps = any(
                dep_line in line_numbers 
                for dep_line in node.data_dependencies.union(node.control_dependencies)
            )
            
            if not has_internal_deps:
                entry_points.append(node)
        
        return entry_points
    
    def _find_exit_points(self, nodes: List[SliceNode]) -> List[SliceNode]:
        """Find exit points in the slice."""
        # Exit points are nodes that are not dependencies of other nodes
        dependency_lines = set()
        for node in nodes:
            dependency_lines.update(node.data_dependencies)
            dependency_lines.update(node.control_dependencies)
        
        exit_points = [n for n in nodes if n.line_number not in dependency_lines]
        return exit_points
    
    def _calculate_security_score(self, nodes: List[SliceNode]) -> float:
        """Calculate overall security score for the slice."""
        if not nodes:
            return 0.0
        
        total_score = sum(node.security_relevance for node in nodes)
        return min(total_score / len(nodes), 1.0)
    
    def _calculate_completeness_score(self, nodes: List[SliceNode], slice_point: SlicePoint) -> float:
        """Calculate completeness score for the slice."""
        # This is a simplified completeness metric
        # In practice, this would involve more sophisticated analysis
        
        if not nodes:
            return 0.0
        
        # Check if the slice includes the original slice point
        has_criterion = any(
            n.line_number == slice_point.line_number and n.file_path == slice_point.file_path
            for n in nodes
        )
        
        base_score = 0.8 if has_criterion else 0.3
        
        # Bonus for having both entry and exit points
        entry_points = self._find_entry_points(nodes)
        exit_points = self._find_exit_points(nodes)
        
        if entry_points and exit_points:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _find_control_dependencies(self, node: ast.AST, file_path: str) -> Set[int]:
        """Find control dependencies for a node."""
        # Simplified control dependency analysis
        # In practice, this would use the control flow graph
        control_deps = set()
        
        # This is a placeholder implementation
        # Real implementation would analyze the control flow graph
        
        return control_deps
    
    def _find_nodes_defining_variable(self, var_name: str, line_num: int, file_path: str) -> List[ast.AST]:
        """Find AST nodes that define a variable."""
        nodes = []
        tree = self.file_asts[file_path]
        
        for node in ast.walk(tree):
            if (hasattr(node, 'lineno') and node.lineno == line_num and
                isinstance(node, ast.Assign)):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == var_name:
                        nodes.append(node)
        
        return nodes
    
    def _find_nodes_using_variable(self, var_name: str, line_num: int, file_path: str) -> List[ast.AST]:
        """Find AST nodes that use a variable."""
        nodes = []
        tree = self.file_asts[file_path]
        
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno >= line_num:
                for child in ast.walk(node):
                    if (isinstance(child, ast.Name) and child.id == var_name and
                        isinstance(child.ctx, ast.Load)):
                        nodes.append(node)
                        break
        
        return nodes
    
    def _find_nodes_at_line(self, line_num: int, file_path: str) -> List[ast.AST]:
        """Find all AST nodes at a specific line."""
        nodes = []
        tree = self.file_asts[file_path]
        
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno == line_num:
                nodes.append(node)
        
        return nodes
