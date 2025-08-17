"""
Intelligent code retrieval system for AI Code Audit System.

This module provides advanced code retrieval capabilities including:
- Semantic-based code search
- Call graph analysis
- Cross-file dependency tracking
- Code slicing and context extraction
"""

import ast
import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from ..core.models import FileInfo, ProjectInfo

logger = logging.getLogger(__name__)


class RetrievalType(Enum):
    """Types of code retrieval queries."""
    FUNCTION_DEFINITION = "function_definition"
    CLASS_DEFINITION = "class_definition"
    VARIABLE_USAGE = "variable_usage"
    IMPORT_CHAIN = "import_chain"
    CALL_GRAPH = "call_graph"
    DATA_FLOW = "data_flow"
    SECURITY_PATTERN = "security_pattern"


class MatchConfidence(Enum):
    """Confidence levels for retrieval matches."""
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RetrievalQuery:
    """Query for code retrieval."""
    query_type: RetrievalType
    target: str  # Function name, class name, variable name, etc.
    context: Optional[str] = None  # Additional context
    file_filter: Optional[List[str]] = None  # Limit search to specific files
    language_filter: Optional[List[str]] = None  # Limit to specific languages
    max_results: int = 50
    include_context: bool = True  # Include surrounding code context
    context_lines: int = 5  # Lines of context to include


