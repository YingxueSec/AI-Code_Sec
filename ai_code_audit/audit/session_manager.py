"""
Audit session manager for managing audit lifecycles.

This module provides session management capabilities including:
- Session creation and initialization
- State tracking and progress monitoring
- Resource management and cleanup
- Session persistence and recovery
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import logging

from ..core.models import ProjectInfo, FileInfo
from ..database.models import AuditSession as DBSession
from ..database.services import AuditSessionService

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Audit session status enumeration."""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SessionConfig:
    """Configuration for audit session."""
    max_files: int = 50
    max_concurrent_tasks: int = 3
    timeout_minutes: int = 60
    retry_attempts: int = 3
    save_intermediate_results: bool = True
    enable_progress_callbacks: bool = True


@dataclass
class SessionProgress:
    """Progress tracking for audit session."""
    total_files: int = 0
    analyzed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    current_file: Optional[str] = None
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.analyzed_files + self.failed_files + self.skipped_files) / self.total_files * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        processed = self.analyzed_files + self.failed_files
        if processed == 0:
            return 0.0
        return self.analyzed_files / processed * 100


@dataclass
class AuditSession:
    """Audit session data structure."""
    session_id: str
    project_path: str
    project_info: ProjectInfo
    config: SessionConfig
    status: SessionStatus = SessionStatus.CREATED
    progress: SessionProgress = field(default_factory=SessionProgress)
    results: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_status(self, status: SessionStatus, message: Optional[str] = None):
        """Update session status."""
        self.status = status
        self.updated_at = datetime.now()
        if message:
            self.metadata['last_status_message'] = message
        logger.info(f"Session {self.session_id} status updated to {status.value}")


