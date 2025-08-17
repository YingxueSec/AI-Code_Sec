"""
Semantic analysis engine for AI Code Audit System.

This module provides comprehensive semantic analysis including:
- Variable dependency analysis
- Data flow analysis
- Control flow analysis
- Symbol resolution and scope analysis
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from ..core.models import FileInfo, ProjectInfo

logger = logging.getLogger(__name__)


class VariableType(Enum):
    """Types of variables in semantic analysis."""
    LOCAL = "local"
    PARAMETER = "parameter"
    GLOBAL = "global"
    ATTRIBUTE = "attribute"
    BUILTIN = "builtin"
    IMPORTED = "imported"


class DataFlowType(Enum):
    """Types of data flow."""
    ASSIGNMENT = "assignment"
    FUNCTION_CALL = "function_call"
    RETURN = "return"
    PARAMETER_PASSING = "parameter_passing"
    ATTRIBUTE_ACCESS = "attribute_access"
    SUBSCRIPT_ACCESS = "subscript_access"


@dataclass
class Variable:
    """Represents a variable in the code."""
    name: str
    var_type: VariableType
    scope: str
    defined_at: Tuple[int, int]  # (line, column)
    file_path: str
    data_type: Optional[str] = None
    is_tainted: bool = False
    taint_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlow:
    """Represents a data flow edge."""
    source: Variable
    target: Variable
    flow_type: DataFlowType
    location: Tuple[int, int]  # (line, column)
    file_path: str
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ControlFlowNode:
    """Represents a node in the control flow graph."""
    node_id: str
    node_type: str  # 'statement', 'condition', 'loop', 'function_entry', 'function_exit'
    line_number: int
    file_path: str
    ast_node: ast.AST
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticAnalysisResult:
    """Result of semantic analysis."""
    file_path: str
    variables: Dict[str, Variable] = field(default_factory=dict)
    data_flows: List[DataFlow] = field(default_factory=list)
    control_flow_nodes: Dict[str, ControlFlowNode] = field(default_factory=dict)
    function_definitions: Dict[str, ast.FunctionDef] = field(default_factory=dict)
    class_definitions: Dict[str, ast.ClassDef] = field(default_factory=dict)
    imports: Dict[str, ast.Import] = field(default_factory=dict)
    scopes: Dict[str, Set[str]] = field(default_factory=dict)  # scope -> variable names
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticAnalyzer:
    """Comprehensive semantic analysis engine."""
    
    def __init__(self, project_info: ProjectInfo):
        """Initialize semantic analyzer."""
        self.project_info = project_info
        self.file_contents: Dict[str, str] = {}
        self.file_asts: Dict[str, ast.AST] = {}
        self.analysis_results: Dict[str, SemanticAnalysisResult] = {}
        
        # Global symbol table across all files
        self.global_symbols: Dict[str, Variable] = {}
        self.cross_file_references: Dict[str, List[str]] = {}  # file -> referenced files
        
        # Load and parse files
        self._load_project_files()
    
    def _load_project_files(self):
        """Load and parse all project files."""
        logger.info("Loading project files for semantic analysis...")
        
        for file_info in self.project_info.files:
            if file_info.language == 'python':
                try:
                    file_path = Path(file_info.absolute_path)
                    if file_path.exists():
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        self.file_contents[file_info.path] = content
                        
                        # Parse AST
                        tree = ast.parse(content, filename=file_info.path)
                        self.file_asts[file_info.path] = tree
                        
                except Exception as e:
                    logger.warning(f"Failed to load {file_info.path}: {e}")
        
        logger.info(f"Loaded {len(self.file_asts)} Python files for analysis")
    
    def analyze_file(self, file_path: str) -> SemanticAnalysisResult:
        """Perform semantic analysis on a single file."""
        if file_path not in self.file_asts:
            raise ValueError(f"File {file_path} not found or not parsed")
        
        result = SemanticAnalysisResult(file_path=file_path)
        tree = self.file_asts[file_path]
        
        # Analyze in phases
        self._analyze_definitions(tree, result)
        self._analyze_variables(tree, result)
        self._analyze_data_flows(tree, result)
        self._analyze_control_flows(tree, result)
        self._analyze_scopes(tree, result)
        
        self.analysis_results[file_path] = result
        return result
    
    def analyze_all_files(self) -> Dict[str, SemanticAnalysisResult]:
        """Perform semantic analysis on all files."""
        logger.info("Starting semantic analysis of all files...")
        
        for file_path in self.file_asts:
            try:
                self.analyze_file(file_path)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
        
        # Build cross-file references
        self._build_cross_file_references()
        
        logger.info(f"Completed semantic analysis of {len(self.analysis_results)} files")
        return self.analysis_results
    
    def _analyze_definitions(self, tree: ast.AST, result: SemanticAnalysisResult):
        """Analyze function and class definitions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result.function_definitions[node.name] = node
            elif isinstance(node, ast.ClassDef):
                result.class_definitions[node.name] = node
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                # Handle imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.asname or alias.name
                        result.imports[import_name] = node
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        import_name = alias.asname or alias.name
                        result.imports[f"{module}.{import_name}"] = node
    
    def _analyze_variables(self, tree: ast.AST, result: SemanticAnalysisResult):
        """Analyze variable definitions and usage."""
        current_scope = "global"
        scope_stack = [current_scope]
        
        class VariableVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, result):
                self.analyzer = analyzer
                self.result = result
                self.current_scope = "global"
                self.scope_stack = ["global"]
            
            def visit_FunctionDef(self, node):
                # Enter function scope
                func_scope = f"function:{node.name}:{node.lineno}"
                self.scope_stack.append(func_scope)
                self.current_scope = func_scope
                
                # Analyze parameters
                for arg in node.args.args:
                    var = Variable(
                        name=arg.arg,
                        var_type=VariableType.PARAMETER,
                        scope=self.current_scope,
                        defined_at=(node.lineno, node.col_offset),
                        file_path=result.file_path
                    )
                    self.result.variables[f"{self.current_scope}:{arg.arg}"] = var
                
                # Visit function body
                self.generic_visit(node)
                
                # Exit function scope
                self.scope_stack.pop()
                self.current_scope = self.scope_stack[-1]
            
            def visit_ClassDef(self, node):
                # Enter class scope
                class_scope = f"class:{node.name}:{node.lineno}"
                self.scope_stack.append(class_scope)
                self.current_scope = class_scope
                
                # Visit class body
                self.generic_visit(node)
                
                # Exit class scope
                self.scope_stack.pop()
                self.current_scope = self.scope_stack[-1]
            
            def visit_Assign(self, node):
                # Analyze assignments
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var = Variable(
                            name=target.id,
                            var_type=VariableType.LOCAL if self.current_scope != "global" else VariableType.GLOBAL,
                            scope=self.current_scope,
                            defined_at=(node.lineno, node.col_offset),
                            file_path=result.file_path
                        )
                        self.result.variables[f"{self.current_scope}:{target.id}"] = var
                
                self.generic_visit(node)
            
            def visit_Name(self, node):
                # Analyze variable usage
                if isinstance(node.ctx, ast.Load):
                    # This is a variable read
                    var_key = f"{self.current_scope}:{node.id}"
                    if var_key not in self.result.variables:
                        # Check if it's in outer scopes
                        for scope in reversed(self.scope_stack):
                            scope_key = f"{scope}:{node.id}"
                            if scope_key in self.result.variables:
                                break
                        else:
                            # Unknown variable - might be builtin or imported
                            var = Variable(
                                name=node.id,
                                var_type=VariableType.BUILTIN if node.id in __builtins__ else VariableType.IMPORTED,
                                scope=self.current_scope,
                                defined_at=(node.lineno, node.col_offset),
                                file_path=result.file_path
                            )
                            self.result.variables[var_key] = var
        
        visitor = VariableVisitor(self, result)
        visitor.visit(tree)
    
    def _analyze_data_flows(self, tree: ast.AST, result: SemanticAnalysisResult):
        """Analyze data flow relationships."""
        class DataFlowVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, result):
                self.analyzer = analyzer
                self.result = result
                self.current_scope = "global"
            
            def visit_FunctionDef(self, node):
                old_scope = self.current_scope
                self.current_scope = f"function:{node.name}:{node.lineno}"
                self.generic_visit(node)
                self.current_scope = old_scope
            
            def visit_ClassDef(self, node):
                old_scope = self.current_scope
                self.current_scope = f"class:{node.name}:{node.lineno}"
                self.generic_visit(node)
                self.current_scope = old_scope
            
            def visit_Assign(self, node):
                # Create data flow from value to target
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Name):
                        source_key = f"{self.current_scope}:{node.value.id}"
                        target_key = f"{self.current_scope}:{target.id}"
                        
                        source_var = self.result.variables.get(source_key)
                        target_var = self.result.variables.get(target_key)
                        
                        if source_var and target_var:
                            flow = DataFlow(
                                source=source_var,
                                target=target_var,
                                flow_type=DataFlowType.ASSIGNMENT,
                                location=(node.lineno, node.col_offset),
                                file_path=result.file_path
                            )
                            self.result.data_flows.append(flow)
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Analyze function calls for data flow
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    # Create data flows for arguments
                    for i, arg in enumerate(node.args):
                        if isinstance(arg, ast.Name):
                            arg_key = f"{self.current_scope}:{arg.id}"
                            arg_var = self.result.variables.get(arg_key)
                            
                            if arg_var:
                                # Create a synthetic parameter variable
                                param_var = Variable(
                                    name=f"{func_name}_param_{i}",
                                    var_type=VariableType.PARAMETER,
                                    scope=f"function:{func_name}",
                                    defined_at=(node.lineno, node.col_offset),
                                    file_path=result.file_path
                                )
                                
                                flow = DataFlow(
                                    source=arg_var,
                                    target=param_var,
                                    flow_type=DataFlowType.PARAMETER_PASSING,
                                    location=(node.lineno, node.col_offset),
                                    file_path=result.file_path,
                                    context=f"call to {func_name}"
                                )
                                self.result.data_flows.append(flow)
                
                self.generic_visit(node)
        
        visitor = DataFlowVisitor(self, result)
        visitor.visit(tree)
    
    def _analyze_control_flows(self, tree: ast.AST, result: SemanticAnalysisResult):
        """Analyze control flow graph."""
        node_counter = 0
        
        def create_node(ast_node, node_type):
            nonlocal node_counter
            node_id = f"node_{node_counter}"
            node_counter += 1
            
            cf_node = ControlFlowNode(
                node_id=node_id,
                node_type=node_type,
                line_number=ast_node.lineno,
                file_path=result.file_path,
                ast_node=ast_node
            )
            result.control_flow_nodes[node_id] = cf_node
            return cf_node
        
        class ControlFlowVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_node = None
                self.break_targets = []
                self.continue_targets = []
            
            def visit_FunctionDef(self, node):
                entry_node = create_node(node, 'function_entry')
                old_current = self.current_node
                self.current_node = entry_node
                
                # Visit function body
                for stmt in node.body:
                    self.visit(stmt)
                
                # Create exit node
                exit_node = create_node(node, 'function_exit')
                if self.current_node:
                    self.current_node.successors.add(exit_node.node_id)
                    exit_node.predecessors.add(self.current_node.node_id)
                
                self.current_node = old_current
            
            def visit_If(self, node):
                condition_node = create_node(node, 'condition')
                
                if self.current_node:
                    self.current_node.successors.add(condition_node.node_id)
                    condition_node.predecessors.add(self.current_node.node_id)
                
                # Visit if body
                old_current = self.current_node
                self.current_node = condition_node
                
                for stmt in node.body:
                    self.visit(stmt)
                
                if_end = self.current_node
                
                # Visit else body if exists
                self.current_node = condition_node
                if node.orelse:
                    for stmt in node.orelse:
                        self.visit(stmt)
                
                else_end = self.current_node
                
                # Merge point
                merge_node = create_node(node, 'statement')
                if if_end:
                    if_end.successors.add(merge_node.node_id)
                    merge_node.predecessors.add(if_end.node_id)
                if else_end and else_end != condition_node:
                    else_end.successors.add(merge_node.node_id)
                    merge_node.predecessors.add(else_end.node_id)
                elif else_end == condition_node:
                    condition_node.successors.add(merge_node.node_id)
                    merge_node.predecessors.add(condition_node.node_id)
                
                self.current_node = merge_node
            
            def visit_While(self, node):
                loop_header = create_node(node, 'loop')
                
                if self.current_node:
                    self.current_node.successors.add(loop_header.node_id)
                    loop_header.predecessors.add(self.current_node.node_id)
                
                # Visit loop body
                old_current = self.current_node
                old_break = self.break_targets[:]
                old_continue = self.continue_targets[:]
                
                self.current_node = loop_header
                self.break_targets.append(loop_header)
                self.continue_targets.append(loop_header)
                
                for stmt in node.body:
                    self.visit(stmt)
                
                # Loop back
                if self.current_node:
                    self.current_node.successors.add(loop_header.node_id)
                    loop_header.predecessors.add(self.current_node.node_id)
                
                self.current_node = loop_header
                self.break_targets = old_break
                self.continue_targets = old_continue
            
            def generic_visit(self, node):
                if hasattr(node, 'lineno'):
                    stmt_node = create_node(node, 'statement')
                    
                    if self.current_node:
                        self.current_node.successors.add(stmt_node.node_id)
                        stmt_node.predecessors.add(self.current_node.node_id)
                    
                    self.current_node = stmt_node
                
                super().generic_visit(node)
        
        visitor = ControlFlowVisitor()
        visitor.visit(tree)
    
    def _analyze_scopes(self, tree: ast.AST, result: SemanticAnalysisResult):
        """Analyze scope relationships."""
        for var_key, variable in result.variables.items():
            scope = variable.scope
            if scope not in result.scopes:
                result.scopes[scope] = set()
            result.scopes[scope].add(variable.name)
    
    def _build_cross_file_references(self):
        """Build cross-file reference relationships."""
        for file_path, result in self.analysis_results.items():
            references = []
            
            # Analyze imports to find referenced files
            for import_name, import_node in result.imports.items():
                if isinstance(import_node, ast.ImportFrom) and import_node.module:
                    # Try to resolve module to file path
                    module_parts = import_node.module.split('.')
                    potential_file = '/'.join(module_parts) + '.py'
                    
                    # Check if this file exists in our project
                    for other_file in self.analysis_results:
                        if other_file.endswith(potential_file):
                            references.append(other_file)
                            break
            
            self.cross_file_references[file_path] = references
    
    def get_variable_dependencies(self, file_path: str, variable_name: str) -> List[Variable]:
        """Get all variables that the given variable depends on."""
        if file_path not in self.analysis_results:
            return []
        
        result = self.analysis_results[file_path]
        dependencies = []
        
        # Find data flows where this variable is the target
        for flow in result.data_flows:
            if flow.target.name == variable_name:
                dependencies.append(flow.source)
        
        return dependencies
    
    def get_variable_uses(self, file_path: str, variable_name: str) -> List[Variable]:
        """Get all variables that use the given variable."""
        if file_path not in self.analysis_results:
            return []
        
        result = self.analysis_results[file_path]
        uses = []
        
        # Find data flows where this variable is the source
        for flow in result.data_flows:
            if flow.source.name == variable_name:
                uses.append(flow.target)
        
        return uses
    
    def find_paths_between_variables(self, file_path: str, source_var: str, target_var: str) -> List[List[DataFlow]]:
        """Find all data flow paths between two variables."""
        if file_path not in self.analysis_results:
            return []
        
        result = self.analysis_results[file_path]
        paths = []
        
        def dfs(current_var, target, path, visited):
            if current_var == target:
                paths.append(path[:])
                return
            
            if current_var in visited:
                return
            
            visited.add(current_var)
            
            # Find outgoing flows
            for flow in result.data_flows:
                if flow.source.name == current_var:
                    path.append(flow)
                    dfs(flow.target.name, target, path, visited)
                    path.pop()
            
            visited.remove(current_var)
        
        dfs(source_var, target_var, [], set())
        return paths