@dataclass
class CodeMatch:
    """A single code match result."""
    file_path: str
    line_number: int
    column_number: int
    match_text: str
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    confidence: MatchConfidence = MatchConfidence.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Result of a code retrieval query."""
    query: RetrievalQuery
    matches: List[CodeMatch] = field(default_factory=list)
    total_matches: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_matches(self) -> bool:
        """Check if any matches were found."""
        return len(self.matches) > 0
    
    @property
    def high_confidence_matches(self) -> List[CodeMatch]:
        """Get only high confidence matches."""
        return [m for m in self.matches if m.confidence in [MatchConfidence.EXACT, MatchConfidence.HIGH]]


class CodeRetriever:
    """Intelligent code retrieval system."""
    
    def __init__(self, project_info: ProjectInfo):
        """Initialize code retriever with project information."""
        self.project_info = project_info
        self.file_contents: Dict[str, str] = {}
        self.ast_cache: Dict[str, ast.AST] = {}
        self.symbol_index: Dict[str, List[CodeMatch]] = {}
        
        # Initialize retrieval
        self._build_indices()
    
    def _build_indices(self):
        """Build search indices for fast retrieval."""
        logger.info("Building code retrieval indices...")
        
        for file_info in self.project_info.files:
            if not file_info.language or file_info.language not in ['python', 'javascript', 'java', 'go']:
                continue
            
            try:
                # Load file content
                file_path = Path(file_info.absolute_path)
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    self.file_contents[file_info.path] = content
                    
                    # Build language-specific indices
                    if file_info.language == 'python':
                        self._index_python_file(file_info.path, content)
                    elif file_info.language == 'javascript':
                        self._index_javascript_file(file_info.path, content)
                    
            except Exception as e:
                logger.warning(f"Failed to index file {file_info.path}: {e}")
        
        logger.info(f"Indexed {len(self.file_contents)} files with {len(self.symbol_index)} symbols")
    
    def _index_python_file(self, file_path: str, content: str):
        """Index Python file for retrieval."""
        try:
            tree = ast.parse(content)
            self.ast_cache[file_path] = tree
            
            # Extract symbols
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._add_symbol_match(
                        'function', node.name, file_path, 
                        node.lineno, node.col_offset, content
                    )
                elif isinstance(node, ast.ClassDef):
                    self._add_symbol_match(
                        'class', node.name, file_path,
                        node.lineno, node.col_offset, content
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_symbol_match(
                            'import', alias.name, file_path,
                            node.lineno, node.col_offset, content
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_symbol_match(
                            'import', node.module, file_path,
                            node.lineno, node.col_offset, content
                        )
                        
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
    
    def _index_javascript_file(self, file_path: str, content: str):
        """Index JavaScript file for retrieval (basic regex-based)."""
        lines = content.split('\n')
        
        # Function definitions
        func_pattern = r'function\s+(\w+)\s*\('
        for i, line in enumerate(lines):
            matches = re.finditer(func_pattern, line)
            for match in matches:
                self._add_symbol_match(
                    'function', match.group(1), file_path,
                    i + 1, match.start(), content
                )
        
        # Class definitions
        class_pattern = r'class\s+(\w+)\s*[{]'
        for i, line in enumerate(lines):
            matches = re.finditer(class_pattern, line)
            for match in matches:
                self._add_symbol_match(
                    'class', match.group(1), file_path,
                    i + 1, match.start(), content
                )
        
        # Import statements
        import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
        for i, line in enumerate(lines):
            matches = re.finditer(import_pattern, line)
            for match in matches:
                self._add_symbol_match(
                    'import', match.group(1), file_path,
                    i + 1, match.start(), content
                )
    
    def _add_symbol_match(self, symbol_type: str, symbol_name: str, file_path: str, 
                         line_no: int, col_no: int, content: str):
        """Add a symbol match to the index."""
        lines = content.split('\n')
        
        # Get context
        context_before = []
        context_after = []
        
        start_line = max(0, line_no - 6)  # 5 lines before + current line
        end_line = min(len(lines), line_no + 5)  # 5 lines after
        
        if line_no > 0:
            context_before = lines[start_line:line_no-1]
            match_text = lines[line_no-1] if line_no <= len(lines) else ""
            context_after = lines[line_no:end_line]
        else:
            match_text = ""
        
        match = CodeMatch(
            file_path=file_path,
            line_number=line_no,
            column_number=col_no,
            match_text=match_text,
            context_before=context_before,
            context_after=context_after,
            confidence=MatchConfidence.HIGH,
            metadata={'symbol_type': symbol_type, 'symbol_name': symbol_name}
        )
        
        # Add to index
        key = f"{symbol_type}:{symbol_name}"
        if key not in self.symbol_index:
            self.symbol_index[key] = []
        self.symbol_index[key].append(match)
    
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """Perform code retrieval based on query."""
        import time
        start_time = time.time()
        
        result = RetrievalResult(query=query)
        
        try:
            if query.query_type == RetrievalType.FUNCTION_DEFINITION:
                result.matches = self._find_function_definitions(query)
            elif query.query_type == RetrievalType.CLASS_DEFINITION:
                result.matches = self._find_class_definitions(query)
            elif query.query_type == RetrievalType.VARIABLE_USAGE:
                result.matches = self._find_variable_usage(query)
            elif query.query_type == RetrievalType.IMPORT_CHAIN:
                result.matches = self._find_import_chain(query)
            elif query.query_type == RetrievalType.CALL_GRAPH:
                result.matches = self._find_call_graph(query)
            elif query.query_type == RetrievalType.SECURITY_PATTERN:
                result.matches = self._find_security_patterns(query)
            else:
                logger.warning(f"Unsupported query type: {query.query_type}")
            
            # Apply filters
            result.matches = self._apply_filters(result.matches, query)
            
            # Limit results
            if len(result.matches) > query.max_results:
                result.matches = result.matches[:query.max_results]
            
            result.total_matches = len(result.matches)
            result.execution_time = time.time() - start_time
            
            logger.info(f"Retrieved {result.total_matches} matches for {query.query_type.value} query")
            
        except Exception as e:
            logger.error(f"Error during code retrieval: {e}")
            result.metadata['error'] = str(e)
        
        return result
    
    def _find_function_definitions(self, query: RetrievalQuery) -> List[CodeMatch]:
        """Find function definitions."""
        key = f"function:{query.target}"
        return self.symbol_index.get(key, [])
    
    def _find_class_definitions(self, query: RetrievalQuery) -> List[CodeMatch]:
        """Find class definitions."""
        key = f"class:{query.target}"
        return self.symbol_index.get(key, [])
    
    def _find_variable_usage(self, query: RetrievalQuery) -> List[CodeMatch]:
        """Find variable usage across files."""
        matches = []
        
        for file_path, content in self.file_contents.items():
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # Simple regex-based variable search
                pattern = r'\b' + re.escape(query.target) + r'\b'
                for match in re.finditer(pattern, line):
                    code_match = CodeMatch(
                        file_path=file_path,
                        line_number=i + 1,
                        column_number=match.start(),
                        match_text=line,
                        confidence=MatchConfidence.MEDIUM,
                        metadata={'variable_name': query.target}
                    )
                    
                    # Add context if requested
                    if query.include_context:
                        start_line = max(0, i - query.context_lines)
                        end_line = min(len(lines), i + query.context_lines + 1)
                        code_match.context_before = lines[start_line:i]
                        code_match.context_after = lines[i+1:end_line]
                    
                    matches.append(code_match)
        
        return matches
    
    def _find_import_chain(self, query: RetrievalQuery) -> List[CodeMatch]:
        """Find import chains and dependencies."""
        key = f"import:{query.target}"
        return self.symbol_index.get(key, [])
    
    def _find_call_graph(self, query: RetrievalQuery) -> List[CodeMatch]:
        """Find function calls and build call graph."""
        matches = []
        
        # Look for function calls
        call_pattern = r'\b' + re.escape(query.target) + r'\s*\('
        
        for file_path, content in self.file_contents.items():
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                for match in re.finditer(call_pattern, line):
                    code_match = CodeMatch(
                        file_path=file_path,
                        line_number=i + 1,
                        column_number=match.start(),
                        match_text=line,
                        confidence=MatchConfidence.HIGH,
                        metadata={'call_type': 'function_call', 'function_name': query.target}
                    )
                    
                    if query.include_context:
                        start_line = max(0, i - query.context_lines)
                        end_line = min(len(lines), i + query.context_lines + 1)
                        code_match.context_before = lines[start_line:i]
                        code_match.context_after = lines[i+1:end_line]
                    
                    matches.append(code_match)
        
        return matches
    
    def _find_security_patterns(self, query: RetrievalQuery) -> List[CodeMatch]:
        """Find security-related patterns."""
        matches = []
        
        # Define security patterns
        security_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*\+.*["\']',
                r'query\s*\(\s*["\'].*\+.*["\']',
                r'SELECT.*\+.*FROM',
            ],
            'xss': [
                r'innerHTML\s*=.*\+',
                r'document\.write\s*\(.*\+',
                r'eval\s*\(',
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'os\.path\.join.*\.\.',
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
            ]
        }
        
        patterns = security_patterns.get(query.target, [query.target])
        
        for file_path, content in self.file_contents.items():
            lines = content.split('\n')
            
            for pattern in patterns:
                for i, line in enumerate(lines):
                    for match in re.finditer(pattern, line, re.IGNORECASE):
                        code_match = CodeMatch(
                            file_path=file_path,
                            line_number=i + 1,
                            column_number=match.start(),
                            match_text=line,
                            confidence=MatchConfidence.HIGH,
                            metadata={
                                'security_pattern': query.target,
                                'pattern_matched': pattern
                            }
                        )
                        
                        if query.include_context:
                            start_line = max(0, i - query.context_lines)
                            end_line = min(len(lines), i + query.context_lines + 1)
                            code_match.context_before = lines[start_line:i]
                            code_match.context_after = lines[i+1:end_line]
                        
                        matches.append(code_match)
        
        return matches
    
    def _apply_filters(self, matches: List[CodeMatch], query: RetrievalQuery) -> List[CodeMatch]:
        """Apply query filters to matches."""
        filtered_matches = matches
        
        # File filter
        if query.file_filter:
            filtered_matches = [
                m for m in filtered_matches 
                if any(file_pattern in m.file_path for file_pattern in query.file_filter)
            ]
        
        # Language filter (basic implementation)
        if query.language_filter:
            filtered_matches = [
                m for m in filtered_matches
                if any(lang in m.file_path.lower() for lang in query.language_filter)
            ]
        
        # Sort by confidence and line number
        filtered_matches.sort(key=lambda x: (x.confidence.value, x.file_path, x.line_number))
        
        return filtered_matches
    
    def get_symbol_statistics(self) -> Dict[str, int]:
        """Get statistics about indexed symbols."""
        stats = {}
        
        for key in self.symbol_index:
            symbol_type = key.split(':')[0]
            if symbol_type not in stats:
                stats[symbol_type] = 0
            stats[symbol_type] += len(self.symbol_index[key])
        
        return stats
