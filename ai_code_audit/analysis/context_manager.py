"""
Intelligent context management for AI Code Audit System.

This module provides advanced context management capabilities including:
- Code snippet extraction and optimization
- Dependency relationship analysis
- Minimal sufficient set construction
- Context window optimization for LLMs
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from ..core.models import FileInfo, ProjectInfo
from .code_retrieval import CodeRetriever, RetrievalQuery, RetrievalType

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of code context."""
    FUNCTION_CONTEXT = "function_context"
    CLASS_CONTEXT = "class_context"
    MODULE_CONTEXT = "module_context"
    DEPENDENCY_CONTEXT = "dependency_context"
    SECURITY_CONTEXT = "security_context"
    MINIMAL_CONTEXT = "minimal_context"


class ContextPriority(Enum):
    """Priority levels for context inclusion."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class CodeSnippet:
    """A code snippet with metadata."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    context_type: ContextType
    priority: ContextPriority = ContextPriority.MEDIUM
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def line_count(self) -> int:
        """Get number of lines in snippet."""
        return self.end_line - self.start_line + 1
    
    @property
    def token_estimate(self) -> int:
        """Estimate token count (rough approximation)."""
        return len(self.content.split()) * 1.3  # Rough token estimation


@dataclass
class CodeContext:
    """Complete code context for analysis."""
    target_file: str
    target_function: Optional[str] = None
    target_class: Optional[str] = None
    snippets: List[CodeSnippet] = field(default_factory=list)
    total_tokens: int = 0
    context_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_snippet(self, snippet: CodeSnippet):
        """Add a code snippet to context."""
        self.snippets.append(snippet)
        self.total_tokens += snippet.token_estimate
    
    def get_snippets_by_priority(self, max_priority: ContextPriority) -> List[CodeSnippet]:
        """Get snippets up to a certain priority level."""
        return [s for s in self.snippets if s.priority.value <= max_priority.value]
    
    def optimize_for_token_limit(self, max_tokens: int) -> 'CodeContext':
        """Optimize context to fit within token limit."""
        # Sort by priority (lower number = higher priority)
        sorted_snippets = sorted(self.snippets, key=lambda x: x.priority.value)
        
        optimized_context = CodeContext(
            target_file=self.target_file,
            target_function=self.target_function,
            target_class=self.target_class,
            context_summary=self.context_summary,
            metadata=self.metadata.copy()
        )
        
        current_tokens = 0
        for snippet in sorted_snippets:
            if current_tokens + snippet.token_estimate <= max_tokens:
                optimized_context.add_snippet(snippet)
                current_tokens += snippet.token_estimate
            else:
                break
        
        return optimized_context


