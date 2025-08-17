"""
Main audit engine that orchestrates the complete audit workflow.

This module provides the main audit engine that coordinates:
- Session management
- Analysis orchestration
- Result aggregation
- Report generation
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from ..core.models import ProjectInfo
from ..analysis.project_analyzer import ProjectAnalyzer
from ..analysis.code_retrieval import CodeRetriever
from ..analysis.context_manager import ContextManager
from ..analysis.cache_manager import CacheManager, CacheType
from ..analysis.coverage_tracker import CoverageTracker
from ..analysis.task_matrix import TaskMatrix, AnalysisTask, TaskType
from ..analysis.coverage_reporter import CoverageReporter
from ..llm.manager import LLMManager
from ..llm.base import LLMModelType
from ..llm.prompts import PromptManager
from ..templates.advanced_templates import AdvancedTemplateManager
# from ..database.services import DatabaseService  # Optional database integration

from .session_manager import AuditSessionManager, AuditSession, SessionConfig, SessionStatus
from .orchestrator import AnalysisOrchestrator, OrchestrationConfig
from .aggregator import ResultAggregator, AuditResult
from .report_generator import ReportGenerator, ReportFormat, ReportConfig

logger = logging.getLogger(__name__)


class AuditEngine:
    """Main audit engine for coordinating complete audit workflows."""
    
    def __init__(
        self,
        llm_manager: Optional[LLMManager] = None,
        db_session: Optional[Any] = None,
        project_analyzer: Optional[ProjectAnalyzer] = None,
        enable_caching: bool = True,
        cache_dir: Optional[str] = None
    ):
        """Initialize audit engine."""
        self.llm_manager = llm_manager or LLMManager()
        self.db_session = db_session
        self.project_analyzer = project_analyzer or ProjectAnalyzer()

        # Initialize advanced components
        self.code_retriever: Optional[CodeRetriever] = None
        self.context_manager: Optional[ContextManager] = None
        self.cache_manager: Optional[CacheManager] = None
        self.coverage_tracker: Optional[CoverageTracker] = None
        self.task_matrix: Optional[TaskMatrix] = None
        self.coverage_reporter: Optional[CoverageReporter] = None
        self.advanced_templates = AdvancedTemplateManager()

        # Initialize core components
        self.session_manager = AuditSessionManager(db_session)
        self.prompt_manager = PromptManager()
        self.orchestrator = AnalysisOrchestrator(self.llm_manager, self.prompt_manager)
        self.aggregator = ResultAggregator()
        self.report_generator = ReportGenerator()

        # Configuration
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir

        # State
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the audit engine."""
        if self.is_initialized:
            return
        
        try:
            # LLM manager is already initialized in constructor
            # Just validate providers
            validation_results = await self.llm_manager.validate_providers()
            valid_providers = [name for name, valid in validation_results.items() if valid]

            if not valid_providers:
                logger.warning("No valid LLM providers found, but continuing...")
            else:
                logger.info(f"Valid LLM providers: {', '.join(valid_providers)}")

            # Start session manager cleanup task
            await self.session_manager.start_cleanup_task()

            # Start orchestrator
            await self.orchestrator.start()

            self.is_initialized = True
            logger.info("Audit engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize audit engine: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the audit engine."""
        if not self.is_initialized:
            return
        
        try:
            # Stop orchestrator
            await self.orchestrator.stop()
            
            # Stop session manager cleanup
            await self.session_manager.stop_cleanup_task()
            
            # Close LLM manager
            await self.llm_manager.close()
            
            self.is_initialized = False
            logger.info("Audit engine shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during audit engine shutdown: {e}")
    
    async def start_audit(
        self,
        project_path: str,
        template: str = "security_audit",
        model: Optional[LLMModelType] = None,
        max_files: int = 50,
        session_config: Optional[SessionConfig] = None,
        progress_callback: Optional[Callable] = None,
        use_advanced_context: bool = True,
        use_caching: bool = True
    ) -> str:
        """Start a new audit session."""
        if not self.is_initialized:
            await self.initialize()
        
        logger.info(f"Starting audit for project: {project_path}")
        
        try:
            # Analyze project structure
            project_info = await self.project_analyzer.analyze_project(project_path)

            # Initialize advanced components with project info
            if use_advanced_context:
                self.code_retriever = CodeRetriever(project_info)
                self.context_manager = ContextManager(project_info, self.code_retriever)

            if use_caching and self.enable_caching:
                self.cache_manager = CacheManager(self.cache_dir)

            # Initialize coverage tracking
            self.coverage_tracker = CoverageTracker(project_info)
            self.task_matrix = TaskMatrix()
            self.coverage_reporter = CoverageReporter(self.coverage_tracker)

            # Create session configuration
            if session_config is None:
                session_config = SessionConfig(
                    max_files=max_files,
                    max_concurrent_tasks=3,
                    timeout_minutes=60
                )

            # Create audit session
            session = await self.session_manager.create_session(
                project_path=project_path,
                project_info=project_info,
                config=session_config
            )
            
            # Register progress callback
            if progress_callback:
                self.session_manager.register_progress_callback(
                    session.session_id, progress_callback
                )
            
            # Start analysis in background
            asyncio.create_task(self._run_audit_workflow(session, template, model))
            
            logger.info(f"Audit session {session.session_id} started")
            return session.session_id
            
        except Exception as e:
            logger.error(f"Failed to start audit: {e}")
            raise
    
    async def get_audit_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get audit session status."""
        session = await self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'status': session.status.value,
            'progress': {
                'total_files': session.progress.total_files,
                'analyzed_files': session.progress.analyzed_files,
                'failed_files': session.progress.failed_files,
                'completion_percentage': session.progress.completion_percentage,
                'current_file': session.progress.current_file,
                'estimated_completion': session.progress.estimated_completion.isoformat() if session.progress.estimated_completion else None,
            },
            'statistics': {
                'total_results': len(session.results),
                'total_errors': len(session.errors),
                'success_rate': session.progress.success_rate,
            },
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
        }
    
    async def get_audit_results(self, session_id: str) -> Optional[AuditResult]:
        """Get aggregated audit results."""
        session = await self.session_manager.get_session(session_id)
        if not session:
            return None
        
        if session.status != SessionStatus.COMPLETED:
            return None
        
        # Aggregate results
        audit_result = await self.aggregator.aggregate_results(
            session_id=session.session_id,
            project_path=session.project_path,
            project_name=session.project_info.name,
            raw_results=session.results
        )
        
        return audit_result
    
    async def generate_report(
        self,
        session_id: str,
        format: ReportFormat,
        output_path: Optional[str] = None,
        config: Optional[ReportConfig] = None
    ) -> Optional[str]:
        """Generate audit report."""
        audit_result = await self.get_audit_results(session_id)
        if not audit_result:
            return None
        
        # Configure report generator
        if config:
            self.report_generator.config = config
        
        # Generate report
        report = await self.report_generator.generate_report(
            audit_result=audit_result,
            format=format,
            output_path=output_path
        )
        
        return report.content
    
    async def cancel_audit(self, session_id: str) -> bool:
        """Cancel running audit session."""
        return await self.session_manager.cancel_session(session_id)
    
    async def list_active_audits(self) -> List[Dict[str, Any]]:
        """List all active audit sessions."""
        sessions = await self.session_manager.list_active_sessions()

        return [
            {
                'session_id': session.session_id,
                'project_name': session.project_info.name,
                'project_path': session.project_path,
                'status': session.status.value,
                'progress': session.progress.completion_percentage,
                'created_at': session.created_at.isoformat(),
            }
            for session in sessions
        ]

    async def generate_coverage_report(
        self,
        output_path: str,
        format: str = "html"
    ) -> Optional[str]:
        """Generate coverage analysis report."""
        if not self.coverage_reporter:
            logger.warning("Coverage reporter not initialized")
            return None

        try:
            if format.lower() == "html":
                return self.coverage_reporter.generate_html_report(output_path)
            elif format.lower() == "json":
                self.coverage_reporter.generate_json_report(output_path)
                return f"JSON coverage report generated: {output_path}"
            elif format.lower() == "markdown":
                return self.coverage_reporter.generate_markdown_report(output_path)
            else:
                logger.error(f"Unsupported coverage report format: {format}")
                return None

        except Exception as e:
            logger.error(f"Failed to generate coverage report: {e}")
            return None

    def get_coverage_stats(self) -> Optional[Dict[str, Any]]:
        """Get current coverage statistics."""
        if not self.coverage_tracker:
            return None

        stats = self.coverage_tracker.get_coverage_stats()
        return {
            'total_units': stats.total_units,
            'analyzed_units': stats.analyzed_units,
            'pending_units': stats.pending_units,
            'skipped_units': stats.skipped_units,
            'failed_units': stats.failed_units,
            'coverage_percentage': stats.coverage_percentage,
            'success_rate': stats.success_rate,
        }
    
    async def _run_audit_workflow(
        self,
        session: AuditSession,
        template: str,
        model: Optional[LLMModelType]
    ):
        """Run the complete audit workflow."""
        try:
            # Update session status
            await self.session_manager.update_session_status(
                session.session_id, SessionStatus.INITIALIZING
            )
            
            # Select files for analysis
            files_to_analyze = self._select_files_for_analysis(
                session.project_info.files,
                session.config.max_files
            )
            
            # Update progress
            await self.session_manager.update_session_progress(
                session.session_id,
                analyzed_files=0,
                failed_files=0
            )
            
            # Start analysis
            await self.session_manager.update_session_status(
                session.session_id, SessionStatus.RUNNING
            )
            
            # Schedule analysis tasks
            task_ids = await self.orchestrator.schedule_analysis(
                session=session,
                files=files_to_analyze,
                template=template,
                model=model
            )
            
            # Monitor progress
            await self._monitor_analysis_progress(session, task_ids)
            
            # Complete session
            await self.session_manager.update_session_status(
                session.session_id, SessionStatus.COMPLETED
            )
            
            logger.info(f"Audit workflow completed for session {session.session_id}")
            
        except Exception as e:
            logger.error(f"Audit workflow failed for session {session.session_id}: {e}")
            
            await self.session_manager.add_session_error(
                session.session_id, str(e)
            )
            await self.session_manager.update_session_status(
                session.session_id, SessionStatus.FAILED
            )
    
    async def _monitor_analysis_progress(self, session: AuditSession, task_ids: List[str]):
        """Monitor analysis progress and update session."""
        completed_tasks = 0
        failed_tasks = 0
        
        while completed_tasks + failed_tasks < len(task_ids):
            await asyncio.sleep(2)  # Check every 2 seconds
            
            # Check task statuses
            new_completed = 0
            new_failed = 0
            current_file = None
            
            for task_id in task_ids:
                task = await self.orchestrator.get_task_status(task_id)
                if not task:
                    continue
                
                if task.status.value == "completed":
                    new_completed += 1
                    # Add result to session
                    if task.result:
                        await self.session_manager.add_session_result(
                            session.session_id, task.result
                        )
                elif task.status.value == "failed":
                    new_failed += 1
                    # Add error to session
                    if task.error:
                        await self.session_manager.add_session_error(
                            session.session_id, f"Task {task_id}: {task.error}"
                        )
                elif task.status.value == "running":
                    current_file = task.file_info.path
            
            # Update progress if changed
            if new_completed != completed_tasks or new_failed != failed_tasks:
                completed_tasks = new_completed
                failed_tasks = new_failed
                
                await self.session_manager.update_session_progress(
                    session.session_id,
                    analyzed_files=completed_tasks,
                    failed_files=failed_tasks,
                    current_file=current_file
                )
    
    def _select_files_for_analysis(self, all_files: List, max_files: int) -> List:
        """Select files for analysis based on priority."""
        # Filter files that should be analyzed
        analyzable_files = [
            f for f in all_files
            if f.language and f.size < 500000  # Skip very large files
        ]
        
        # Sort by priority (security-critical files first)
        def file_priority(file_info):
            path_lower = file_info.path.lower()
            
            # Security-critical patterns
            if any(pattern in path_lower for pattern in [
                'auth', 'login', 'password', 'token', 'session',
                'admin', 'config', 'database', 'api'
            ]):
                return 0  # Highest priority
            
            # Main application files
            if any(pattern in path_lower for pattern in ['main', 'app', 'index']):
                return 1
            
            # Source files
            if not any(pattern in path_lower for pattern in ['test', 'spec', 'mock']):
                return 2
            
            # Test files (lowest priority)
            return 3
        
        analyzable_files.sort(key=file_priority)
        
        # Limit to max_files
        return analyzable_files[:max_files]
