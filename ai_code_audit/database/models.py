"""
SQLAlchemy ORM models for AI Code Audit System.

This module defines the database schema using SQLAlchemy ORM models
with support for async operations.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, DateTime, Enum, JSON,
    Numeric, ForeignKey, Boolean, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import CHAR

from ai_code_audit.core.models import ProjectType, SeverityLevel, VulnerabilityType

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Project(Base):
    """Project table for storing project information."""
    
    __tablename__ = 'projects'
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    path = Column(Text, nullable=False)
    project_type = Column(Enum(ProjectType), default=ProjectType.UNKNOWN, nullable=False)
    languages = Column(JSON, default=lambda: [])
    architecture_pattern = Column(String(100))
    total_files = Column(Integer, default=0, nullable=False)
    total_lines = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_scanned_at = Column(DateTime)
    
    # Relationships
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="project", cascade="all, delete-orphan")
    audit_sessions = relationship("AuditSession", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_name', 'name'),
        Index('idx_project_created_at', 'created_at'),
        Index('idx_project_type', 'project_type'),
    )
    
    def __repr__(self) -> str:
        return f"<Project(id='{self.id}', name='{self.name}', type='{self.project_type}')>"


class File(Base):
    """File table for storing source file information."""
    
    __tablename__ = 'files'
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    project_id = Column(CHAR(36), ForeignKey('projects.id'), nullable=False)
    path = Column(Text, nullable=False)
    absolute_path = Column(Text, nullable=False)
    language = Column(String(50))
    size = Column(BigInteger, default=0)
    hash = Column(String(64))
    last_modified = Column(DateTime)
    functions = Column(JSON)
    classes = Column(JSON)
    imports = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="files")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_project_id', 'project_id'),
        Index('idx_file_language', 'language'),
        Index('idx_file_hash', 'hash'),
    )
    
    def __repr__(self) -> str:
        return f"<File(id='{self.id}', path='{self.path}', language='{self.language}')>"


class Module(Base):
    """Module table for storing functional module information."""
    
    __tablename__ = 'modules'
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    project_id = Column(CHAR(36), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    business_logic = Column(Text)
    risk_level = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    files = Column(JSON)
    entry_points = Column(JSON)
    dependencies = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="modules")
    audit_sessions = relationship("AuditSession", back_populates="module")
    security_findings = relationship("SecurityFinding", back_populates="module")
    
    # Indexes
    __table_args__ = (
        Index('idx_module_project_id', 'project_id'),
        Index('idx_module_risk_level', 'risk_level'),
        Index('idx_module_name', 'name'),
    )
    
    def __repr__(self) -> str:
        return f"<Module(id='{self.id}', name='{self.name}', risk_level='{self.risk_level}')>"


class AuditSession(Base):
    """Audit session table for tracking audit executions."""

    __tablename__ = 'audit_sessions'

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    project_id = Column(CHAR(36), ForeignKey('projects.id'), nullable=False)
    module_id = Column(CHAR(36), ForeignKey('modules.id'))
    llm_model = Column(String(50), nullable=False)  # Renamed from model_used to avoid Pydantic conflict
    status = Column(Enum('pending', 'running', 'completed', 'failed', 'cancelled'), default='pending')
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    duration = Column(Integer, default=0, nullable=False)  # Duration in seconds
    total_findings = Column(Integer, default=0, nullable=False)
    critical_findings = Column(Integer, default=0, nullable=False)
    high_findings = Column(Integer, default=0, nullable=False)
    medium_findings = Column(Integer, default=0, nullable=False)
    low_findings = Column(Integer, default=0, nullable=False)
    config = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="audit_sessions")
    module = relationship("Module", back_populates="audit_sessions")
    security_findings = relationship("SecurityFinding", back_populates="session", cascade="all, delete-orphan")
    audit_reports = relationship("AuditReport", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_session_project_id', 'project_id'),
        Index('idx_audit_session_status', 'status'),
        Index('idx_audit_session_start_time', 'start_time'),
        Index('idx_audit_session_model', 'llm_model'),
    )
    
    def __repr__(self) -> str:
        return f"<AuditSession(id='{self.id}', status='{self.status}', model='{self.llm_model}')>"


class SecurityFinding(Base):
    """Security finding table for storing discovered vulnerabilities."""
    
    __tablename__ = 'security_findings'
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    session_id = Column(CHAR(36), ForeignKey('audit_sessions.id'), nullable=False)
    project_id = Column(CHAR(36), ForeignKey('projects.id'), nullable=False)
    module_id = Column(CHAR(36), ForeignKey('modules.id'))
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer)
    vulnerability_type = Column(Enum(VulnerabilityType), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    code_snippet = Column(Text)
    recommendation = Column(Text)
    confidence = Column(Numeric(3, 2), default=0.00)
    cwe_id = Column(String(20))
    owasp_category = Column(String(100))
    status = Column(Enum('open', 'fixed', 'false_positive', 'accepted_risk'), default='open')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    session = relationship("AuditSession", back_populates="security_findings")
    project = relationship("Project")
    module = relationship("Module", back_populates="security_findings")
    
    # Indexes
    __table_args__ = (
        Index('idx_finding_session_id', 'session_id'),
        Index('idx_finding_project_id', 'project_id'),
        Index('idx_finding_severity', 'severity'),
        Index('idx_finding_vulnerability_type', 'vulnerability_type'),
        Index('idx_finding_status', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<SecurityFinding(id='{self.id}', type='{self.vulnerability_type}', severity='{self.severity}')>"


class AuditReport(Base):
    """Audit report table for storing generated reports."""
    
    __tablename__ = 'audit_reports'
    
    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    session_id = Column(CHAR(36), ForeignKey('audit_sessions.id'), nullable=False)
    project_id = Column(CHAR(36), ForeignKey('projects.id'), nullable=False)
    report_type = Column(Enum('module', 'project', 'comprehensive'), default='module')
    format = Column(Enum('json', 'html', 'pdf', 'markdown'), default='json')
    title = Column(String(500))
    summary = Column(Text)
    content = Column(Text)  # Large text content
    file_path = Column(Text)
    file_size = Column(BigInteger, default=0)
    generated_at = Column(DateTime, default=func.now())
    
    # Relationships
    session = relationship("AuditSession", back_populates="audit_reports")
    project = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index('idx_report_session_id', 'session_id'),
        Index('idx_report_project_id', 'project_id'),
        Index('idx_report_type', 'report_type'),
        Index('idx_report_format', 'format'),
    )
    
    def __repr__(self) -> str:
        return f"<AuditReport(id='{self.id}', type='{self.report_type}', format='{self.format}')>"


class CacheEntry(Base):
    """Cache entry table for storing temporary data."""

    __tablename__ = 'cache_entries'

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    cache_key = Column(String(255), unique=True, nullable=False)
    cache_type = Column(Enum('project_analysis', 'code_snippet', 'llm_response', 'file_hash'), nullable=False)
    content = Column(Text)
    cache_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    accessed_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_key', 'cache_key'),
        Index('idx_cache_type', 'cache_type'),
        Index('idx_cache_expires_at', 'expires_at'),
        Index('idx_cache_accessed_at', 'accessed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<CacheEntry(id='{self.id}', key='{self.cache_key}', type='{self.cache_type}')>"
