"""
Database service layer for AI Code Audit System.

This module provides high-level database operations and business logic
for interacting with the database models.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ai_code_audit.core.models import ProjectType, SeverityLevel, VulnerabilityType
from ai_code_audit.core.exceptions import DatabaseError, ValidationError
from ai_code_audit.database.models import (
    Project, File, Module, AuditSession, SecurityFinding, AuditReport, CacheEntry
)


class ProjectService:
    """Service for project-related database operations."""
    
    @staticmethod
    async def create_project(
        session: AsyncSession,
        name: str,
        path: str,
        project_type: ProjectType = ProjectType.UNKNOWN,
        languages: Optional[List[str]] = None,
        architecture_pattern: Optional[str] = None,
    ) -> Project:
        """Create a new project."""
        try:
            project = Project(
                name=name,
                path=path,
                project_type=project_type,
                languages=languages or [],
                architecture_pattern=architecture_pattern,
            )
            
            session.add(project)
            await session.flush()  # Get the ID without committing
            await session.refresh(project)
            
            return project
            
        except Exception as e:
            raise DatabaseError(f"Failed to create project: {e}")
    
    @staticmethod
    async def get_project_by_id(session: AsyncSession, project_id: str) -> Optional[Project]:
        """Get project by ID with related data."""
        try:
            stmt = (
                select(Project)
                .options(
                    selectinload(Project.files),
                    selectinload(Project.modules),
                    selectinload(Project.audit_sessions),
                )
                .where(Project.id == project_id)
            )
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise DatabaseError(f"Failed to get project: {e}")
    
    @staticmethod
    async def get_project_by_path(session: AsyncSession, path: str) -> Optional[Project]:
        """Get project by path."""
        try:
            stmt = select(Project).where(Project.path == path)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise DatabaseError(f"Failed to get project by path: {e}")
    
    @staticmethod
    async def list_projects(
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        """List all projects with pagination."""
        try:
            stmt = (
                select(Project)
                .order_by(Project.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            raise DatabaseError(f"Failed to list projects: {e}")
    
    @staticmethod
    async def update_project_stats(
        session: AsyncSession,
        project_id: str,
        total_files: int,
        total_lines: int,
    ) -> None:
        """Update project statistics."""
        try:
            stmt = (
                update(Project)
                .where(Project.id == project_id)
                .values(
                    total_files=total_files,
                    total_lines=total_lines,
                    last_scanned_at=datetime.now(),
                )
            )
            
            await session.execute(stmt)
            
        except Exception as e:
            raise DatabaseError(f"Failed to update project stats: {e}")


class FileService:
    """Service for file-related database operations."""
    
    @staticmethod
    async def create_file(
        session: AsyncSession,
        project_id: str,
        path: str,
        absolute_path: str,
        language: Optional[str] = None,
        size: int = 0,
        hash: Optional[str] = None,
        last_modified: Optional[datetime] = None,
        functions: Optional[List[str]] = None,
        classes: Optional[List[str]] = None,
        imports: Optional[List[str]] = None,
    ) -> File:
        """Create a new file record."""
        try:
            file_obj = File(
                project_id=project_id,
                path=path,
                absolute_path=absolute_path,
                language=language,
                size=size,
                hash=hash,
                last_modified=last_modified,
                functions=functions or [],
                classes=classes or [],
                imports=imports or [],
            )
            
            session.add(file_obj)
            await session.flush()
            await session.refresh(file_obj)
            
            return file_obj
            
        except Exception as e:
            raise DatabaseError(f"Failed to create file: {e}")
    
    @staticmethod
    async def get_files_by_project(
        session: AsyncSession,
        project_id: str,
        language: Optional[str] = None,
    ) -> List[File]:
        """Get all files for a project, optionally filtered by language."""
        try:
            stmt = select(File).where(File.project_id == project_id)
            
            if language:
                stmt = stmt.where(File.language == language)
            
            stmt = stmt.order_by(File.path)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            raise DatabaseError(f"Failed to get files: {e}")
    
    @staticmethod
    async def update_file_hash(
        session: AsyncSession,
        file_id: str,
        new_hash: str,
        last_modified: datetime,
    ) -> None:
        """Update file hash and modification time."""
        try:
            stmt = (
                update(File)
                .where(File.id == file_id)
                .values(hash=new_hash, last_modified=last_modified)
            )
            
            await session.execute(stmt)
            
        except Exception as e:
            raise DatabaseError(f"Failed to update file hash: {e}")


class AuditSessionService:
    """Service for audit session operations."""
    
    @staticmethod
    async def create_audit_session(
        session: AsyncSession,
        project_id: str,
        llm_model: str,
        module_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AuditSession:
        """Create a new audit session."""
        try:
            audit_session = AuditSession(
                project_id=project_id,
                module_id=module_id,
                llm_model=llm_model,
                config=config or {},
                status='pending',
            )
            
            session.add(audit_session)
            await session.flush()
            await session.refresh(audit_session)
            
            return audit_session
            
        except Exception as e:
            raise DatabaseError(f"Failed to create audit session: {e}")
    
    @staticmethod
    async def update_session_status(
        session: AsyncSession,
        session_id: str,
        status: str,
        end_time: Optional[datetime] = None,
    ) -> None:
        """Update audit session status."""
        try:
            values = {"status": status}
            if end_time:
                values["end_time"] = end_time
            
            stmt = (
                update(AuditSession)
                .where(AuditSession.id == session_id)
                .values(**values)
            )
            
            await session.execute(stmt)
            
        except Exception as e:
            raise DatabaseError(f"Failed to update session status: {e}")
    
    @staticmethod
    async def get_session_with_findings(
        session: AsyncSession,
        session_id: str,
    ) -> Optional[AuditSession]:
        """Get audit session with all findings."""
        try:
            stmt = (
                select(AuditSession)
                .options(selectinload(AuditSession.security_findings))
                .where(AuditSession.id == session_id)
            )
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise DatabaseError(f"Failed to get session with findings: {e}")


class SecurityFindingService:
    """Service for security finding operations."""
    
    @staticmethod
    async def create_finding(
        session: AsyncSession,
        session_id: str,
        project_id: str,
        vulnerability_type: VulnerabilityType,
        severity: SeverityLevel,
        title: str,
        description: str,
        file_path: str,
        module_id: Optional[str] = None,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        recommendation: Optional[str] = None,
        confidence: float = 0.0,
        cwe_id: Optional[str] = None,
        owasp_category: Optional[str] = None,
    ) -> SecurityFinding:
        """Create a new security finding."""
        try:
            finding = SecurityFinding(
                session_id=session_id,
                project_id=project_id,
                module_id=module_id,
                file_path=file_path,
                line_number=line_number,
                vulnerability_type=vulnerability_type,
                severity=severity,
                title=title,
                description=description,
                code_snippet=code_snippet,
                recommendation=recommendation,
                confidence=confidence,
                cwe_id=cwe_id,
                owasp_category=owasp_category,
            )
            
            session.add(finding)
            await session.flush()
            await session.refresh(finding)
            
            return finding
            
        except Exception as e:
            raise DatabaseError(f"Failed to create security finding: {e}")
    
    @staticmethod
    async def get_findings_by_project(
        session: AsyncSession,
        project_id: str,
        severity: Optional[SeverityLevel] = None,
        status: Optional[str] = None,
    ) -> List[SecurityFinding]:
        """Get all findings for a project with optional filters."""
        try:
            stmt = select(SecurityFinding).where(SecurityFinding.project_id == project_id)
            
            if severity:
                stmt = stmt.where(SecurityFinding.severity == severity)
            
            if status:
                stmt = stmt.where(SecurityFinding.status == status)
            
            stmt = stmt.order_by(
                SecurityFinding.severity.desc(),
                SecurityFinding.confidence.desc(),
            )
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            raise DatabaseError(f"Failed to get findings: {e}")
    
    @staticmethod
    async def get_findings_summary(
        session: AsyncSession,
        project_id: str,
    ) -> Dict[str, int]:
        """Get summary of findings by severity."""
        try:
            stmt = (
                select(
                    SecurityFinding.severity,
                    func.count(SecurityFinding.id).label('count')
                )
                .where(SecurityFinding.project_id == project_id)
                .where(SecurityFinding.status == 'open')
                .group_by(SecurityFinding.severity)
            )
            
            result = await session.execute(stmt)
            summary = {severity.value: 0 for severity in SeverityLevel}
            
            for row in result:
                summary[row.severity.value] = row.count
            
            return summary
            
        except Exception as e:
            raise DatabaseError(f"Failed to get findings summary: {e}")


class CacheService:
    """Service for cache operations."""
    
    @staticmethod
    async def set_cache(
        session: AsyncSession,
        key: str,
        cache_type: str,
        content: str,
        cache_metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> CacheEntry:
        """Set a cache entry."""
        try:
            # Delete existing entry with same key
            await session.execute(
                delete(CacheEntry).where(CacheEntry.cache_key == key)
            )

            cache_entry = CacheEntry(
                cache_key=key,
                cache_type=cache_type,
                content=content,
                cache_metadata=cache_metadata or {},
                expires_at=expires_at,
            )
            
            session.add(cache_entry)
            await session.flush()
            await session.refresh(cache_entry)
            
            return cache_entry
            
        except Exception as e:
            raise DatabaseError(f"Failed to set cache: {e}")
    
    @staticmethod
    async def get_cache(session: AsyncSession, key: str) -> Optional[CacheEntry]:
        """Get a cache entry by key."""
        try:
            stmt = select(CacheEntry).where(CacheEntry.cache_key == key)
            
            # Check if not expired
            now = datetime.now()
            stmt = stmt.where(
                (CacheEntry.expires_at.is_(None)) | (CacheEntry.expires_at > now)
            )
            
            result = await session.execute(stmt)
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                # Update access time
                await session.execute(
                    update(CacheEntry)
                    .where(CacheEntry.id == cache_entry.id)
                    .values(accessed_at=now)
                )
            
            return cache_entry
            
        except Exception as e:
            raise DatabaseError(f"Failed to get cache: {e}")
    
    @staticmethod
    async def clear_expired_cache(session: AsyncSession) -> int:
        """Clear expired cache entries."""
        try:
            now = datetime.now()
            stmt = delete(CacheEntry).where(
                CacheEntry.expires_at.is_not(None),
                CacheEntry.expires_at <= now
            )
            
            result = await session.execute(stmt)
            return result.rowcount
            
        except Exception as e:
            raise DatabaseError(f"Failed to clear expired cache: {e}")