class ContextManager:
    """Intelligent context management system."""
    
    def __init__(self, project_info: ProjectInfo, code_retriever: Optional[CodeRetriever] = None):
        """Initialize context manager."""
        self.project_info = project_info
        self.code_retriever = code_retriever or CodeRetriever(project_info)
        self.file_contents: Dict[str, str] = {}
        self.ast_cache: Dict[str, ast.AST] = {}
        
        # Load file contents
        self._load_file_contents()
    
    def _load_file_contents(self):
        """Load file contents for context extraction."""
        for file_info in self.project_info.files:
            if file_info.language in ['python', 'javascript', 'java', 'go']:
                try:
                    file_path = Path(file_info.absolute_path)
                    if file_path.exists():
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        self.file_contents[file_info.path] = content
                        
                        # Parse Python files for AST
                        if file_info.language == 'python':
                            try:
                                tree = ast.parse(content)
                                self.ast_cache[file_info.path] = tree
                            except SyntaxError:
                                logger.warning(f"Syntax error in {file_info.path}")
                                
                except Exception as e:
                    logger.warning(f"Failed to load {file_info.path}: {e}")
    
    async def build_context(
        self,
        target_file: str,
        target_function: Optional[str] = None,
        target_class: Optional[str] = None,
        context_types: Optional[List[ContextType]] = None,
        max_tokens: Optional[int] = None
    ) -> CodeContext:
        """Build comprehensive code context for analysis."""
        if context_types is None:
            context_types = [
                ContextType.FUNCTION_CONTEXT,
                ContextType.DEPENDENCY_CONTEXT,
                ContextType.SECURITY_CONTEXT
            ]
        
        context = CodeContext(
            target_file=target_file,
            target_function=target_function,
            target_class=target_class
        )
        
        # Build different types of context
        for context_type in context_types:
            snippets = await self._extract_context_snippets(
                target_file, target_function, target_class, context_type
            )
            for snippet in snippets:
                context.add_snippet(snippet)
        
        # Generate context summary
        context.context_summary = self._generate_context_summary(context)
        
        # Optimize for token limit if specified
        if max_tokens:
            context = context.optimize_for_token_limit(max_tokens)
        
        logger.info(f"Built context with {len(context.snippets)} snippets, {context.total_tokens} tokens")
        return context
    
    async def _extract_context_snippets(
        self,
        target_file: str,
        target_function: Optional[str],
        target_class: Optional[str],
        context_type: ContextType
    ) -> List[CodeSnippet]:
        """Extract context snippets based on type."""
        snippets = []
        
        if context_type == ContextType.FUNCTION_CONTEXT:
            snippets.extend(await self._extract_function_context(target_file, target_function))
        elif context_type == ContextType.CLASS_CONTEXT:
            snippets.extend(await self._extract_class_context(target_file, target_class))
        elif context_type == ContextType.MODULE_CONTEXT:
            snippets.extend(await self._extract_module_context(target_file))
        elif context_type == ContextType.DEPENDENCY_CONTEXT:
            snippets.extend(await self._extract_dependency_context(target_file))
        elif context_type == ContextType.SECURITY_CONTEXT:
            snippets.extend(await self._extract_security_context(target_file))
        elif context_type == ContextType.MINIMAL_CONTEXT:
            snippets.extend(await self._extract_minimal_context(target_file, target_function))
        
        return snippets
    
    async def _extract_function_context(self, target_file: str, target_function: Optional[str]) -> List[CodeSnippet]:
        """Extract function-level context."""
        snippets = []
        
        if not target_function:
            return snippets
        
        # Find function definition
        query = RetrievalQuery(
            query_type=RetrievalType.FUNCTION_DEFINITION,
            target=target_function,
            file_filter=[target_file],
            include_context=True,
            context_lines=10
        )
        
        result = await self.code_retriever.retrieve(query)
        
        for match in result.matches:
            snippet = CodeSnippet(
                file_path=match.file_path,
                start_line=max(1, match.line_number - 5),
                end_line=match.line_number + len(match.context_after) + 5,
                content=self._extract_lines(
                    match.file_path,
                    max(1, match.line_number - 5),
                    match.line_number + len(match.context_after) + 5
                ),
                context_type=ContextType.FUNCTION_CONTEXT,
                priority=ContextPriority.CRITICAL,
                metadata={'function_name': target_function}
            )
            snippets.append(snippet)
        
        # Find function calls
        call_query = RetrievalQuery(
            query_type=RetrievalType.CALL_GRAPH,
            target=target_function,
            max_results=10,
            include_context=True,
            context_lines=3
        )
        
        call_result = await self.code_retriever.retrieve(call_query)
        
        for match in call_result.matches:
            snippet = CodeSnippet(
                file_path=match.file_path,
                start_line=max(1, match.line_number - 3),
                end_line=match.line_number + 3,
                content=self._extract_lines(
                    match.file_path,
                    max(1, match.line_number - 3),
                    match.line_number + 3
                ),
                context_type=ContextType.FUNCTION_CONTEXT,
                priority=ContextPriority.HIGH,
                metadata={'call_site': True, 'function_name': target_function}
            )
            snippets.append(snippet)
        
        return snippets
    
    async def _extract_class_context(self, target_file: str, target_class: Optional[str]) -> List[CodeSnippet]:
        """Extract class-level context."""
        snippets = []
        
        if not target_class:
            return snippets
        
        query = RetrievalQuery(
            query_type=RetrievalType.CLASS_DEFINITION,
            target=target_class,
            file_filter=[target_file],
            include_context=True,
            context_lines=5
        )
        
        result = await self.code_retriever.retrieve(query)
        
        for match in result.matches:
            # Extract class definition and methods
            if target_file in self.ast_cache:
                class_snippet = self._extract_class_from_ast(target_file, target_class)
                if class_snippet:
                    snippets.append(class_snippet)
            else:
                # Fallback to simple extraction
                snippet = CodeSnippet(
                    file_path=match.file_path,
                    start_line=match.line_number,
                    end_line=match.line_number + 50,  # Estimate class size
                    content=self._extract_lines(match.file_path, match.line_number, match.line_number + 50),
                    context_type=ContextType.CLASS_CONTEXT,
                    priority=ContextPriority.CRITICAL,
                    metadata={'class_name': target_class}
                )
                snippets.append(snippet)
        
        return snippets
    
    async def _extract_module_context(self, target_file: str) -> List[CodeSnippet]:
        """Extract module-level context (imports, globals, etc.)."""
        snippets = []
        
        if target_file not in self.file_contents:
            return snippets
        
        content = self.file_contents[target_file]
        lines = content.split('\n')
        
        # Extract imports (first 50 lines typically)
        import_end = min(50, len(lines))
        for i in range(import_end):
            line = lines[i].strip()
            if line.startswith(('import ', 'from ')) or line.startswith('#'):
                continue
            elif line and not line.startswith(('def ', 'class ', '@')):
                # Found non-import code, stop here
                import_end = i
                break
        
        if import_end > 0:
            snippet = CodeSnippet(
                file_path=target_file,
                start_line=1,
                end_line=import_end,
                content='\n'.join(lines[:import_end]),
                context_type=ContextType.MODULE_CONTEXT,
                priority=ContextPriority.HIGH,
                metadata={'section': 'imports_and_globals'}
            )
            snippets.append(snippet)
        
        return snippets
    
    async def _extract_dependency_context(self, target_file: str) -> List[CodeSnippet]:
        """Extract dependency context from related files."""
        snippets = []
        
        # Find imports in target file
        if target_file in self.file_contents:
            content = self.file_contents[target_file]
            
            # Extract import statements
            import_query = RetrievalQuery(
                query_type=RetrievalType.IMPORT_CHAIN,
                target="",  # Will be filled per import
                file_filter=[target_file],
                max_results=20
            )
            
            # Simple regex-based import extraction
            import re
            import_pattern = r'from\s+(\S+)\s+import|import\s+(\S+)'
            
            for match in re.finditer(import_pattern, content):
                module_name = match.group(1) or match.group(2)
                if module_name and not module_name.startswith('.'):
                    # Look for this module in project files
                    for file_info in self.project_info.files:
                        if module_name.replace('.', '/') in file_info.path:
                            snippet = CodeSnippet(
                                file_path=file_info.path,
                                start_line=1,
                                end_line=min(100, len(self.file_contents.get(file_info.path, '').split('\n'))),
                                content=self._extract_lines(file_info.path, 1, 100),
                                context_type=ContextType.DEPENDENCY_CONTEXT,
                                priority=ContextPriority.MEDIUM,
                                metadata={'imported_module': module_name}
                            )
                            snippets.append(snippet)
                            break
        
        return snippets
    
    async def _extract_security_context(self, target_file: str) -> List[CodeSnippet]:
        """Extract security-relevant context."""
        snippets = []
        
        # Security patterns to look for
        security_patterns = [
            'sql_injection',
            'xss',
            'path_traversal',
            'hardcoded_secrets'
        ]
        
        for pattern in security_patterns:
            query = RetrievalQuery(
                query_type=RetrievalType.SECURITY_PATTERN,
                target=pattern,
                file_filter=[target_file],
                include_context=True,
                context_lines=5,
                max_results=5
            )
            
            result = await self.code_retriever.retrieve(query)
            
            for match in result.matches:
                snippet = CodeSnippet(
                    file_path=match.file_path,
                    start_line=max(1, match.line_number - 5),
                    end_line=match.line_number + 5,
                    content=self._extract_lines(
                        match.file_path,
                        max(1, match.line_number - 5),
                        match.line_number + 5
                    ),
                    context_type=ContextType.SECURITY_CONTEXT,
                    priority=ContextPriority.CRITICAL,
                    metadata={'security_pattern': pattern}
                )
                snippets.append(snippet)
        
        return snippets
    
    async def _extract_minimal_context(self, target_file: str, target_function: Optional[str]) -> List[CodeSnippet]:
        """Extract minimal sufficient context for analysis."""
        snippets = []
        
        # This would implement a more sophisticated algorithm to find
        # the minimal set of code needed to understand the target
        # For now, just return the target function
        
        if target_function:
            function_snippets = await self._extract_function_context(target_file, target_function)
            # Take only the function definition, not calls
            for snippet in function_snippets:
                if snippet.metadata.get('function_name') == target_function and not snippet.metadata.get('call_site'):
                    snippet.context_type = ContextType.MINIMAL_CONTEXT
                    snippet.priority = ContextPriority.CRITICAL
                    snippets.append(snippet)
                    break
        
        return snippets
    
    def _extract_lines(self, file_path: str, start_line: int, end_line: int) -> str:
        """Extract lines from file."""
        if file_path not in self.file_contents:
            return ""
        
        lines = self.file_contents[file_path].split('\n')
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        return '\n'.join(lines[start_idx:end_idx])
    
    def _extract_class_from_ast(self, file_path: str, class_name: str) -> Optional[CodeSnippet]:
        """Extract class definition using AST."""
        if file_path not in self.ast_cache:
            return None
        
        tree = self.ast_cache[file_path]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # Calculate class end line (approximate)
                end_line = node.lineno + 50  # Rough estimate
                
                content = self._extract_lines(file_path, node.lineno, end_line)
                
                return CodeSnippet(
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=end_line,
                    content=content,
                    context_type=ContextType.CLASS_CONTEXT,
                    priority=ContextPriority.CRITICAL,
                    metadata={'class_name': class_name, 'extracted_from_ast': True}
                )
        
        return None
    
    def _generate_context_summary(self, context: CodeContext) -> str:
        """Generate a summary of the context."""
        summary_parts = []
        
        summary_parts.append(f"Target file: {context.target_file}")
        
        if context.target_function:
            summary_parts.append(f"Target function: {context.target_function}")
        
        if context.target_class:
            summary_parts.append(f"Target class: {context.target_class}")
        
        # Count snippets by type
        type_counts = {}
        for snippet in context.snippets:
            context_type = snippet.context_type.value
            type_counts[context_type] = type_counts.get(context_type, 0) + 1
        
        if type_counts:
            summary_parts.append("Context includes:")
            for context_type, count in type_counts.items():
                summary_parts.append(f"  - {count} {context_type} snippet(s)")
        
        summary_parts.append(f"Total tokens: {context.total_tokens}")
        
        return '\n'.join(summary_parts)
