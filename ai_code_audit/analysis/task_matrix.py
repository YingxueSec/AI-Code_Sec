"""
Task matrix management system for AI Code Audit System.

This module provides intelligent task prioritization and queue management including:
- Multi-dimensional priority matrix
- Dynamic priority adjustment
- Resource-aware task scheduling
- Dependency-based task ordering
"""

import heapq
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

from .coverage_tracker import CodeUnit, Priority, AnalysisStatus

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of analysis tasks."""
    FILE_ANALYSIS = "file_analysis"
    FUNCTION_ANALYSIS = "function_analysis"
    CLASS_ANALYSIS = "class_analysis"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_CHECK = "dependency_check"
    CONTEXT_BUILD = "context_build"


class UrgencyLevel(Enum):
    """Urgency levels for tasks."""
    IMMEDIATE = 1
    URGENT = 2
    NORMAL = 3
    DEFERRED = 4


class ComplexityLevel(Enum):
    """Complexity levels for tasks."""
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    VERY_COMPLEX = 4


@dataclass
class TaskMetrics:
    """Metrics for task prioritization."""
    security_impact: float = 0.5  # 0.0 to 1.0
    business_criticality: float = 0.5  # 0.0 to 1.0
    technical_complexity: float = 0.5  # 0.0 to 1.0
    estimated_duration: float = 60.0  # seconds
    dependency_count: int = 0
    failure_risk: float = 0.1  # 0.0 to 1.0
    
    def calculate_priority_score(self) -> float:
        """Calculate overall priority score."""
        # Weighted scoring algorithm
        weights = {
            'security': 0.35,
            'business': 0.25,
            'complexity': -0.15,  # Higher complexity = lower priority
            'duration': -0.10,    # Longer duration = lower priority
            'dependencies': -0.05,
            'risk': -0.10
        }
        
        score = (
            weights['security'] * self.security_impact +
            weights['business'] * self.business_criticality +
            weights['complexity'] * (1.0 - self.technical_complexity) +
            weights['duration'] * (1.0 - min(self.estimated_duration / 300.0, 1.0)) +
            weights['dependencies'] * (1.0 - min(self.dependency_count / 10.0, 1.0)) +
            weights['risk'] * (1.0 - self.failure_risk)
        )
        
        return max(0.0, min(1.0, score))


@dataclass
class AnalysisTask:
    """Analysis task with priority matrix attributes."""
    id: str
    code_unit: CodeUnit
    task_type: TaskType
    priority: Priority
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    complexity: ComplexityLevel = ComplexityLevel.MODERATE
    metrics: TaskMetrics = field(default_factory=TaskMetrics)
    dependencies: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def priority_score(self) -> float:
        """Get calculated priority score."""
        return self.metrics.calculate_priority_score()
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready for execution."""
        return len(self.dependencies) == 0 and self.code_unit.status == AnalysisStatus.PENDING
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.estimated_completion:
            return datetime.now() > self.estimated_completion
        return False
    
    def __lt__(self, other):
        """Comparison for priority queue (higher score = higher priority)."""
        return self.priority_score > other.priority_score


@dataclass
class MatrixConfig:
    """Configuration for task matrix."""
    max_queue_size: int = 1000
    priority_boost_threshold: int = 3  # Boost priority after N retries
    urgency_multiplier: float = 1.5
    complexity_penalty: float = 0.8
    dependency_timeout_hours: int = 24
    enable_dynamic_adjustment: bool = True
    rebalance_interval_minutes: int = 15


