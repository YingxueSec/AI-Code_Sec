"""
Hallucination detection system for AI Code Audit System.

This module provides comprehensive hallucination detection including:
- Line number reference validation
- Code snippet verification
- Function/class existence checking
- File path validation
"""

import re
import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationType(Enum):
    """Types of validation checks."""
    LINE_NUMBER = "line_number"
    CODE_SNIPPET = "code_snippet"
    FUNCTION_REFERENCE = "function_reference"
    CLASS_REFERENCE = "class_reference"
    FILE_PATH = "file_path"
    VARIABLE_REFERENCE = "variable_reference"


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    issue_type: ValidationType
    severity: ValidationSeverity
    description: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_elements: int = 0
    total_elements: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def validation_rate(self) -> float:
        """Get validation success rate."""
        if self.total_elements == 0:
            return 1.0
        return (self.validated_elements / self.total_elements) * 100
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get critical validation issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical validation issues."""
        return len(self.critical_issues) > 0


class HallucinationDetector:
    """Comprehensive hallucination detection system."""
    
    def __init__(self, project_files: Dict[str, str]):
        """Initialize hallucination detector.
        
        Args:
            project_files: Dict mapping file paths to file contents
        """
        self.project_files = project_files
        self.file_line_counts: Dict[str, int] = {}
        self.file_ast_cache: Dict[str, ast.AST] = {}
        self.function_index: Dict[str, Set[str]] = {}  # file_path -> function_names
        self.class_index: Dict[str, Set[str]] = {}     # file_path -> class_names
        
        # Build indices
        self._build_indices()
    
    def _build_indices(self):
        """Build indices for validation."""
        logger.info("Building validation indices...")
        
        for file_path, content in self.project_files.items():
            # Count lines
            self.file_line_counts[file_path] = len(content.split('\n'))
            
            # Parse Python files for AST
            if file_path.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    self.file_ast_cache[file_path] = tree
                    
                    # Extract functions and classes
                    functions = set()
                    classes = set()
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.add(node.name)
                        elif isinstance(node, ast.ClassDef):
                            classes.add(node.name)
                    
                    self.function_index[file_path] = functions
                    self.class_index[file_path] = classes
                    
                except SyntaxError:
                    logger.warning(f"Syntax error in {file_path}, skipping AST parsing")
        
        logger.info(f"Built indices for {len(self.project_files)} files")
    
    def validate_analysis_result(self, analysis_result: Dict[str, Any]) -> ValidationResult:
        """Validate an analysis result for hallucinations."""
        result = ValidationResult(
            is_valid=True,
            confidence_score=1.0,
            total_elements=0,
            validated_elements=0
        )
        
        file_path = analysis_result.get('file_path')
        analysis_text = analysis_result.get('analysis', '')
        
        if not file_path or not analysis_text:
            result.is_valid = False
            result.confidence_score = 0.0
            result.issues.append(ValidationIssue(
                issue_type=ValidationType.FILE_PATH,
                severity=ValidationSeverity.CRITICAL,
                description="Missing file path or analysis text"
            ))
            return result
        
        # Validate line number references
        line_validation = self._validate_line_numbers(analysis_text, file_path)
        result.issues.extend(line_validation.issues)
        result.total_elements += line_validation.total_elements
        result.validated_elements += line_validation.validated_elements
        
        # Validate code snippets
        snippet_validation = self._validate_code_snippets(analysis_text, file_path)
        result.issues.extend(snippet_validation.issues)
        result.total_elements += snippet_validation.total_elements
        result.validated_elements += snippet_validation.validated_elements
        
        # Validate function references
        function_validation = self._validate_function_references(analysis_text, file_path)
        result.issues.extend(function_validation.issues)
        result.total_elements += function_validation.total_elements
        result.validated_elements += function_validation.validated_elements
        
        # Validate class references
        class_validation = self._validate_class_references(analysis_text, file_path)
        result.issues.extend(class_validation.issues)
        result.total_elements += class_validation.total_elements
        result.validated_elements += class_validation.validated_elements
        
        # Calculate overall confidence
        if result.total_elements > 0:
            base_confidence = result.validated_elements / result.total_elements
            
            # Reduce confidence based on issue severity
            severity_penalties = {
                ValidationSeverity.CRITICAL: 0.5,
                ValidationSeverity.HIGH: 0.3,
                ValidationSeverity.MEDIUM: 0.2,
                ValidationSeverity.LOW: 0.1,
                ValidationSeverity.INFO: 0.05
            }
            
            penalty = 0.0
            for issue in result.issues:
                penalty += severity_penalties.get(issue.severity, 0.0)
            
            result.confidence_score = max(0.0, base_confidence - penalty)
        
        # Determine if result is valid
        result.is_valid = result.confidence_score >= 0.7 and not result.has_critical_issues
        
        return result
    
    def _validate_line_numbers(self, analysis_text: str, file_path: str) -> ValidationResult:
        """Validate line number references in analysis text."""
        result = ValidationResult(is_valid=True, confidence_score=1.0)
        
        # Extract line number references
        line_patterns = [
            r'line\s+(\d+)',
            r'line\s+number\s+(\d+)',
            r'on\s+line\s+(\d+)',
            r'at\s+line\s+(\d+)',
            r':(\d+):',  # file:line: format
        ]
        
        max_line = self.file_line_counts.get(file_path, 0)
        
        for pattern in line_patterns:
            matches = re.finditer(pattern, analysis_text, re.IGNORECASE)
            
            for match in matches:
                line_num = int(match.group(1))
                result.total_elements += 1
                
                if line_num <= 0:
                    result.issues.append(ValidationIssue(
                        issue_type=ValidationType.LINE_NUMBER,
                        severity=ValidationSeverity.CRITICAL,
                        description=f"Invalid line number: {line_num} (must be positive)",
                        actual=str(line_num),
                        file_path=file_path
                    ))
                elif line_num > max_line:
                    result.issues.append(ValidationIssue(
                        issue_type=ValidationType.LINE_NUMBER,
                        severity=ValidationSeverity.HIGH,
                        description=f"Line number {line_num} exceeds file length ({max_line} lines)",
                        actual=str(line_num),
                        expected=f"<= {max_line}",
                        file_path=file_path,
                        suggestion=f"Check if line number should be <= {max_line}"
                    ))
                else:
                    result.validated_elements += 1
        
        return result
    
    def _validate_code_snippets(self, analysis_text: str, file_path: str) -> ValidationResult:
        """Validate code snippets in analysis text."""
        result = ValidationResult(is_valid=True, confidence_score=1.0)
        
        # Extract code blocks
        code_block_pattern = r'```[\w]*\n(.*?)\n```'
        matches = re.finditer(code_block_pattern, analysis_text, re.DOTALL)
        
        file_content = self.project_files.get(file_path, '')
        file_lines = file_content.split('\n')
        
        for match in matches:
            code_snippet = match.group(1).strip()
            result.total_elements += 1
            
            if not code_snippet:
                continue
            
            # Check if snippet exists in file
            snippet_lines = [line.strip() for line in code_snippet.split('\n') if line.strip()]
            
            if self._find_snippet_in_file(snippet_lines, file_lines):
                result.validated_elements += 1
            else:
                # Check for partial matches
                partial_match_score = self._calculate_partial_match(snippet_lines, file_lines)
                
                if partial_match_score > 0.7:
                    result.validated_elements += 1
                    result.issues.append(ValidationIssue(
                        issue_type=ValidationType.CODE_SNIPPET,
                        severity=ValidationSeverity.LOW,
                        description=f"Code snippet partially matches file content ({partial_match_score:.1%} similarity)",
                        file_path=file_path,
                        metadata={'similarity_score': partial_match_score}
                    ))
                else:
                    result.issues.append(ValidationIssue(
                        issue_type=ValidationType.CODE_SNIPPET,
                        severity=ValidationSeverity.HIGH,
                        description="Code snippet not found in file",
                        actual=code_snippet[:100] + "..." if len(code_snippet) > 100 else code_snippet,
                        file_path=file_path,
                        suggestion="Verify that the code snippet is from the correct file"
                    ))
        
        return result
    
    def _validate_function_references(self, analysis_text: str, file_path: str) -> ValidationResult:
        """Validate function references in analysis text."""
        result = ValidationResult(is_valid=True, confidence_score=1.0)
        
        # Extract function references
        function_patterns = [
            r'function\s+`?(\w+)`?',
            r'method\s+`?(\w+)`?',
            r'def\s+(\w+)',
            r'(\w+)\s*\(',  # Function calls
        ]
        
        file_functions = self.function_index.get(file_path, set())
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, analysis_text, re.IGNORECASE)
            
            for match in matches:
                func_name = match.group(1)
                
                # Skip common words and keywords
                if func_name.lower() in ['if', 'for', 'while', 'def', 'class', 'import', 'return']:
                    continue
                
                result.total_elements += 1
                
                if func_name in file_functions:
                    result.validated_elements += 1
                else:
                    # Check if it might be a built-in or imported function
                    if self._is_likely_builtin_or_import(func_name):
                        result.validated_elements += 1
                    else:
                        result.issues.append(ValidationIssue(
                            issue_type=ValidationType.FUNCTION_REFERENCE,
                            severity=ValidationSeverity.MEDIUM,
                            description=f"Function '{func_name}' not found in file",
                            actual=func_name,
                            file_path=file_path,
                            suggestion="Verify function name or check if it's imported"
                        ))
        
        return result
    
    def _validate_class_references(self, analysis_text: str, file_path: str) -> ValidationResult:
        """Validate class references in analysis text."""
        result = ValidationResult(is_valid=True, confidence_score=1.0)
        
        # Extract class references
        class_patterns = [
            r'class\s+`?(\w+)`?',
            r'(\w+)\s+class',
            r'instance\s+of\s+`?(\w+)`?',
        ]
        
        file_classes = self.class_index.get(file_path, set())
        
        for pattern in class_patterns:
            matches = re.finditer(pattern, analysis_text, re.IGNORECASE)
            
            for match in matches:
                class_name = match.group(1)
                
                # Skip common words
                if class_name.lower() in ['class', 'instance', 'object', 'type']:
                    continue
                
                result.total_elements += 1
                
                if class_name in file_classes:
                    result.validated_elements += 1
                else:
                    # Check if it might be a built-in or imported class
                    if self._is_likely_builtin_or_import(class_name):
                        result.validated_elements += 1
                    else:
                        result.issues.append(ValidationIssue(
                            issue_type=ValidationType.CLASS_REFERENCE,
                            severity=ValidationSeverity.MEDIUM,
                            description=f"Class '{class_name}' not found in file",
                            actual=class_name,
                            file_path=file_path,
                            suggestion="Verify class name or check if it's imported"
                        ))
        
        return result
    
    def _find_snippet_in_file(self, snippet_lines: List[str], file_lines: List[str]) -> bool:
        """Check if code snippet exists in file."""
        if not snippet_lines:
            return True
        
        snippet_len = len(snippet_lines)
        
        for i in range(len(file_lines) - snippet_len + 1):
            file_section = [line.strip() for line in file_lines[i:i + snippet_len]]
            
            if file_section == snippet_lines:
                return True
        
        return False
    
    def _calculate_partial_match(self, snippet_lines: List[str], file_lines: List[str]) -> float:
        """Calculate partial match score between snippet and file."""
        if not snippet_lines:
            return 1.0
        
        best_score = 0.0
        snippet_len = len(snippet_lines)
        
        for i in range(len(file_lines) - snippet_len + 1):
            file_section = [line.strip() for line in file_lines[i:i + snippet_len]]
            
            # Calculate similarity
            matches = sum(1 for s, f in zip(snippet_lines, file_section) if s == f)
            score = matches / snippet_len
            
            best_score = max(best_score, score)
        
        return best_score
    
    def _is_likely_builtin_or_import(self, name: str) -> bool:
        """Check if name is likely a built-in function or imported."""
        # Common built-in functions and types
        builtins = {
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'max', 'min',
            'sum', 'any', 'all', 'isinstance', 'hasattr', 'getattr', 'setattr',
            'open', 'input', 'format', 'join', 'split', 'strip', 'replace',
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError'
        }
        
        # Common imported modules/functions
        common_imports = {
            'os', 'sys', 'json', 'time', 'datetime', 'random', 'math',
            'requests', 'urllib', 'logging', 'pathlib', 'collections',
            'itertools', 'functools', 'operator', 'copy', 'pickle'
        }
        
        return name in builtins or name in common_imports or name.startswith('_')
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results."""
        if not results:
            return {}
        
        total_elements = sum(r.total_elements for r in results)
        validated_elements = sum(r.validated_elements for r in results)
        total_issues = sum(len(r.issues) for r in results)
        
        # Count issues by severity
        severity_counts = {}
        for result in results:
            for issue in result.issues:
                severity = issue.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count issues by type
        type_counts = {}
        for result in results:
            for issue in result.issues:
                issue_type = issue.issue_type.value
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return {
            'total_validations': len(results),
            'valid_results': len([r for r in results if r.is_valid]),
            'validation_rate': (validated_elements / total_elements * 100) if total_elements > 0 else 100,
            'average_confidence': sum(r.confidence_score for r in results) / len(results),
            'total_issues': total_issues,
            'severity_distribution': severity_counts,
            'issue_type_distribution': type_counts,
            'critical_issues': sum(len(r.critical_issues) for r in results),
        }
