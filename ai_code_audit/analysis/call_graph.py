"""
Call graph construction system for AI Code Audit System.

This module provides comprehensive call graph analysis including:
- Function call graph construction
- Class dependency graph building
- Cross-file analysis and resolution
- Method resolution and inheritance tracking
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from ..core.models import FileInfo, ProjectInfo

logger = logging.getLogger(__name__)


class CallType(Enum):
    """Types of function calls."""
    DIRECT_CALL = "direct_call"
    METHOD_CALL = "method_call"
    CONSTRUCTOR_CALL = "constructor_call"
    SUPER_CALL = "super_call"
    DYNAMIC_CALL = "dynamic_call"


class DependencyType(Enum):
    """Types of dependencies."""
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    IMPORT = "import"
    USAGE = "usage"


@dataclass(frozen=True)
class FunctionNode:
    """Represents a function in the call graph."""
    name: str
    qualified_name: str  # module.class.function
    file_path: str
    line_number: int
    is_method: bool = False
    class_name: Optional[str] = None
    parameters: Tuple[str, ...] = field(default_factory=tuple)
    return_type: Optional[str] = None
    is_async: bool = False
    decorators: Tuple[str, ...] = field(default_factory=tuple)
    docstring: Optional[str] = None
    complexity: int = 0

    def __post_init__(self):
        # Convert lists to tuples for hashability
        if isinstance(self.parameters, list):
            object.__setattr__(self, 'parameters', tuple(self.parameters))
        if isinstance(self.decorators, list):
            object.__setattr__(self, 'decorators', tuple(self.decorators))


@dataclass
class CallEdge:
    """Represents a call relationship between functions."""
    caller: FunctionNode
    callee: FunctionNode
    call_type: CallType
    line_number: int
    file_path: str
    arguments: List[str] = field(default_factory=list)
    is_conditional: bool = False
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassNode:
    """Represents a class in the dependency graph."""
    name: str
    qualified_name: str
    file_path: str
    line_number: int
    base_classes: List[str] = field(default_factory=list)
    methods: List[FunctionNode] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_abstract: bool = False
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between classes."""
    source: ClassNode
    target: ClassNode
    dependency_type: DependencyType
    line_number: int
    file_path: str
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallGraphResult:
    """Result of call graph analysis."""
    functions: Dict[str, FunctionNode] = field(default_factory=dict)
    classes: Dict[str, ClassNode] = field(default_factory=dict)
    call_edges: List[CallEdge] = field(default_factory=list)
    dependency_edges: List[DependencyEdge] = field(default_factory=list)
    entry_points: List[FunctionNode] = field(default_factory=list)
    unreachable_functions: List[FunctionNode] = field(default_factory=list)
    cyclic_dependencies: List[List[str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CallGraphBuilder:
    """Comprehensive call graph construction system."""
    
    def __init__(self, project_info: ProjectInfo):
        """Initialize call graph builder."""
        self.project_info = project_info
        self.file_contents: Dict[str, str] = {}
        self.file_asts: Dict[str, ast.AST] = {}
        self.module_names: Dict[str, str] = {}  # file_path -> module_name
        
        # Symbol tables
        self.functions: Dict[str, FunctionNode] = {}
        self.classes: Dict[str, ClassNode] = {}
        self.imports: Dict[str, Dict[str, str]] = {}  # file_path -> {name: module}
        
        # Load and parse files
        self._load_project_files()
    
    def _load_project_files(self):
        """Load and parse all project files."""
        logger.info("Loading project files for call graph analysis...")
        
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
                        
                        # Determine module name
                        module_name = file_info.path.replace('/', '.').replace('.py', '')
                        self.module_names[file_info.path] = module_name
                        
                except Exception as e:
                    logger.warning(f"Failed to load {file_info.path}: {e}")
        
        logger.info(f"Loaded {len(self.file_asts)} Python files for call graph analysis")
    
    def build_call_graph(self) -> CallGraphResult:
        """Build complete call graph for the project."""
        logger.info("Building call graph...")
        
        # Phase 1: Extract all function and class definitions
        self._extract_definitions()
        
        # Phase 2: Analyze imports
        self._analyze_imports()
        
        # Phase 3: Build call relationships
        call_edges = self._build_call_relationships()
        
        # Phase 4: Build class dependencies
        dependency_edges = self._build_class_dependencies()
        
        # Phase 5: Analyze reachability and cycles
        entry_points = self._find_entry_points()
        unreachable_functions = self._find_unreachable_functions(entry_points, call_edges)
        cyclic_dependencies = self._find_cyclic_dependencies(call_edges)
        
        result = CallGraphResult(
            functions=self.functions,
            classes=self.classes,
            call_edges=call_edges,
            dependency_edges=dependency_edges,
            entry_points=entry_points,
            unreachable_functions=unreachable_functions,
            cyclic_dependencies=cyclic_dependencies
        )
        
        logger.info(f"Call graph built: {len(self.functions)} functions, {len(self.classes)} classes, "
                   f"{len(call_edges)} call edges, {len(dependency_edges)} dependency edges")

        # Store result for helper methods
        self._last_result = result

        return result
    
    def _extract_definitions(self):
        """Extract all function and class definitions."""
        for file_path, tree in self.file_asts.items():
            module_name = self.module_names[file_path]
            
            class DefinitionExtractor(ast.NodeVisitor):
                def __init__(self, builder, file_path, module_name):
                    self.builder = builder
                    self.file_path = file_path
                    self.module_name = module_name
                    self.current_class = None
                
                def visit_ClassDef(self, node):
                    # Extract class information
                    qualified_name = f"{self.module_name}.{node.name}"
                    
                    base_classes = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_classes.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_classes.append(ast.unparse(base))
                    
                    class_node = ClassNode(
                        name=node.name,
                        qualified_name=qualified_name,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        base_classes=base_classes,
                        decorators=[ast.unparse(d) for d in node.decorator_list],
                        docstring=ast.get_docstring(node)
                    )
                    
                    self.builder.classes[qualified_name] = class_node
                    
                    # Visit class methods
                    old_class = self.current_class
                    self.current_class = class_node
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    # Extract function information
                    if self.current_class:
                        qualified_name = f"{self.current_class.qualified_name}.{node.name}"
                        is_method = True
                        class_name = self.current_class.name
                    else:
                        qualified_name = f"{self.module_name}.{node.name}"
                        is_method = False
                        class_name = None
                    
                    parameters = [arg.arg for arg in node.args.args]
                    
                    function_node = FunctionNode(
                        name=node.name,
                        qualified_name=qualified_name,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        is_method=is_method,
                        class_name=class_name,
                        parameters=tuple(parameters),
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        decorators=tuple([ast.unparse(d) for d in node.decorator_list]),
                        docstring=ast.get_docstring(node),
                        complexity=self._calculate_complexity(node)
                    )
                    
                    self.builder.functions[qualified_name] = function_node
                    
                    # Add method to class
                    if self.current_class:
                        self.current_class.methods.append(function_node)
                
                def _calculate_complexity(self, node):
                    """Calculate cyclomatic complexity."""
                    complexity = 1  # Base complexity
                    
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                            complexity += 1
                        elif isinstance(child, ast.ExceptHandler):
                            complexity += 1
                        elif isinstance(child, (ast.And, ast.Or)):
                            complexity += 1
                    
                    return complexity
            
            extractor = DefinitionExtractor(self, file_path, module_name)
            extractor.visit(tree)
    
    def _analyze_imports(self):
        """Analyze import statements in all files."""
        for file_path, tree in self.file_asts.items():
            file_imports = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        file_imports[name] = alias.name
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        name = alias.asname or alias.name
                        file_imports[name] = f"{module}.{alias.name}" if module else alias.name
            
            self.imports[file_path] = file_imports
    
    def _build_call_relationships(self) -> List[CallEdge]:
        """Build call relationships between functions."""
        call_edges = []
        
        for file_path, tree in self.file_asts.items():
            
            class CallExtractor(ast.NodeVisitor):
                def __init__(self, builder, file_path):
                    self.builder = builder
                    self.file_path = file_path
                    self.current_function = None
                    self.function_stack = []
                
                def visit_FunctionDef(self, node):
                    # Find the function node
                    module_name = self.builder.module_names[self.file_path]
                    
                    if self.current_function:
                        # Method inside class
                        qualified_name = f"{self.current_function.qualified_name}.{node.name}"
                    else:
                        qualified_name = f"{module_name}.{node.name}"
                    
                    function_node = self.builder.functions.get(qualified_name)
                    if function_node:
                        self.function_stack.append(self.current_function)
                        self.current_function = function_node
                        self.generic_visit(node)
                        self.current_function = self.function_stack.pop()
                
                def visit_Call(self, node):
                    if not self.current_function:
                        return
                    
                    # Analyze function call
                    callee_name = None
                    call_type = CallType.DIRECT_CALL
                    
                    if isinstance(node.func, ast.Name):
                        # Direct function call
                        callee_name = node.func.id
                        call_type = CallType.DIRECT_CALL
                    elif isinstance(node.func, ast.Attribute):
                        # Method call
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == 'super':
                                call_type = CallType.SUPER_CALL
                                callee_name = node.func.attr
                            else:
                                call_type = CallType.METHOD_CALL
                                callee_name = f"{node.func.value.id}.{node.func.attr}"
                        else:
                            call_type = CallType.METHOD_CALL
                            callee_name = node.func.attr
                    
                    if callee_name:
                        # Resolve callee
                        callee_node = self._resolve_callee(callee_name, self.file_path)
                        
                        if callee_node:
                            # Extract arguments
                            arguments = []
                            for arg in node.args:
                                if isinstance(arg, ast.Name):
                                    arguments.append(arg.id)
                                elif isinstance(arg, ast.Constant):
                                    arguments.append(str(arg.value))
                                else:
                                    arguments.append(ast.unparse(arg))
                            
                            edge = CallEdge(
                                caller=self.current_function,
                                callee=callee_node,
                                call_type=call_type,
                                line_number=node.lineno,
                                file_path=self.file_path,
                                arguments=arguments
                            )
                            call_edges.append(edge)
                    
                    self.generic_visit(node)
                
                def _resolve_callee(self, callee_name, file_path):
                    """Resolve callee name to function node."""
                    # Check local functions first
                    module_name = self.builder.module_names[file_path]
                    local_qualified = f"{module_name}.{callee_name}"
                    
                    if local_qualified in self.builder.functions:
                        return self.builder.functions[local_qualified]
                    
                    # Check imports
                    file_imports = self.builder.imports.get(file_path, {})
                    if callee_name in file_imports:
                        imported_name = file_imports[callee_name]
                        if imported_name in self.builder.functions:
                            return self.builder.functions[imported_name]
                    
                    # Check method calls on known classes
                    if '.' in callee_name:
                        parts = callee_name.split('.')
                        if len(parts) == 2:
                            obj_name, method_name = parts
                            # Try to find the method in known classes
                            for class_qualified, class_node in self.builder.classes.items():
                                for method in class_node.methods:
                                    if method.name == method_name:
                                        return method
                    
                    return None
            
            extractor = CallExtractor(self, file_path)
            extractor.visit(tree)
        
        return call_edges
    
    def _build_class_dependencies(self) -> List[DependencyEdge]:
        """Build dependency relationships between classes."""
        dependency_edges = []
        
        for class_qualified, class_node in self.classes.items():
            # Inheritance dependencies
            for base_class in class_node.base_classes:
                # Try to resolve base class
                base_node = self._resolve_class(base_class, class_node.file_path)
                if base_node:
                    edge = DependencyEdge(
                        source=class_node,
                        target=base_node,
                        dependency_type=DependencyType.INHERITANCE,
                        line_number=class_node.line_number,
                        file_path=class_node.file_path,
                        context=f"inherits from {base_class}"
                    )
                    dependency_edges.append(edge)
        
        return dependency_edges

    def _resolve_class(self, class_name: str, file_path: str) -> Optional[ClassNode]:
        """Resolve class name to class node."""
        # Check local classes first
        module_name = self.module_names[file_path]
        local_qualified = f"{module_name}.{class_name}"
        
        if local_qualified in self.classes:
            return self.classes[local_qualified]
        
        # Check imports
        file_imports = self.imports.get(file_path, {})
        if class_name in file_imports:
            imported_name = file_imports[class_name]
            if imported_name in self.classes:
                return self.classes[imported_name]
        
        return None
    
    def _find_entry_points(self) -> List[FunctionNode]:
        """Find entry point functions (main, __main__, etc.)."""
        entry_points = []
        
        for qualified_name, function_node in self.functions.items():
            if (function_node.name in ['main', '__main__'] or 
                qualified_name.endswith('.__main__') or
                'if __name__ == "__main__"' in self.file_contents.get(function_node.file_path, '')):
                entry_points.append(function_node)
        
        return entry_points
    
    def _find_unreachable_functions(self, entry_points: List[FunctionNode], call_edges: List[CallEdge]) -> List[FunctionNode]:
        """Find functions that are not reachable from entry points."""
        if not entry_points:
            return []
        
        reachable = set()
        
        def dfs(function_node):
            if function_node.qualified_name in reachable:
                return
            
            reachable.add(function_node.qualified_name)
            
            # Find all functions called by this function
            for edge in [e for e in call_edges if e.caller == function_node]:
                dfs(edge.callee)
        
        # Start DFS from all entry points
        for entry_point in entry_points:
            dfs(entry_point)
        
        # Find unreachable functions
        unreachable = []
        for qualified_name, function_node in self.functions.items():
            if qualified_name not in reachable:
                unreachable.append(function_node)
        
        return unreachable
    
    def _find_cyclic_dependencies(self, call_edges: List[CallEdge]) -> List[List[str]]:
        """Find cyclic dependencies in the call graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_name, path):
            if node_name in rec_stack:
                # Found a cycle
                cycle_start = path.index(node_name)
                cycle = path[cycle_start:] + [node_name]
                cycles.append(cycle)
                return
            
            if node_name in visited:
                return
            
            visited.add(node_name)
            rec_stack.add(node_name)
            path.append(node_name)
            
            # Find all functions called by this function
            if node_name in self.functions:
                function_node = self.functions[node_name]
                for edge in [e for e in call_edges if e.caller == function_node]:
                    dfs(edge.callee.qualified_name, path)
            
            path.pop()
            rec_stack.remove(node_name)
        
        # Check all functions
        for qualified_name in self.functions:
            if qualified_name not in visited:
                dfs(qualified_name, [])
        
        return cycles
    
    def get_function_callers(self, function_qualified_name: str) -> List[FunctionNode]:
        """Get all functions that call the given function."""
        callers = []
        target_function = self.functions.get(function_qualified_name)
        
        if target_function:
            # This method should be called after build_call_graph()
            result = getattr(self, '_last_result', None)
            if result:
                for edge in result.call_edges:
                    if edge.callee == target_function:
                        callers.append(edge.caller)
        
        return callers
    
    def get_function_callees(self, function_qualified_name: str) -> List[FunctionNode]:
        """Get all functions called by the given function."""
        callees = []
        source_function = self.functions.get(function_qualified_name)
        
        if source_function:
            # This method should be called after build_call_graph()
            result = getattr(self, '_last_result', None)
            if result:
                for edge in result.call_edges:
                    if edge.caller == source_function:
                        callees.append(edge.callee)
        
        return callees
    
    def get_call_chain(self, start_function: str, end_function: str) -> List[List[FunctionNode]]:
        """Find all call chains from start function to end function."""
        start_node = self.functions.get(start_function)
        end_node = self.functions.get(end_function)
        
        if not start_node or not end_node:
            return []
        
        chains = []
        
        def dfs(current_node, target_node, path, visited):
            if current_node == target_node:
                chains.append(path[:])
                return
            
            if current_node in visited:
                return
            
            visited.add(current_node)
            
            # Find all functions called by current function
            result = getattr(self, '_last_result', None)
            if result:
                for edge in [e for e in result.call_edges if e.caller == current_node]:
                    path.append(edge.callee)
                    dfs(edge.callee, target_node, path, visited)
                    path.pop()
            
            visited.remove(current_node)
        
        dfs(start_node, end_node, [start_node], set())
        return chains
