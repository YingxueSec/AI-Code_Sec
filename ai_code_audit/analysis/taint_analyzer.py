"""
Taint analysis system for AI Code Audit System.

This module provides comprehensive taint analysis including:
- Taint propagation tracking
- Source and sink identification
- Data flow path analysis
- Security vulnerability detection
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .semantic_analyzer import SemanticAnalyzer, Variable, DataFlow
from .call_graph import CallGraphBuilder, FunctionNode

logger = logging.getLogger(__name__)


class TaintType(Enum):
    """Types of taint."""
    USER_INPUT = "user_input"
    FILE_INPUT = "file_input"
    NETWORK_INPUT = "network_input"
    DATABASE_INPUT = "database_input"
    ENVIRONMENT_INPUT = "environment_input"
    COMMAND_INJECTION = "command_injection"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    DESERIALIZATION = "deserialization"


class TaintLevel(Enum):
    """Levels of taint severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CLEAN = "clean"


@dataclass
class TaintSource:
    """Represents a source of taint."""
    name: str
    taint_type: TaintType
    taint_level: TaintLevel
    file_path: str
    line_number: int
    function_patterns: List[str] = field(default_factory=list)
    variable_patterns: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaintSink:
    """Represents a sink that can be affected by taint."""
    name: str
    vulnerable_to: List[TaintType] = field(default_factory=list)
    severity: TaintLevel = TaintLevel.HIGH
    file_path: str = ""
    line_number: int = 0
    function_patterns: List[str] = field(default_factory=list)
    parameter_positions: List[int] = field(default_factory=list)  # Which parameters are vulnerable
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaintedVariable:
    """Represents a tainted variable."""
    variable: Variable
    taint_types: Set[TaintType] = field(default_factory=set)
    taint_level: TaintLevel = TaintLevel.MEDIUM
    source_location: Optional[Tuple[str, int]] = None  # (file_path, line_number)
    propagation_path: List[Tuple[str, int]] = field(default_factory=list)
    sanitized: bool = False
    sanitization_methods: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaintFlow:
    """Represents a taint flow from source to sink."""
    source: TaintSource
    sink: TaintSink
    tainted_variables: List[TaintedVariable] = field(default_factory=list)
    flow_path: List[Tuple[str, int, str]] = field(default_factory=list)  # (file, line, description)
    vulnerability_type: TaintType = TaintType.USER_INPUT
    severity: TaintLevel = TaintLevel.HIGH
    is_exploitable: bool = True
    sanitization_gaps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaintAnalysisResult:
    """Result of taint analysis."""
    file_path: str
    taint_sources: List[TaintSource] = field(default_factory=list)
    taint_sinks: List[TaintSink] = field(default_factory=list)
    tainted_variables: List[TaintedVariable] = field(default_factory=list)
    taint_flows: List[TaintFlow] = field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    sanitization_functions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaintAnalyzer:
    """Comprehensive taint analysis system."""
    
    def __init__(self, semantic_analyzer: SemanticAnalyzer, call_graph_builder: CallGraphBuilder):
        """Initialize taint analyzer."""
        self.semantic_analyzer = semantic_analyzer
        self.call_graph_builder = call_graph_builder
        
        # Initialize predefined sources and sinks
        self.predefined_sources = self._initialize_sources()
        self.predefined_sinks = self._initialize_sinks()
        self.sanitization_functions = self._initialize_sanitizers()
        
        # Analysis state
        self.tainted_variables: Dict[str, TaintedVariable] = {}
        self.analysis_results: Dict[str, TaintAnalysisResult] = {}
    
    def _initialize_sources(self) -> List[TaintSource]:
        """Initialize predefined taint sources."""
        sources = [
            # User input sources
            TaintSource(
                name="user_input",
                taint_type=TaintType.USER_INPUT,
                taint_level=TaintLevel.HIGH,
                file_path="",
                line_number=0,
                function_patterns=["input", "raw_input", "sys.stdin.read"],
                variable_patterns=["request.args", "request.form", "request.json", "request.data"],
                description="Direct user input from console or web requests"
            ),
            
            # File input sources
            TaintSource(
                name="file_input",
                taint_type=TaintType.FILE_INPUT,
                taint_level=TaintLevel.MEDIUM,
                file_path="",
                line_number=0,
                function_patterns=["open", "file", "read", "readlines"],
                variable_patterns=["sys.argv"],
                description="Input from files or command line arguments"
            ),
            
            # Network input sources
            TaintSource(
                name="network_input",
                taint_type=TaintType.NETWORK_INPUT,
                taint_level=TaintLevel.HIGH,
                file_path="",
                line_number=0,
                function_patterns=["requests.get", "requests.post", "urllib.request", "socket.recv"],
                description="Input from network requests"
            ),
            
            # Environment input sources
            TaintSource(
                name="environment_input",
                taint_type=TaintType.ENVIRONMENT_INPUT,
                taint_level=TaintLevel.MEDIUM,
                file_path="",
                line_number=0,
                function_patterns=["os.environ.get", "os.getenv"],
                variable_patterns=["os.environ"],
                description="Input from environment variables"
            ),
        ]
        
        return sources
    
    def _initialize_sinks(self) -> List[TaintSink]:
        """Initialize predefined taint sinks."""
        sinks = [
            # Command injection sinks
            TaintSink(
                name="command_execution",
                vulnerable_to=[TaintType.USER_INPUT, TaintType.FILE_INPUT],
                severity=TaintLevel.CRITICAL,
                function_patterns=["os.system", "subprocess.call", "subprocess.run", "subprocess.Popen"],
                parameter_positions=[0],
                description="Command execution functions vulnerable to injection"
            ),
            
            # SQL injection sinks
            TaintSink(
                name="sql_execution",
                vulnerable_to=[TaintType.USER_INPUT, TaintType.FILE_INPUT],
                severity=TaintLevel.CRITICAL,
                function_patterns=["execute", "cursor.execute", "query", "raw"],
                parameter_positions=[0],
                description="SQL execution functions vulnerable to injection"
            ),
            
            # Code execution sinks
            TaintSink(
                name="code_execution",
                vulnerable_to=[TaintType.USER_INPUT, TaintType.FILE_INPUT],
                severity=TaintLevel.CRITICAL,
                function_patterns=["eval", "exec", "compile"],
                parameter_positions=[0],
                description="Code execution functions"
            ),
            
            # File system sinks
            TaintSink(
                name="file_operations",
                vulnerable_to=[TaintType.USER_INPUT, TaintType.PATH_TRAVERSAL],
                severity=TaintLevel.HIGH,
                function_patterns=["open", "file", "remove", "unlink", "rmdir"],
                parameter_positions=[0],
                description="File system operations vulnerable to path traversal"
            ),
            
            # XSS sinks (for web applications)
            TaintSink(
                name="html_output",
                vulnerable_to=[TaintType.USER_INPUT, TaintType.XSS],
                severity=TaintLevel.HIGH,
                function_patterns=["render", "render_template", "HttpResponse"],
                parameter_positions=[0, 1],
                description="HTML output functions vulnerable to XSS"
            ),
        ]
        
        return sinks
    
    def _initialize_sanitizers(self) -> Set[str]:
        """Initialize sanitization functions."""
        return {
            # General sanitization
            "escape", "quote", "sanitize", "clean", "filter",
            
            # HTML sanitization
            "html.escape", "cgi.escape", "bleach.clean",
            
            # SQL sanitization
            "quote_identifier", "escape_string", "parameterize",
            
            # Path sanitization
            "os.path.normpath", "os.path.abspath", "pathlib.Path.resolve",
            
            # Command sanitization
            "shlex.quote", "pipes.quote",
        }
    
    def analyze_file(self, file_path: str) -> TaintAnalysisResult:
        """Perform taint analysis on a single file."""
        logger.info(f"Performing taint analysis on {file_path}")
        
        # Get semantic analysis
        if file_path not in self.semantic_analyzer.analysis_results:
            self.semantic_analyzer.analyze_file(file_path)
        
        semantic_result = self.semantic_analyzer.analysis_results[file_path]
        
        result = TaintAnalysisResult(file_path=file_path)
        
        # Phase 1: Identify sources and sinks in the file
        self._identify_sources_and_sinks(file_path, result)
        
        # Phase 2: Track taint propagation
        self._track_taint_propagation(file_path, semantic_result, result)
        
        # Phase 3: Identify taint flows
        self._identify_taint_flows(result)
        
        # Phase 4: Detect vulnerabilities
        self._detect_vulnerabilities(result)
        
        self.analysis_results[file_path] = result
        
        logger.info(f"Taint analysis complete: {len(result.taint_flows)} flows, "
                   f"{len(result.vulnerabilities)} vulnerabilities")
        
        return result
    
    def analyze_all_files(self) -> Dict[str, TaintAnalysisResult]:
        """Perform taint analysis on all files."""
        logger.info("Starting taint analysis of all files...")
        
        for file_path in self.semantic_analyzer.file_asts:
            try:
                self.analyze_file(file_path)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
        
        logger.info(f"Completed taint analysis of {len(self.analysis_results)} files")
        return self.analysis_results
    
    def _identify_sources_and_sinks(self, file_path: str, result: TaintAnalysisResult):
        """Identify taint sources and sinks in the file."""
        tree = self.semantic_analyzer.file_asts[file_path]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_call_for_sources_sinks(node, file_path, result)
            elif isinstance(node, ast.Attribute):
                self._check_attribute_for_sources_sinks(node, file_path, result)
    
    def _check_call_for_sources_sinks(self, call_node: ast.Call, file_path: str, result: TaintAnalysisResult):
        """Check if a function call is a source or sink."""
        func_name = ""
        
        if isinstance(call_node.func, ast.Name):
            func_name = call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                func_name = f"{call_node.func.value.id}.{call_node.func.attr}"
            else:
                func_name = call_node.func.attr
        
        # Check for sources
        for source_template in self.predefined_sources:
            for pattern in source_template.function_patterns:
                if pattern in func_name:
                    source = TaintSource(
                        name=func_name,
                        taint_type=source_template.taint_type,
                        taint_level=source_template.taint_level,
                        file_path=file_path,
                        line_number=call_node.lineno,
                        function_patterns=[func_name],
                        description=f"Taint source: {func_name}"
                    )
                    result.taint_sources.append(source)
                    break
        
        # Check for sinks
        for sink_template in self.predefined_sinks:
            for pattern in sink_template.function_patterns:
                if pattern in func_name:
                    sink = TaintSink(
                        name=func_name,
                        vulnerable_to=sink_template.vulnerable_to,
                        severity=sink_template.severity,
                        file_path=file_path,
                        line_number=call_node.lineno,
                        function_patterns=[func_name],
                        parameter_positions=sink_template.parameter_positions,
                        description=f"Taint sink: {func_name}"
                    )
                    result.taint_sinks.append(sink)
                    break
    
    def _check_attribute_for_sources_sinks(self, attr_node: ast.Attribute, file_path: str, result: TaintAnalysisResult):
        """Check if an attribute access is a source."""
        attr_name = ast.unparse(attr_node)
        
        # Check for sources
        for source_template in self.predefined_sources:
            for pattern in source_template.variable_patterns:
                if pattern in attr_name:
                    source = TaintSource(
                        name=attr_name,
                        taint_type=source_template.taint_type,
                        taint_level=source_template.taint_level,
                        file_path=file_path,
                        line_number=attr_node.lineno,
                        variable_patterns=[attr_name],
                        description=f"Taint source: {attr_name}"
                    )
                    result.taint_sources.append(source)
                    break
    
    def _track_taint_propagation(self, file_path: str, semantic_result, result: TaintAnalysisResult):
        """Track how taint propagates through variables."""
        # Initialize tainted variables from sources
        for source in result.taint_sources:
            # Find variables that receive taint from this source
            self._propagate_from_source(source, semantic_result, result)
        
        # Propagate taint through data flows
        changed = True
        iterations = 0
        max_iterations = 10  # Prevent infinite loops
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for flow in semantic_result.data_flows:
                if self._propagate_through_flow(flow, result):
                    changed = True
    
    def _propagate_from_source(self, source: TaintSource, semantic_result, result: TaintAnalysisResult):
        """Propagate taint from a source."""
        # Find variables assigned from this source
        tree = self.semantic_analyzer.file_asts[source.file_path]
        
        for node in ast.walk(tree):
            if (hasattr(node, 'lineno') and node.lineno == source.line_number and
                isinstance(node, ast.Assign)):
                
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Create tainted variable
                        var_key = f"{source.file_path}:global:{target.id}"
                        
                        # Find the variable in semantic analysis
                        for var_id, variable in semantic_result.variables.items():
                            if variable.name == target.id:
                                tainted_var = TaintedVariable(
                                    variable=variable,
                                    taint_types={source.taint_type},
                                    taint_level=source.taint_level,
                                    source_location=(source.file_path, source.line_number),
                                    propagation_path=[(source.file_path, source.line_number)]
                                )
                                
                                result.tainted_variables.append(tainted_var)
                                self.tainted_variables[var_key] = tainted_var
                                break
    
    def _propagate_through_flow(self, flow: DataFlow, result: TaintAnalysisResult) -> bool:
        """Propagate taint through a data flow."""
        source_key = f"{flow.source.file_path}:{flow.source.scope}:{flow.source.name}"
        target_key = f"{flow.target.file_path}:{flow.target.scope}:{flow.target.name}"
        
        # Check if source is tainted
        if source_key in self.tainted_variables:
            source_taint = self.tainted_variables[source_key]
            
            # Check if target is already tainted
            if target_key not in self.tainted_variables:
                # Propagate taint to target
                target_taint = TaintedVariable(
                    variable=flow.target,
                    taint_types=source_taint.taint_types.copy(),
                    taint_level=source_taint.taint_level,
                    source_location=source_taint.source_location,
                    propagation_path=source_taint.propagation_path + [(flow.file_path, flow.location[0])]
                )
                
                # Check for sanitization
                if self._is_sanitized(flow):
                    target_taint.sanitized = True
                    target_taint.sanitization_methods = self._get_sanitization_methods(flow)
                    target_taint.taint_level = TaintLevel.LOW
                
                result.tainted_variables.append(target_taint)
                self.tainted_variables[target_key] = target_taint
                return True
        
        return False
    
    def _is_sanitized(self, flow: DataFlow) -> bool:
        """Check if a data flow includes sanitization."""
        # Check if the flow goes through a sanitization function
        if flow.context:
            for sanitizer in self.sanitization_functions:
                if sanitizer in flow.context:
                    return True
        
        return False
    
    def _get_sanitization_methods(self, flow: DataFlow) -> List[str]:
        """Get sanitization methods used in a flow."""
        methods = []
        
        if flow.context:
            for sanitizer in self.sanitization_functions:
                if sanitizer in flow.context:
                    methods.append(sanitizer)
        
        return methods
    
    def _identify_taint_flows(self, result: TaintAnalysisResult):
        """Identify complete taint flows from sources to sinks."""
        for sink in result.taint_sinks:
            for tainted_var in result.tainted_variables:
                # Check if tainted variable can reach this sink
                if self._can_reach_sink(tainted_var, sink, result):
                    # Find the original source
                    source = self._find_source_for_variable(tainted_var, result)
                    
                    if source:
                        flow = TaintFlow(
                            source=source,
                            sink=sink,
                            tainted_variables=[tainted_var],
                            flow_path=tainted_var.propagation_path,
                            vulnerability_type=list(tainted_var.taint_types)[0],
                            severity=self._calculate_flow_severity(tainted_var, sink),
                            is_exploitable=not tainted_var.sanitized
                        )
                        
                        if tainted_var.sanitized:
                            flow.sanitization_gaps = self._analyze_sanitization_gaps(tainted_var, sink)
                        
                        result.taint_flows.append(flow)
    
    def _can_reach_sink(self, tainted_var: TaintedVariable, sink: TaintSink, result: TaintAnalysisResult) -> bool:
        """Check if a tainted variable can reach a sink."""
        # Simplified reachability check
        # In practice, this would involve more sophisticated analysis
        
        # Check if the variable is used in the same file as the sink
        if tainted_var.variable.file_path == sink.file_path:
            # Check if any of the taint types match the sink's vulnerabilities
            return bool(tainted_var.taint_types.intersection(set(sink.vulnerable_to)))
        
        return False
    
    def _find_source_for_variable(self, tainted_var: TaintedVariable, result: TaintAnalysisResult) -> Optional[TaintSource]:
        """Find the original source for a tainted variable."""
        if tainted_var.source_location:
            file_path, line_number = tainted_var.source_location
            
            for source in result.taint_sources:
                if source.file_path == file_path and source.line_number == line_number:
                    return source
        
        return None
    
    def _calculate_flow_severity(self, tainted_var: TaintedVariable, sink: TaintSink) -> TaintLevel:
        """Calculate the severity of a taint flow."""
        # Use the maximum severity between variable taint level and sink severity
        severity_order = [TaintLevel.CLEAN, TaintLevel.LOW, TaintLevel.MEDIUM, TaintLevel.HIGH, TaintLevel.CRITICAL]
        
        var_index = severity_order.index(tainted_var.taint_level)
        sink_index = severity_order.index(sink.severity)
        
        max_index = max(var_index, sink_index)
        return severity_order[max_index]
    
    def _analyze_sanitization_gaps(self, tainted_var: TaintedVariable, sink: TaintSink) -> List[str]:
        """Analyze gaps in sanitization."""
        gaps = []
        
        # Check if sanitization is appropriate for the sink type
        if tainted_var.sanitized:
            for taint_type in tainted_var.taint_types:
                if taint_type in sink.vulnerable_to:
                    # Check if sanitization methods are appropriate
                    appropriate_sanitizers = self._get_appropriate_sanitizers(taint_type)
                    
                    if not any(method in appropriate_sanitizers for method in tainted_var.sanitization_methods):
                        gaps.append(f"Inappropriate sanitization for {taint_type.value}")
        
        return gaps
    
    def _get_appropriate_sanitizers(self, taint_type: TaintType) -> Set[str]:
        """Get appropriate sanitizers for a taint type."""
        sanitizer_map = {
            TaintType.USER_INPUT: {"escape", "quote", "sanitize"},
            TaintType.SQL_INJECTION: {"quote_identifier", "escape_string", "parameterize"},
            TaintType.XSS: {"html.escape", "cgi.escape", "bleach.clean"},
            TaintType.COMMAND_INJECTION: {"shlex.quote", "pipes.quote"},
            TaintType.PATH_TRAVERSAL: {"os.path.normpath", "os.path.abspath"},
        }
        
        return sanitizer_map.get(taint_type, set())
    
    def _detect_vulnerabilities(self, result: TaintAnalysisResult):
        """Detect vulnerabilities from taint flows."""
        for flow in result.taint_flows:
            if flow.is_exploitable:
                vulnerability = {
                    "type": flow.vulnerability_type.value,
                    "severity": flow.severity.value,
                    "source": {
                        "file": flow.source.file_path,
                        "line": flow.source.line_number,
                        "description": flow.source.description
                    },
                    "sink": {
                        "file": flow.sink.file_path,
                        "line": flow.sink.line_number,
                        "description": flow.sink.description
                    },
                    "flow_path": flow.flow_path,
                    "exploitable": flow.is_exploitable,
                    "sanitization_gaps": flow.sanitization_gaps,
                    "recommendation": self._get_vulnerability_recommendation(flow)
                }
                
                result.vulnerabilities.append(vulnerability)
    
    def _get_vulnerability_recommendation(self, flow: TaintFlow) -> str:
        """Get recommendation for fixing a vulnerability."""
        recommendations = {
            TaintType.SQL_INJECTION: "Use parameterized queries or prepared statements",
            TaintType.COMMAND_INJECTION: "Use subprocess with shell=False and validate inputs",
            TaintType.XSS: "Escape HTML output and validate user inputs",
            TaintType.PATH_TRAVERSAL: "Validate and sanitize file paths, use os.path.normpath",
            TaintType.USER_INPUT: "Validate and sanitize all user inputs"
        }
        
        return recommendations.get(flow.vulnerability_type, "Validate and sanitize inputs")
    
    def get_vulnerability_summary(self) -> Dict[str, Any]:
        """Get summary of all vulnerabilities found."""
        all_vulnerabilities = []
        
        for result in self.analysis_results.values():
            all_vulnerabilities.extend(result.vulnerabilities)
        
        # Group by type and severity
        by_type = {}
        by_severity = {}
        
        for vuln in all_vulnerabilities:
            vuln_type = vuln["type"]
            severity = vuln["severity"]
            
            by_type[vuln_type] = by_type.get(vuln_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_vulnerabilities": len(all_vulnerabilities),
            "by_type": by_type,
            "by_severity": by_severity,
            "files_analyzed": len(self.analysis_results),
            "exploitable_count": len([v for v in all_vulnerabilities if v["exploitable"]])
        }
