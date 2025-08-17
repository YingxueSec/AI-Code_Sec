"""
Code consistency checker for AI Code Audit System.

This module provides comprehensive consistency checking including:
- Code snippet vs file content verification
- Context accuracy validation
- Semantic consistency checking
- Cross-reference validation
"""

import difflib
import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConsistencyType(Enum):
    """Types of consistency checks."""
    EXACT_MATCH = "exact_match"
    SEMANTIC_MATCH = "semantic_match"
    PARTIAL_MATCH = "partial_match"
    CONTEXT_MATCH = "context_match"
    STRUCTURE_MATCH = "structure_match"


class ConsistencyLevel(Enum):
    """Consistency check levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class ConsistencyIssue:
    """Individual consistency issue."""
    issue_type: ConsistencyType
    severity: str  # critical, high, medium, low
    description: str
    expected_content: Optional[str] = None
    actual_content: Optional[str] = None
    similarity_score: float = 0.0
    line_range: Optional[Tuple[int, int]] = None
    file_path: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsistencyResult:
    """Result of consistency check."""
    is_consistent: bool
    overall_score: float  # 0.0 to 1.0
    issues: List[ConsistencyIssue] = field(default_factory=list)
    checked_elements: int = 0
    consistent_elements: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def consistency_rate(self) -> float:
        """Get consistency success rate."""
        if self.checked_elements == 0:
            return 1.0
        return (self.consistent_elements / self.checked_elements) * 100
    
    @property
    def critical_issues(self) -> List[ConsistencyIssue]:
        """Get critical consistency issues."""
        return [issue for issue in self.issues if issue.severity == "critical"]


class ConsistencyChecker:
    """Comprehensive code consistency checking system."""
    
    def __init__(self, project_files: Dict[str, str], check_level: ConsistencyLevel = ConsistencyLevel.MODERATE):
        """Initialize consistency checker.
        
        Args:
            project_files: Dict mapping file paths to file contents
            check_level: Level of consistency checking strictness
        """
        self.project_files = project_files
        self.check_level = check_level
        self.file_lines: Dict[str, List[str]] = {}
        self.file_ast_cache: Dict[str, ast.AST] = {}
        
        # Preprocess files
        self._preprocess_files()
    
    def _preprocess_files(self):
        """Preprocess files for consistency checking."""
        for file_path, content in self.project_files.items():
            self.file_lines[file_path] = content.split('\n')
            
            # Parse Python files
            if file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    self.file_ast_cache[file_path] = tree
                except SyntaxError:
                    logger.warning(f"Syntax error in {file_path}, skipping AST parsing")
    
    def check_analysis_consistency(self, analysis_result: Dict[str, Any]) -> ConsistencyResult:
        """Check consistency of analysis result with actual code."""
        result = ConsistencyResult(
            is_consistent=True,
            overall_score=1.0
        )
        
        file_path = analysis_result.get('file_path')
        analysis_text = analysis_result.get('analysis', '')
        
        if not file_path or file_path not in self.project_files:
            result.is_consistent = False
            result.overall_score = 0.0
            result.issues.append(ConsistencyIssue(
                issue_type=ConsistencyType.EXACT_MATCH,
                severity="critical",
                description=f"File path '{file_path}' not found in project",
                file_path=file_path
            ))
            return result
        
        # Check code snippets consistency
        snippet_result = self._check_code_snippets(analysis_text, file_path)
        result.issues.extend(snippet_result.issues)
        result.checked_elements += snippet_result.checked_elements
        result.consistent_elements += snippet_result.consistent_elements
        
        # Check function/class references consistency
        reference_result = self._check_references(analysis_text, file_path)
        result.issues.extend(reference_result.issues)
        result.checked_elements += reference_result.checked_elements
        result.consistent_elements += reference_result.consistent_elements
        
        # Check line number consistency
        line_result = self._check_line_numbers(analysis_text, file_path)
        result.issues.extend(line_result.issues)
        result.checked_elements += line_result.checked_elements
        result.consistent_elements += line_result.consistent_elements
        
        # Check context consistency
        context_result = self._check_context_consistency(analysis_text, file_path)
        result.issues.extend(context_result.issues)
        result.checked_elements += context_result.checked_elements
        result.consistent_elements += context_result.consistent_elements
        
        # Calculate overall score
        if result.checked_elements > 0:
            base_score = result.consistent_elements / result.checked_elements
            
            # Apply penalties for issues
            penalty = 0.0
            for issue in result.issues:
                if issue.severity == "critical":
                    penalty += 0.3
                elif issue.severity == "high":
                    penalty += 0.2
                elif issue.severity == "medium":
                    penalty += 0.1
                elif issue.severity == "low":
                    penalty += 0.05
            
            result.overall_score = max(0.0, base_score - penalty)
        
        # Determine if consistent based on level
        threshold = {
            ConsistencyLevel.STRICT: 0.9,
            ConsistencyLevel.MODERATE: 0.7,
            ConsistencyLevel.LENIENT: 0.5
        }.get(self.check_level, 0.7)
        
        result.is_consistent = result.overall_score >= threshold and len(result.critical_issues) == 0
        
        return result
    
    def _check_code_snippets(self, analysis_text: str, file_path: str) -> ConsistencyResult:
        """Check consistency of code snippets."""
        result = ConsistencyResult(is_consistent=True, overall_score=1.0)
        
        # Extract code blocks
        import re
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', analysis_text, re.DOTALL)
        
        file_lines = self.file_lines[file_path]
        
        for code_block in code_blocks:
            result.checked_elements += 1
            
            # Clean and normalize code block
            snippet_lines = [line.strip() for line in code_block.strip().split('\n') if line.strip()]
            
            if not snippet_lines:
                result.consistent_elements += 1
                continue
            
            # Find best match in file
            best_match = self._find_best_match(snippet_lines, file_lines)
            
            if best_match['score'] >= 0.9:
                result.consistent_elements += 1
            elif best_match['score'] >= 0.7:
                result.consistent_elements += 1
                result.issues.append(ConsistencyIssue(
                    issue_type=ConsistencyType.PARTIAL_MATCH,
                    severity="low",
                    description=f"Code snippet partially matches file content",
                    similarity_score=best_match['score'],
                    line_range=(best_match['start_line'], best_match['end_line']),
                    file_path=file_path,
                    metadata={'match_details': best_match}
                ))
            else:
                result.issues.append(ConsistencyIssue(
                    issue_type=ConsistencyType.EXACT_MATCH,
                    severity="high" if best_match['score'] < 0.3 else "medium",
                    description=f"Code snippet does not match file content (similarity: {best_match['score']:.1%})",
                    expected_content='\n'.join(snippet_lines),
                    actual_content=best_match.get('matched_content', ''),
                    similarity_score=best_match['score'],
                    file_path=file_path,
                    suggestion="Verify that the code snippet is from the correct file and location"
                ))
        
        return result
    
    def _check_references(self, analysis_text: str, file_path: str) -> ConsistencyResult:
        """Check consistency of function/class references."""
        result = ConsistencyResult(is_consistent=True, overall_score=1.0)
        
        if file_path not in self.file_ast_cache:
            return result
        
        tree = self.file_ast_cache[file_path]
        
        # Extract actual functions and classes
        actual_functions = set()
        actual_classes = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                actual_functions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                actual_classes.add(node.name)
        
        # Extract referenced functions and classes from analysis
        import re
        
        # Function references
        func_patterns = [
            r'function\s+`?(\w+)`?',
            r'method\s+`?(\w+)`?',
            r'def\s+(\w+)',
        ]
        
        for pattern in func_patterns:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            for func_name in matches:
                if func_name in ['if', 'for', 'while', 'def', 'class']:  # Skip keywords
                    continue
                
                result.checked_elements += 1
                
                if func_name in actual_functions:
                    result.consistent_elements += 1
                else:
                    # Check if it might be imported or built-in
                    if self._is_likely_external_reference(func_name):
                        result.consistent_elements += 1
                    else:
                        result.issues.append(ConsistencyIssue(
                            issue_type=ConsistencyType.SEMANTIC_MATCH,
                            severity="medium",
                            description=f"Referenced function '{func_name}' not found in file",
                            actual_content=func_name,
                            file_path=file_path,
                            suggestion="Check if function is imported or defined elsewhere"
                        ))
        
        # Class references
        class_patterns = [
            r'class\s+`?(\w+)`?',
            r'(\w+)\s+class',
        ]
        
        for pattern in class_patterns:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            for class_name in matches:
                if class_name.lower() in ['class', 'object', 'type']:  # Skip generic terms
                    continue
                
                result.checked_elements += 1
                
                if class_name in actual_classes:
                    result.consistent_elements += 1
                else:
                    if self._is_likely_external_reference(class_name):
                        result.consistent_elements += 1
                    else:
                        result.issues.append(ConsistencyIssue(
                            issue_type=ConsistencyType.SEMANTIC_MATCH,
                            severity="medium",
                            description=f"Referenced class '{class_name}' not found in file",
                            actual_content=class_name,
                            file_path=file_path,
                            suggestion="Check if class is imported or defined elsewhere"
                        ))
        
        return result
    
    def _check_line_numbers(self, analysis_text: str, file_path: str) -> ConsistencyResult:
        """Check consistency of line number references."""
        result = ConsistencyResult(is_consistent=True, overall_score=1.0)
        
        import re
        
        # Extract line number references with context
        line_patterns = [
            r'line\s+(\d+)[:\s]*([^\n]*)',
            r'on\s+line\s+(\d+)[:\s]*([^\n]*)',
            r'at\s+line\s+(\d+)[:\s]*([^\n]*)',
        ]
        
        file_lines = self.file_lines[file_path]
        max_line = len(file_lines)
        
        for pattern in line_patterns:
            matches = re.finditer(pattern, analysis_text, re.IGNORECASE)
            
            for match in matches:
                line_num = int(match.group(1))
                context = match.group(2).strip()
                
                result.checked_elements += 1
                
                if line_num <= 0 or line_num > max_line:
                    result.issues.append(ConsistencyIssue(
                        issue_type=ConsistencyType.EXACT_MATCH,
                        severity="critical",
                        description=f"Line number {line_num} is out of range (file has {max_line} lines)",
                        actual_content=str(line_num),
                        expected_content=f"1-{max_line}",
                        file_path=file_path
                    ))
                    continue
                
                # Check if context matches actual line content
                actual_line = file_lines[line_num - 1].strip()
                
                if context and actual_line:
                    similarity = self._calculate_text_similarity(context, actual_line)
                    
                    if similarity >= 0.7:
                        result.consistent_elements += 1
                    elif similarity >= 0.4:
                        result.consistent_elements += 1
                        result.issues.append(ConsistencyIssue(
                            issue_type=ConsistencyType.CONTEXT_MATCH,
                            severity="low",
                            description=f"Line {line_num} context partially matches",
                            expected_content=context,
                            actual_content=actual_line,
                            similarity_score=similarity,
                            line_range=(line_num, line_num),
                            file_path=file_path
                        ))
                    else:
                        result.issues.append(ConsistencyIssue(
                            issue_type=ConsistencyType.CONTEXT_MATCH,
                            severity="medium",
                            description=f"Line {line_num} context does not match actual content",
                            expected_content=context,
                            actual_content=actual_line,
                            similarity_score=similarity,
                            line_range=(line_num, line_num),
                            file_path=file_path,
                            suggestion="Verify line number and context accuracy"
                        ))
                else:
                    result.consistent_elements += 1
        
        return result
    
    def _check_context_consistency(self, analysis_text: str, file_path: str) -> ConsistencyResult:
        """Check overall context consistency."""
        result = ConsistencyResult(is_consistent=True, overall_score=1.0)
        
        # Check if analysis mentions features that don't exist in the file
        file_content = self.project_files[file_path]
        
        # Common inconsistencies to check
        checks = [
            ('imports', r'import\s+(\w+)', self._check_import_exists),
            ('variables', r'variable\s+`?(\w+)`?', self._check_variable_usage),
            ('decorators', r'@(\w+)', self._check_decorator_exists),
        ]
        
        for check_name, pattern, check_func in checks:
            import re
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            
            for match in matches:
                result.checked_elements += 1
                
                if check_func(match, file_content):
                    result.consistent_elements += 1
                else:
                    result.issues.append(ConsistencyIssue(
                        issue_type=ConsistencyType.SEMANTIC_MATCH,
                        severity="low",
                        description=f"Referenced {check_name[:-1]} '{match}' not clearly present in file",
                        actual_content=match,
                        file_path=file_path,
                        suggestion=f"Verify {check_name[:-1]} usage in file"
                    ))
        
        return result
    
    def _find_best_match(self, snippet_lines: List[str], file_lines: List[str]) -> Dict[str, Any]:
        """Find best matching section in file for code snippet."""
        best_score = 0.0
        best_start = 0
        best_end = 0
        best_content = ""
        
        snippet_len = len(snippet_lines)
        
        for i in range(len(file_lines) - snippet_len + 1):
            file_section = [line.strip() for line in file_lines[i:i + snippet_len]]
            
            # Calculate similarity
            score = self._calculate_sequence_similarity(snippet_lines, file_section)
            
            if score > best_score:
                best_score = score
                best_start = i + 1  # 1-based line numbers
                best_end = i + snippet_len
                best_content = '\n'.join(file_lines[i:i + snippet_len])
        
        return {
            'score': best_score,
            'start_line': best_start,
            'end_line': best_end,
            'matched_content': best_content
        }
    
    def _calculate_sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """Calculate similarity between two sequences of strings."""
        if not seq1 or not seq2:
            return 0.0
        
        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, seq1, seq2)
        return matcher.ratio()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1 = ' '.join(text1.split())
        text2 = ' '.join(text2.split())
        
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _is_likely_external_reference(self, name: str) -> bool:
        """Check if name is likely an external reference."""
        # Built-ins and common imports
        common_names = {
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set',
            'Exception', 'ValueError', 'TypeError', 'os', 'sys', 'json',
            'time', 'datetime', 'random', 'math', 'requests'
        }
        
        return name in common_names or name.startswith('_') or name.isupper()
    
    def _check_import_exists(self, import_name: str, file_content: str) -> bool:
        """Check if import exists in file."""
        import re
        patterns = [
            rf'import\s+{re.escape(import_name)}',
            rf'from\s+\w+\s+import\s+.*{re.escape(import_name)}',
            rf'from\s+{re.escape(import_name)}\s+import',
        ]
        
        for pattern in patterns:
            if re.search(pattern, file_content):
                return True
        
        return False
    
    def _check_variable_usage(self, var_name: str, file_content: str) -> bool:
        """Check if variable is used in file."""
        import re
        # Simple check for variable usage
        pattern = rf'\b{re.escape(var_name)}\b'
        return bool(re.search(pattern, file_content))
    
    def _check_decorator_exists(self, decorator_name: str, file_content: str) -> bool:
        """Check if decorator exists in file."""
        import re
        pattern = rf'@{re.escape(decorator_name)}'
        return bool(re.search(pattern, file_content))
