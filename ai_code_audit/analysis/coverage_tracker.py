"""
Coverage tracking system for AI Code Audit System.

This module provides comprehensive coverage tracking including:
- File and function-level coverage tracking
- Analysis status monitoring (analyzed, pending, skipped)
- Coverage gap identification
- Priority-based task queue management
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import json
from datetime import datetime

from ..core.models import FileInfo, ProjectInfo

logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    """Analysis status for code units."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class CoverageLevel(Enum):
    """Coverage granularity levels."""
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"


class Priority(Enum):
    """Priority levels for analysis tasks."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class CodeUnit:
    """Represents a unit of code for coverage tracking."""
    id: str
    name: str
    file_path: str
    start_line: int
    end_line: int
    unit_type: CoverageLevel
    status: AnalysisStatus = AnalysisStatus.PENDING
    priority: Priority = Priority.MEDIUM
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: Optional[datetime] = None
    analysis_duration: Optional[float] = None
    
    @property
    def line_count(self) -> int:
        """Get number of lines in this code unit."""
        return self.end_line - self.start_line + 1
    
    @property
    def is_analyzed(self) -> bool:
        """Check if this unit has been analyzed."""
        return self.status == AnalysisStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Check if this unit is pending analysis."""
        return self.status == AnalysisStatus.PENDING


@dataclass
class CoverageStats:
    """Coverage statistics."""
    total_units: int = 0
    analyzed_units: int = 0
    pending_units: int = 0
    skipped_units: int = 0
    failed_units: int = 0
    
    @property
    def coverage_percentage(self) -> float:
        """Calculate coverage percentage."""
        if self.total_units == 0:
            return 0.0
        return (self.analyzed_units / self.total_units) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        processed = self.analyzed_units + self.failed_units
        if processed == 0:
            return 0.0
        return (self.analyzed_units / processed) * 100