class TaskMatrix:
    """Intelligent task prioritization and queue management system."""
    
    def __init__(self, config: Optional[MatrixConfig] = None):
        """Initialize task matrix."""
        self.config = config or MatrixConfig()
        
        # Priority queue (heap) - stores (negative_priority_score, task_id, task)
        self.task_queue: List[Tuple[float, str, AnalysisTask]] = []
        self.tasks: Dict[str, AnalysisTask] = {}
        self.completed_tasks: Dict[str, AnalysisTask] = {}
        self.failed_tasks: Dict[str, AnalysisTask] = {}
        
        # Dependency tracking
        self.dependency_graph: Dict[str, Set[str]] = {}  # task_id -> dependent_task_ids
        self.reverse_dependencies: Dict[str, Set[str]] = {}  # task_id -> dependency_task_ids
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_completion_time': 0.0,
            'priority_adjustments': 0,
        }
        
        # Last rebalance time
        self.last_rebalance = datetime.now()
    
    def add_task(self, task: AnalysisTask) -> bool:
        """Add task to the matrix."""
        if len(self.task_queue) >= self.config.max_queue_size:
            logger.warning("Task queue is full, rejecting new task")
            return False
        
        # Calculate initial metrics
        self._calculate_task_metrics(task)
        
        # Add to queue and tracking
        self.tasks[task.id] = task
        heapq.heappush(self.task_queue, (-task.priority_score, task.id, task))
        
        # Update dependency tracking
        self._update_dependency_graph(task)
        
        self.stats['total_tasks'] += 1
        
        logger.debug(f"Added task {task.id} with priority score {task.priority_score:.3f}")
        return True
    
    def get_next_task(self, resource_constraints: Optional[Dict[str, Any]] = None) -> Optional[AnalysisTask]:
        """Get next task for execution."""
        # Rebalance if needed
        if self._should_rebalance():
            self._rebalance_queue()
        
        # Find next ready task
        while self.task_queue:
            _, task_id, task = heapq.heappop(self.task_queue)
            
            # Check if task is still valid and ready
            if task_id in self.tasks and task.is_ready:
                # Check resource constraints
                if self._meets_resource_constraints(task, resource_constraints):
                    task.started_at = datetime.now()
                    task.code_unit.status = AnalysisStatus.IN_PROGRESS
                    
                    # Estimate completion time
                    task.estimated_completion = datetime.now() + timedelta(
                        seconds=task.metrics.estimated_duration
                    )
                    
                    logger.debug(f"Selected task {task_id} for execution")
                    return task
                else:
                    # Put back in queue if resource constraints not met
                    heapq.heappush(self.task_queue, (-task.priority_score, task_id, task))
                    break
        
        return None
    
    def complete_task(self, task_id: str, success: bool = True, duration: Optional[float] = None):
        """Mark task as completed."""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        if success:
            task.code_unit.status = AnalysisStatus.COMPLETED
            self.completed_tasks[task_id] = task
            self.stats['completed_tasks'] += 1
            
            # Update average completion time
            if duration:
                total_time = self.stats['average_completion_time'] * (self.stats['completed_tasks'] - 1)
                self.stats['average_completion_time'] = (total_time + duration) / self.stats['completed_tasks']
            
            # Release dependent tasks
            self._release_dependent_tasks(task_id)
            
            logger.debug(f"Task {task_id} completed successfully")
        else:
            task.retry_count += 1
            
            if task.retry_count >= task.max_retries:
                task.code_unit.status = AnalysisStatus.FAILED
                self.failed_tasks[task_id] = task
                self.stats['failed_tasks'] += 1
                logger.warning(f"Task {task_id} failed after {task.retry_count} retries")
            else:
                # Boost priority for retry
                if task.retry_count >= self.config.priority_boost_threshold:
                    task.metrics.security_impact = min(1.0, task.metrics.security_impact * 1.2)
                    self.stats['priority_adjustments'] += 1
                
                # Re-queue for retry
                task.code_unit.status = AnalysisStatus.PENDING
                heapq.heappush(self.task_queue, (-task.priority_score, task_id, task))
                logger.debug(f"Task {task_id} re-queued for retry ({task.retry_count}/{task.max_retries})")
        
        # Remove from active tasks
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def _calculate_task_metrics(self, task: AnalysisTask):
        """Calculate task metrics for prioritization."""
        code_unit = task.code_unit
        
        # Security impact based on file/function characteristics
        security_impact = 0.5
        
        # Check for security-critical patterns
        name_lower = code_unit.name.lower()
        path_lower = code_unit.file_path.lower()
        
        if any(pattern in name_lower or pattern in path_lower for pattern in [
            'auth', 'login', 'password', 'token', 'session', 'security',
            'admin', 'crypto', 'encrypt', 'decrypt', 'validate'
        ]):
            security_impact = 0.9
        elif any(pattern in name_lower or pattern in path_lower for pattern in [
            'api', 'endpoint', 'controller', 'handler', 'process'
        ]):
            security_impact = 0.7
        elif any(pattern in name_lower or pattern in path_lower for pattern in [
            'test', 'spec', 'mock', 'example'
        ]):
            security_impact = 0.2
        
        # Business criticality based on priority
        business_criticality = {
            Priority.CRITICAL: 0.9,
            Priority.HIGH: 0.7,
            Priority.MEDIUM: 0.5,
            Priority.LOW: 0.3
        }.get(task.priority, 0.5)
        
        # Technical complexity based on code unit size and type
        complexity = 0.5
        if code_unit.line_count > 100:
            complexity = 0.8
        elif code_unit.line_count > 50:
            complexity = 0.6
        elif code_unit.line_count < 10:
            complexity = 0.3
        
        # Estimated duration based on complexity and type
        base_duration = {
            TaskType.FILE_ANALYSIS: 60,
            TaskType.FUNCTION_ANALYSIS: 30,
            TaskType.CLASS_ANALYSIS: 45,
            TaskType.SECURITY_SCAN: 90,
            TaskType.DEPENDENCY_CHECK: 20,
            TaskType.CONTEXT_BUILD: 15
        }.get(task.task_type, 60)
        
        estimated_duration = base_duration * (1 + complexity)
        
        # Update task metrics
        task.metrics.security_impact = security_impact
        task.metrics.business_criticality = business_criticality
        task.metrics.technical_complexity = complexity
        task.metrics.estimated_duration = estimated_duration
        task.metrics.dependency_count = len(task.dependencies)
    
    def _update_dependency_graph(self, task: AnalysisTask):
        """Update dependency tracking graph."""
        task_id = task.id
        
        # Initialize dependency tracking
        self.dependency_graph[task_id] = set()
        self.reverse_dependencies[task_id] = task.dependencies.copy()
        
        # Update reverse dependencies
        for dep_id in task.dependencies:
            if dep_id not in self.dependency_graph:
                self.dependency_graph[dep_id] = set()
            self.dependency_graph[dep_id].add(task_id)
    
    def _release_dependent_tasks(self, completed_task_id: str):
        """Release tasks that were waiting for this dependency."""
        if completed_task_id not in self.dependency_graph:
            return
        
        dependent_task_ids = self.dependency_graph[completed_task_id].copy()
        
        for dep_task_id in dependent_task_ids:
            if dep_task_id in self.reverse_dependencies:
                self.reverse_dependencies[dep_task_id].discard(completed_task_id)
                
                # If no more dependencies, task becomes ready
                if not self.reverse_dependencies[dep_task_id]:
                    logger.debug(f"Task {dep_task_id} is now ready (dependencies resolved)")
    
    def _meets_resource_constraints(self, task: AnalysisTask, constraints: Optional[Dict[str, Any]]) -> bool:
        """Check if task meets resource constraints."""
        if not constraints:
            return True
        
        # Check memory constraints
        if 'max_memory_mb' in constraints:
            estimated_memory = task.metrics.technical_complexity * 100  # Rough estimate
            if estimated_memory > constraints['max_memory_mb']:
                return False
        
        # Check time constraints
        if 'max_duration_seconds' in constraints:
            if task.metrics.estimated_duration > constraints['max_duration_seconds']:
                return False
        
        # Check complexity constraints
        if 'max_complexity' in constraints:
            if task.complexity.value > constraints['max_complexity']:
                return False
        
        return True
    
    def _should_rebalance(self) -> bool:
        """Check if queue should be rebalanced."""
        if not self.config.enable_dynamic_adjustment:
            return False
        
        time_since_rebalance = datetime.now() - self.last_rebalance
        return time_since_rebalance.total_seconds() > (self.config.rebalance_interval_minutes * 60)
    
    def _rebalance_queue(self):
        """Rebalance task queue based on current conditions."""
        logger.debug("Rebalancing task queue...")
        
        # Extract all tasks from heap
        current_tasks = []
        while self.task_queue:
            _, task_id, task = heapq.heappop(self.task_queue)
            if task_id in self.tasks:
                current_tasks.append(task)
        
        # Recalculate priorities and re-add to queue
        for task in current_tasks:
            # Boost priority for overdue tasks
            if task.is_overdue:
                task.metrics.security_impact = min(1.0, task.metrics.security_impact * 1.3)
                self.stats['priority_adjustments'] += 1
            
            # Recalculate metrics
            self._calculate_task_metrics(task)
            
            # Re-add to queue
            heapq.heappush(self.task_queue, (-task.priority_score, task.id, task))
        
        self.last_rebalance = datetime.now()
        logger.debug(f"Rebalanced {len(current_tasks)} tasks")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self.stats,
            'queue_size': len(self.task_queue),
            'active_tasks': len(self.tasks),
            'pending_dependencies': sum(len(deps) for deps in self.reverse_dependencies.values()),
            'last_rebalance': self.last_rebalance.isoformat(),
        }
    
    def get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of tasks by priority."""
        distribution = {priority.name: 0 for priority in Priority}
        
        for task in self.tasks.values():
            distribution[task.priority.name] += 1
        
        return distribution
    
    def clear_completed_tasks(self, older_than_hours: int = 24):
        """Clear old completed tasks to free memory."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        to_remove = []
        for task_id, task in self.completed_tasks.items():
            if task.started_at and task.started_at < cutoff_time:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.completed_tasks[task_id]
        
        logger.debug(f"Cleared {len(to_remove)} old completed tasks")
