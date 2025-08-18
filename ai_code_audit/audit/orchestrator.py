"""
Analysis orchestrator for managing file analysis workflows.

This module provides orchestration capabilities including:
- Task scheduling and queuing
- Priority management
- Concurrency control
- Error handling and retry logic
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from pathlib import Path

from ..core.models import FileInfo, ProjectInfo
from ..llm.manager import LLMManager
from ..llm.base import LLMRequest, LLMMessage, MessageRole, LLMModelType
from ..llm.prompts import PromptManager
from .session_manager import AuditSession, SessionStatus

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Analysis task status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AnalysisTask:
    """Analysis task data structure."""
    task_id: str
    file_info: FileInfo
    template: str
    model: LLMModelType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get task duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_retryable(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED


@dataclass
class OrchestrationConfig:
    """Configuration for analysis orchestration."""
    max_concurrent_tasks: int = 3
    max_queue_size: int = 100
    task_timeout_minutes: int = 10
    retry_delay_seconds: int = 5
    priority_boost_threshold: int = 3  # Boost priority after N retries
    enable_smart_scheduling: bool = True
    file_size_weight: float = 0.3
    complexity_weight: float = 0.4
    dependency_weight: float = 0.3


class AnalysisOrchestrator:
    """Orchestrator for managing analysis workflows."""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        prompt_manager: PromptManager,
        config: Optional[OrchestrationConfig] = None
    ):
        """Initialize orchestrator."""
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager
        self.config = config or OrchestrationConfig()
        
        # Task management
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=self.config.max_queue_size
        )
        self.running_tasks: Dict[str, AnalysisTask] = {}
        self.completed_tasks: Dict[str, AnalysisTask] = {}
        self.failed_tasks: Dict[str, AnalysisTask] = {}
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        self.worker_tasks: List[asyncio.Task] = []
        self.is_running = False
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'retried_tasks': 0,
            'average_duration': 0.0,
        }
    
    async def start(self):
        """Start the orchestrator."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.config.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        logger.info(f"Started orchestrator with {self.config.max_concurrent_tasks} workers")
    
    async def stop(self):
        """Stop the orchestrator."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all worker tasks
        for worker in self.worker_tasks:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("Stopped orchestrator")
    
    async def schedule_analysis(
        self,
        session: AuditSession,
        files: List[FileInfo],
        template: str = "security_audit",
        model: Optional[LLMModelType] = None
    ) -> List[str]:
        """Schedule analysis tasks for files."""
        if not self.is_running:
            await self.start()
        
        if model is None:
            model = LLMModelType.QWEN_CODER_30B
        
        task_ids = []
        
        for file_info in files:
            # Skip files that are too large or unsupported
            if not self._should_analyze_file(file_info):
                continue
            
            # Create analysis task
            task = AnalysisTask(
                task_id=f"{session.session_id}_{file_info.path}_{datetime.now().timestamp()}",
                file_info=file_info,
                template=template,
                model=model,
                priority=self._calculate_priority(file_info, session.project_info),
                metadata={
                    'session_id': session.session_id,
                    'project_path': session.project_path,
                }
            )
            
            # Add to queue
            try:
                await self.task_queue.put((task.priority.value, task.created_at, task))
                task.status = TaskStatus.QUEUED
                task_ids.append(task.task_id)
                self.stats['total_tasks'] += 1
                
                logger.debug(f"Queued task {task.task_id} for file {file_info.path}")
                
            except asyncio.QueueFull:
                logger.warning(f"Queue full, skipping file {file_info.path}")
                continue
        
        logger.info(f"Scheduled {len(task_ids)} analysis tasks for session {session.session_id}")
        return task_ids
    
    async def get_task_status(self, task_id: str) -> Optional[AnalysisTask]:
        """Get task status by ID."""
        # Check running tasks
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = await self.get_task_status(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            task.status = TaskStatus.SKIPPED
            return True
        
        # For running tasks, we can't easily cancel them
        # This would require more complex task tracking
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        total_completed = self.stats['completed_tasks']
        total_failed = self.stats['failed_tasks']
        total_processed = total_completed + total_failed
        
        return {
            **self.stats,
            'success_rate': (total_completed / total_processed * 100) if total_processed > 0 else 0,
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'is_running': self.is_running,
        }
    
    async def _worker(self, worker_name: str):
        """Worker coroutine for processing tasks."""
        logger.info(f"Started worker {worker_name}")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                try:
                    priority, created_at, task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process task
                await self._process_task(task, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
        
        logger.info(f"Stopped worker {worker_name}")
    
    async def _process_task(self, task: AnalysisTask, worker_name: str):
        """Process a single analysis task."""
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.running_tasks[task.task_id] = task
            
            logger.info(f"Worker {worker_name} processing task {task.task_id}")
            
            try:
                # Set task timeout
                result = await asyncio.wait_for(
                    self._analyze_file(task),
                    timeout=self.config.task_timeout_minutes * 60
                )
                
                # Task completed successfully
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                
                # Move to completed tasks
                self.completed_tasks[task.task_id] = task
                self.stats['completed_tasks'] += 1
                
                # Update average duration
                if task.duration:
                    total_duration = self.stats['average_duration'] * (self.stats['completed_tasks'] - 1)
                    self.stats['average_duration'] = (total_duration + task.duration.total_seconds()) / self.stats['completed_tasks']
                
                logger.info(f"Task {task.task_id} completed successfully")
                
            except asyncio.TimeoutError:
                await self._handle_task_failure(task, "Task timeout")
            except Exception as e:
                await self._handle_task_failure(task, str(e))
            
            finally:
                # Remove from running tasks
                if task.task_id in self.running_tasks:
                    del self.running_tasks[task.task_id]
    
    async def _analyze_file(self, task: AnalysisTask) -> Dict[str, Any]:
        """Analyze a single file."""
        file_info = task.file_info
        
        # Read file content
        try:
            file_path = Path(file_info.absolute_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_info.absolute_path}")
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Limit content size for API
            max_content_size = 50000  # ~50KB
            if len(content) > max_content_size:
                content = content[:max_content_size] + "\n... (content truncated)"
            
        except Exception as e:
            raise Exception(f"Failed to read file {file_info.path}: {e}")
        
        # Generate prompt
        variables = {
            'language': file_info.language or 'unknown',
            'file_path': file_info.path,
            'code_content': content,
            'file_size': file_info.size,
            'additional_context': f"File analysis for {file_info.path}",
            # Add project-level variables (use defaults if not available)
            'project_type': 'web_application',  # Default for now
            'dependencies': 'flask, sqlite3, subprocess',  # Default for test project
        }

        # Add template-specific variables
        if task.template == 'security_audit':
            variables['security_focus'] = 'comprehensive'
        elif task.template == 'code_review':
            variables['target_element'] = f"File: {file_info.path}"
            variables['context'] = f"Code review analysis"
        elif task.template == 'vulnerability_scan':
            variables['scan_depth'] = 'deep'
        
        prompt = self.prompt_manager.generate_prompt(task.template, variables)
        if not prompt:
            raise Exception(f"Failed to generate prompt for template {task.template}")
        
        # Create LLM request
        request = LLMRequest(
            messages=[
                LLMMessage(MessageRole.SYSTEM, prompt['system']),
                LLMMessage(MessageRole.USER, prompt['user'])
            ],
            model=task.model,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Send to LLM
        response = await self.llm_manager.chat_completion(request)
        
        return {
            'file_path': file_info.path,
            'language': file_info.language,
            'template': task.template,
            'model': task.model.value,
            'analysis': response.content,
            'tokens_used': response.usage.total_tokens if response.usage else 0,
            'provider_used': response.metadata.get('provider_used'),
            'analysis_timestamp': datetime.now().isoformat(),
        }
    
    async def _handle_task_failure(self, task: AnalysisTask, error_message: str):
        """Handle task failure and retry logic."""
        task.error = error_message
        task.retry_count += 1
        
        logger.warning(f"Task {task.task_id} failed: {error_message} (retry {task.retry_count}/{task.max_retries})")
        
        if task.is_retryable:
            # Boost priority for retries
            if task.retry_count >= self.config.priority_boost_threshold:
                if task.priority.value > 1:
                    task.priority = TaskPriority(task.priority.value - 1)
            
            # Add delay before retry
            await asyncio.sleep(self.config.retry_delay_seconds * task.retry_count)
            
            # Re-queue task
            task.status = TaskStatus.RETRYING
            await self.task_queue.put((task.priority.value, task.created_at, task))
            self.stats['retried_tasks'] += 1
            
        else:
            # Task failed permanently
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.failed_tasks[task.task_id] = task
            self.stats['failed_tasks'] += 1
    
    def _should_analyze_file(self, file_info: FileInfo) -> bool:
        """Determine if file should be analyzed."""
        # Skip files without language detection
        if not file_info.language:
            return False
        
        # Skip very large files
        max_file_size = 500000  # 500KB
        if file_info.size > max_file_size:
            return False
        
        # Skip binary files
        binary_extensions = {'.exe', '.dll', '.so', '.dylib', '.bin', '.dat'}
        if Path(file_info.path).suffix.lower() in binary_extensions:
            return False
        
        return True
    
    def _calculate_priority(self, file_info: FileInfo, project_info: ProjectInfo) -> TaskPriority:
        """Calculate task priority based on file characteristics."""
        if not self.config.enable_smart_scheduling:
            return TaskPriority.MEDIUM
        
        score = 0.0
        
        # File size factor (smaller files get higher priority for quick wins)
        size_factor = max(0, 1 - (file_info.size / 100000))  # Normalize to 100KB
        score += size_factor * self.config.file_size_weight
        
        # Complexity factor (based on file type and location)
        complexity_factor = self._calculate_complexity_factor(file_info)
        score += complexity_factor * self.config.complexity_weight
        
        # Dependency factor (important files get higher priority)
        dependency_factor = self._calculate_dependency_factor(file_info, project_info)
        score += dependency_factor * self.config.dependency_weight
        
        # Convert score to priority
        if score >= 0.8:
            return TaskPriority.CRITICAL
        elif score >= 0.6:
            return TaskPriority.HIGH
        elif score >= 0.4:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def _calculate_complexity_factor(self, file_info: FileInfo) -> float:
        """Calculate complexity factor for file."""
        # Security-critical file patterns
        security_patterns = [
            'auth', 'login', 'password', 'token', 'session', 'security',
            'admin', 'config', 'settings', 'database', 'db', 'sql',
            'api', 'endpoint', 'route', 'controller', 'middleware'
        ]
        
        file_path_lower = file_info.path.lower()
        
        # Check for security-critical patterns
        for pattern in security_patterns:
            if pattern in file_path_lower:
                return 0.9
        
        # Main application files
        if 'main' in file_path_lower or 'app' in file_path_lower:
            return 0.8
        
        # Source files vs test files
        if 'test' in file_path_lower or 'spec' in file_path_lower:
            return 0.3
        
        return 0.5
    
    def _calculate_dependency_factor(self, file_info: FileInfo, project_info: ProjectInfo) -> float:
        """Calculate dependency importance factor."""
        # Entry points get highest priority
        if file_info.path in project_info.entry_points:
            return 1.0
        
        # Files with many imports/exports are likely important
        if hasattr(file_info, 'imports') and file_info.imports:
            import_count = len(file_info.imports)
            return min(1.0, import_count / 10)  # Normalize to 10 imports
        
        return 0.5