@dataclass
class CoverageReport:
    """Coverage analysis report."""
    project_path: str
    total_stats: CoverageStats
    file_stats: Dict[str, CoverageStats] = field(default_factory=dict)
    uncovered_units: List[CodeUnit] = field(default_factory=list)
    high_priority_gaps: List[CodeUnit] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class CoverageTracker:
    """Comprehensive coverage tracking system."""
    
    def __init__(self, project_info: ProjectInfo):
        """Initialize coverage tracker."""
        self.project_info = project_info
        self.code_units: Dict[str, CodeUnit] = {}
        self.file_units: Dict[str, List[str]] = {}  # file_path -> unit_ids
        self.priority_queue: Dict[Priority, List[str]] = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: []
        }
        
        # Initialize code units
        self._discover_code_units()
        self._build_priority_queue()
    
    def _discover_code_units(self):
        """Discover all code units in the project."""
        logger.info("Discovering code units for coverage tracking...")
        
        for file_info in self.project_info.files:
            if not file_info.language or file_info.language not in ['python', 'javascript', 'java', 'go']:
                continue
            
            try:
                # Add file-level unit
                file_unit_id = f"file:{file_info.path}"
                file_unit = CodeUnit(
                    id=file_unit_id,
                    name=Path(file_info.path).name,
                    file_path=file_info.path,
                    start_line=1,
                    end_line=self._get_file_line_count(file_info.absolute_path),
                    unit_type=CoverageLevel.FILE,
                    priority=self._calculate_file_priority(file_info),
                    metadata={'file_info': file_info}
                )
                
                self.code_units[file_unit_id] = file_unit
                self.file_units[file_info.path] = [file_unit_id]
                
                # Discover function and class units for Python files
                if file_info.language == 'python':
                    function_units = self._discover_python_units(file_info)
                    for unit in function_units:
                        self.code_units[unit.id] = unit
                        self.file_units[file_info.path].append(unit.id)
                
            except Exception as e:
                logger.warning(f"Failed to discover units in {file_info.path}: {e}")
        
        logger.info(f"Discovered {len(self.code_units)} code units across {len(self.file_units)} files")
    
    def _discover_python_units(self, file_info: FileInfo) -> List[CodeUnit]:
        """Discover Python functions and classes."""
        units = []
        
        try:
            file_path = Path(file_info.absolute_path)
            if not file_path.exists():
                return units
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    unit_id = f"function:{file_info.path}:{node.name}:{node.lineno}"
                    unit = CodeUnit(
                        id=unit_id,
                        name=node.name,
                        file_path=file_info.path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno + 10,
                        unit_type=CoverageLevel.FUNCTION,
                        priority=self._calculate_function_priority(node.name, file_info),
                        metadata={'function_name': node.name, 'is_async': isinstance(node, ast.AsyncFunctionDef)}
                    )
                    units.append(unit)
                
                elif isinstance(node, ast.ClassDef):
                    unit_id = f"class:{file_info.path}:{node.name}:{node.lineno}"
                    unit = CodeUnit(
                        id=unit_id,
                        name=node.name,
                        file_path=file_info.path,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno + 20,
                        unit_type=CoverageLevel.CLASS,
                        priority=self._calculate_class_priority(node.name, file_info),
                        metadata={'class_name': node.name}
                    )
                    units.append(unit)
        
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_info.path}: {e}")
        except Exception as e:
            logger.warning(f"Failed to parse {file_info.path}: {e}")
        
        return units
    
    def _get_file_line_count(self, file_path: str) -> int:
        """Get line count of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 1
    
    def _calculate_file_priority(self, file_info: FileInfo) -> Priority:
        """Calculate priority for a file."""
        file_path_lower = file_info.path.lower()
        
        # Critical files
        if any(pattern in file_path_lower for pattern in [
            'auth', 'login', 'password', 'token', 'session', 'security',
            'admin', 'config', 'database', 'api', 'main', 'app'
        ]):
            return Priority.CRITICAL
        
        # High priority files
        if any(pattern in file_path_lower for pattern in [
            'user', 'payment', 'order', 'transaction', 'crypto'
        ]):
            return Priority.HIGH
        
        # Skip test files (low priority)
        if any(pattern in file_path_lower for pattern in ['test', 'spec', 'mock']):
            return Priority.LOW
        
        return Priority.MEDIUM
    
    def _calculate_function_priority(self, function_name: str, file_info: FileInfo) -> Priority:
        """Calculate priority for a function."""
        func_name_lower = function_name.lower()
        
        # Critical functions
        if any(pattern in func_name_lower for pattern in [
            'auth', 'login', 'password', 'encrypt', 'decrypt', 'validate',
            'execute', 'query', 'admin', 'delete', 'create', 'update'
        ]):
            return Priority.CRITICAL
        
        # High priority functions
        if any(pattern in func_name_lower for pattern in [
            'process', 'handle', 'parse', 'verify', 'check'
        ]):
            return Priority.HIGH
        
        # Test functions (low priority)
        if func_name_lower.startswith('test_'):
            return Priority.LOW
        
        # Inherit from file priority
        file_priority = self._calculate_file_priority(file_info)
        return file_priority
    
    def _calculate_class_priority(self, class_name: str, file_info: FileInfo) -> Priority:
        """Calculate priority for a class."""
        class_name_lower = class_name.lower()
        
        # Critical classes
        if any(pattern in class_name_lower for pattern in [
            'auth', 'user', 'admin', 'security', 'crypto', 'database',
            'api', 'controller', 'service', 'manager'
        ]):
            return Priority.CRITICAL
        
        # High priority classes
        if any(pattern in class_name_lower for pattern in [
            'model', 'handler', 'processor', 'validator'
        ]):
            return Priority.HIGH
        
        # Test classes (low priority)
        if class_name_lower.startswith('test'):
            return Priority.LOW
        
        return Priority.MEDIUM
    
    def _build_priority_queue(self):
        """Build priority-based task queue."""
        for unit in self.code_units.values():
            if unit.status == AnalysisStatus.PENDING:
                self.priority_queue[unit.priority].append(unit.id)
        
        # Sort each priority level by additional criteria
        for priority in Priority:
            self.priority_queue[priority].sort(key=lambda unit_id: (
                self.code_units[unit_id].file_path,
                self.code_units[unit_id].start_line
            ))
    
    def get_next_units(self, count: int = 1, priority_filter: Optional[Priority] = None) -> List[CodeUnit]:
        """Get next units for analysis."""
        units = []
        
        priorities = [priority_filter] if priority_filter else list(Priority)
        
        for priority in priorities:
            while len(units) < count and self.priority_queue[priority]:
                unit_id = self.priority_queue[priority].pop(0)
                unit = self.code_units[unit_id]
                
                if unit.status == AnalysisStatus.PENDING:
                    units.append(unit)
        
        return units
    
    def mark_unit_analyzed(self, unit_id: str, analysis_duration: Optional[float] = None):
        """Mark a unit as analyzed."""
        if unit_id in self.code_units:
            unit = self.code_units[unit_id]
            unit.status = AnalysisStatus.COMPLETED
            unit.analyzed_at = datetime.now()
            unit.analysis_duration = analysis_duration
            
            logger.debug(f"Marked unit {unit_id} as analyzed")
    
    def mark_unit_failed(self, unit_id: str, error: str):
        """Mark a unit as failed."""
        if unit_id in self.code_units:
            unit = self.code_units[unit_id]
            unit.status = AnalysisStatus.FAILED
            unit.metadata['error'] = error
            
            logger.warning(f"Marked unit {unit_id} as failed: {error}")
    
    def mark_unit_skipped(self, unit_id: str, reason: str):
        """Mark a unit as skipped."""
        if unit_id in self.code_units:
            unit = self.code_units[unit_id]
            unit.status = AnalysisStatus.SKIPPED
            unit.metadata['skip_reason'] = reason
            
            logger.debug(f"Marked unit {unit_id} as skipped: {reason}")
    
    def get_coverage_stats(self, file_path: Optional[str] = None) -> CoverageStats:
        """Get coverage statistics."""
        units = self.code_units.values()
        
        if file_path:
            unit_ids = self.file_units.get(file_path, [])
            units = [self.code_units[uid] for uid in unit_ids]
        
        stats = CoverageStats()
        
        for unit in units:
            stats.total_units += 1
            
            if unit.status == AnalysisStatus.COMPLETED:
                stats.analyzed_units += 1
            elif unit.status == AnalysisStatus.PENDING:
                stats.pending_units += 1
            elif unit.status == AnalysisStatus.SKIPPED:
                stats.skipped_units += 1
            elif unit.status == AnalysisStatus.FAILED:
                stats.failed_units += 1
        
        return stats
    
    def generate_coverage_report(self) -> CoverageReport:
        """Generate comprehensive coverage report."""
        total_stats = self.get_coverage_stats()
        
        # File-level statistics
        file_stats = {}
        for file_path in self.file_units:
            file_stats[file_path] = self.get_coverage_stats(file_path)
        
        # Find uncovered units
        uncovered_units = [
            unit for unit in self.code_units.values()
            if unit.status == AnalysisStatus.PENDING
        ]
        
        # Find high-priority gaps
        high_priority_gaps = [
            unit for unit in uncovered_units
            if unit.priority in [Priority.CRITICAL, Priority.HIGH]
        ]
        
        return CoverageReport(
            project_path=self.project_info.path,
            total_stats=total_stats,
            file_stats=file_stats,
            uncovered_units=uncovered_units,
            high_priority_gaps=high_priority_gaps
        )
    
    def get_pending_count(self) -> int:
        """Get count of pending units."""
        return sum(len(queue) for queue in self.priority_queue.values())
    
    def get_units_by_file(self, file_path: str) -> List[CodeUnit]:
        """Get all units for a specific file."""
        unit_ids = self.file_units.get(file_path, [])
        return [self.code_units[uid] for uid in unit_ids]
    
    def export_coverage_data(self, output_path: str):
        """Export coverage data to JSON."""
        data = {
            'project_path': self.project_info.path,
            'generated_at': datetime.now().isoformat(),
            'units': {
                unit_id: {
                    'name': unit.name,
                    'file_path': unit.file_path,
                    'start_line': unit.start_line,
                    'end_line': unit.end_line,
                    'unit_type': unit.unit_type.value,
                    'status': unit.status.value,
                    'priority': unit.priority.value,
                    'analyzed_at': unit.analyzed_at.isoformat() if unit.analyzed_at else None,
                    'analysis_duration': unit.analysis_duration,
                    'metadata': unit.metadata
                }
                for unit_id, unit in self.code_units.items()
            },
            'stats': {
                'total': self.get_coverage_stats().total_units,
                'analyzed': self.get_coverage_stats().analyzed_units,
                'coverage_percentage': self.get_coverage_stats().coverage_percentage
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Coverage data exported to {output_path}")