class AuditSessionManager:
    """Manager for audit sessions."""
    
    def __init__(self, db_session: Optional[Any] = None):
        """Initialize session manager."""
        self.db_session = db_session
        self.active_sessions: Dict[str, AuditSession] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def create_session(
        self,
        project_path: str,
        project_info: ProjectInfo,
        config: Optional[SessionConfig] = None
    ) -> AuditSession:
        """Create a new audit session."""
        session_id = str(uuid.uuid4())
        
        if config is None:
            config = SessionConfig()
        
        session = AuditSession(
            session_id=session_id,
            project_path=project_path,
            project_info=project_info,
            config=config
        )
        
        # Initialize progress
        session.progress.total_files = len([
            f for f in project_info.files 
            if f.language and len([f for f in project_info.files]) <= config.max_files
        ])
        session.progress.start_time = datetime.now()
        
        # Estimate completion time (rough estimate: 30 seconds per file)
        estimated_duration = timedelta(seconds=session.progress.total_files * 30)
        session.progress.estimated_completion = session.progress.start_time + estimated_duration
        
        # Store in active sessions
        self.active_sessions[session_id] = session
        
        # Save to database if available
        if self.db_session:
            await self._save_session_to_db(session)
        
        logger.info(f"Created audit session {session_id} for project {project_path}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[AuditSession]:
        """Get audit session by ID."""
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from database
        if self.db_session:
            return await self._load_session_from_db(session_id)
        
        return None
    
    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        message: Optional[str] = None
    ) -> bool:
        """Update session status."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.update_status(status, message)
        
        # Save to database
        if self.db_session:
            await self._save_session_to_db(session)
        
        # Notify progress callbacks
        await self._notify_progress_callbacks(session_id, session)
        
        return True
    
    async def update_session_progress(
        self,
        session_id: str,
        analyzed_files: Optional[int] = None,
        failed_files: Optional[int] = None,
        skipped_files: Optional[int] = None,
        current_file: Optional[str] = None
    ) -> bool:
        """Update session progress."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        if analyzed_files is not None:
            session.progress.analyzed_files = analyzed_files
        if failed_files is not None:
            session.progress.failed_files = failed_files
        if skipped_files is not None:
            session.progress.skipped_files = skipped_files
        if current_file is not None:
            session.progress.current_file = current_file
        
        session.updated_at = datetime.now()
        
        # Update estimated completion
        if session.progress.analyzed_files > 0:
            elapsed = datetime.now() - session.progress.start_time
            avg_time_per_file = elapsed / session.progress.analyzed_files
            remaining_files = session.progress.total_files - session.progress.analyzed_files
            session.progress.estimated_completion = datetime.now() + (avg_time_per_file * remaining_files)
        
        # Save to database
        if self.db_session:
            await self._save_session_to_db(session)

        # Notify progress callbacks
        await self._notify_progress_callbacks(session_id, session)

        return True

    async def add_session_result(self, session_id: str, result: Any) -> bool:
        """Add result to session."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.results.append(result)
        session.updated_at = datetime.now()

        # Save to database if configured
        if self.db_session and session.config.save_intermediate_results:
            await self._save_session_to_db(session)

        return True

    async def add_session_error(self, session_id: str, error: str) -> bool:
        """Add error to session."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.errors.append(error)
        session.updated_at = datetime.now()

        logger.warning(f"Session {session_id} error: {error}")

        # Save to database
        if self.db_session:
            await self._save_session_to_db(session)
        
        return True
    
    def register_progress_callback(self, session_id: str, callback: Callable):
        """Register progress callback for session."""
        if session_id not in self.progress_callbacks:
            self.progress_callbacks[session_id] = []
        self.progress_callbacks[session_id].append(callback)
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up session resources."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Update status to completed/cancelled
            if session.status == SessionStatus.RUNNING:
                session.update_status(SessionStatus.COMPLETED)
            
            # Final save to database
            if self.db_session:
                await self._save_session_to_db(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Clean up callbacks
            if session_id in self.progress_callbacks:
                del self.progress_callbacks[session_id]
            
            logger.info(f"Cleaned up session {session_id}")
            return True
        
        return False
    
    async def list_active_sessions(self) -> List[AuditSession]:
        """List all active sessions."""
        return list(self.active_sessions.values())
    
    async def cancel_session(self, session_id: str) -> bool:
        """Cancel running session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        if session.status in [SessionStatus.RUNNING, SessionStatus.PAUSED]:
            await self.update_session_status(session_id, SessionStatus.CANCELLED)
            await self.cleanup_session(session_id)
            return True
        
        return False
    
    async def _save_session_to_db(self, session: AuditSession):
        """Save session to database."""
        if not self.db_session:
            return

        try:
            # Convert to database model
            db_session = DBSession(
                session_id=session.session_id,
                project_path=session.project_path,
                project_name=session.project_info.name,
                status=session.status.value,
                progress_data={
                    'total_files': session.progress.total_files,
                    'analyzed_files': session.progress.analyzed_files,
                    'failed_files': session.progress.failed_files,
                    'completion_percentage': session.progress.completion_percentage,
                },
                config_data=session.config.__dict__,
                metadata=session.metadata,
                created_at=session.created_at,
                updated_at=session.updated_at
            )

            # Use AuditSessionService to save
            from ..database.services import AuditSessionService
            await AuditSessionService.create_audit_session(self.db_session, **db_session.__dict__)

        except Exception as e:
            logger.error(f"Failed to save session {session.session_id} to database: {e}")

    async def _load_session_from_db(self, session_id: str) -> Optional[AuditSession]:
        """Load session from database."""
        if not self.db_session:
            return None

        try:
            # Use AuditSessionService to load
            from ..database.services import AuditSessionService
            db_session = await AuditSessionService.get_audit_session(self.db_session, session_id)
            if not db_session:
                return None

            # Convert from database model (simplified)
            # In a real implementation, you'd need to reconstruct the full session
            logger.info(f"Loaded session {session_id} from database")
            return None  # Placeholder - implement full conversion

        except Exception as e:
            logger.error(f"Failed to load session {session_id} from database: {e}")
            return None
    
    async def _notify_progress_callbacks(self, session_id: str, session: AuditSession):
        """Notify progress callbacks."""
        if session_id not in self.progress_callbacks:
            return
        
        for callback in self.progress_callbacks[session_id]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(session)
                else:
                    callback(session)
            except Exception as e:
                logger.error(f"Progress callback error for session {session_id}: {e}")
    
    async def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Clean up old completed sessions
                current_time = datetime.now()
                sessions_to_cleanup = []
                
                for session_id, session in self.active_sessions.items():
                    if session.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED]:
                        # Clean up sessions older than 1 hour
                        if current_time - session.updated_at > timedelta(hours=1):
                            sessions_to_cleanup.append(session_id)
                
                for session_id in sessions_to_cleanup:
                    await self.cleanup_session(session_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
