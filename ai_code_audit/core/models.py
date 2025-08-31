"""
Core data models for the AI Code Audit System.

This module defines all the primary data structures used throughout
the application using Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from pydantic import BaseModel, Field, validator, root_validator


class ProjectType(str, Enum):
    """Enumeration of supported project types."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DESKTOP_APPLICATION = "desktop_application"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    """Enumeration of security finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(str, Enum):
    """Enumeration of vulnerability types."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATA_VALIDATION = "data_validation"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSECURE_CRYPTO = "insecure_crypto"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"
    BUFFER_OVERFLOW = "buffer_overflow"
    RACE_CONDITION = "race_condition"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class FileInfo(BaseModel):
    """Information about a source code file."""
    path: str = Field(..., description="Relative path from project root")
    absolute_path: str = Field(..., description="Absolute file path")
    language: Optional[str] = Field(None, description="Programming language")
    size: int = Field(0, description="File size in bytes")
    hash: Optional[str] = Field(None, description="File content hash")
    last_modified: Optional[datetime] = Field(None, description="Last modification time")
    functions: List[str] = Field(default_factory=list, description="Function names")
    classes: List[str] = Field(default_factory=list, description="Class names")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    
    @validator('path')
    def validate_path(cls, v: str) -> str:
        """Validate that path is not empty."""
        if not v.strip():
            raise ValueError("Path cannot be empty")
        return v.strip()
    
    @validator('size')
    def validate_size(cls, v: int) -> int:
        """Validate that size is non-negative."""
        if v < 0:
            raise ValueError("File size cannot be negative")
        return v


class DependencyInfo(BaseModel):
    """Information about a project dependency."""
    name: str = Field(..., description="Dependency name")
    version: Optional[str] = Field(None, description="Dependency version")
    source: str = Field(..., description="Package manager (npm, pip, etc.)")
    vulnerabilities: List[str] = Field(default_factory=list, description="Known vulnerabilities")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v.strip():
            raise ValueError("Dependency name cannot be empty")
        return v.strip()


class ProjectInfo(BaseModel):
    """Comprehensive information about a project."""
    path: str = Field(..., description="Project root path")
    name: str = Field(..., description="Project name")
    project_type: ProjectType = Field(ProjectType.UNKNOWN, description="Project type")
    files: List[FileInfo] = Field(default_factory=list, description="Source files")
    dependencies: List[DependencyInfo] = Field(default_factory=list, description="Dependencies")
    entry_points: List[str] = Field(default_factory=list, description="Entry point files")
    languages: List[str] = Field(default_factory=list, description="Programming languages used")
    architecture_pattern: Optional[str] = Field(None, description="Architecture pattern")
    total_lines: int = Field(0, description="Total lines of code")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()


class Module(BaseModel):
    """Information about a functional module within a project."""
    name: str = Field(..., description="Module name")
    description: str = Field("", description="Module description")
    files: List[str] = Field(default_factory=list, description="Files in this module")
    entry_points: List[str] = Field(default_factory=list, description="Module entry points")
    dependencies: List[str] = Field(default_factory=list, description="Module dependencies")
    business_logic: str = Field("", description="Business logic description")
    risk_level: SeverityLevel = Field(SeverityLevel.MEDIUM, description="Risk assessment")
    
    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v.strip():
            raise ValueError("Module name cannot be empty")
        return v.strip()


class SecurityFinding(BaseModel):
    """A security vulnerability or issue found during audit."""
    id: str = Field(..., description="Unique finding identifier")
    type: VulnerabilityType = Field(..., description="Vulnerability type")
    severity: SeverityLevel = Field(..., description="Severity level")
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Detailed description")
    file_path: str = Field(..., description="File where issue was found")
    line_number: Optional[int] = Field(None, description="Line number")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    recommendation: str = Field("", description="Fix recommendation")
    confidence: float = Field(0.0, description="Confidence score (0.0-1.0)")
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    owasp_category: Optional[str] = Field(None, description="OWASP category")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @validator('confidence')
    def validate_confidence(cls, v: float) -> float:
        """Validate that confidence is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v
    
    @validator('line_number')
    def validate_line_number(cls, v: Optional[int]) -> Optional[int]:
        """Validate that line number is positive."""
        if v is not None and v <= 0:
            raise ValueError("Line number must be positive")
        return v


class AuditResult(BaseModel):
    """Result of an audit session."""
    module: Module = Field(..., description="Audited module")
    findings: List[SecurityFinding] = Field(default_factory=list, description="Security findings")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Audit summary")
    recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    audit_timestamp: datetime = Field(default_factory=datetime.now, description="Audit timestamp")
    model_used: str = Field(..., description="LLM model used")
    session_id: str = Field(..., description="Audit session ID")
    confidence_score: float = Field(0.0, description="Overall confidence score")
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v: float) -> float:
        """Validate that confidence score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class CodeRequest(BaseModel):
    """Request for specific code to be analyzed."""
    file_pattern: str = Field(..., description="File path or pattern")
    reason: str = Field(..., description="Reason for requesting this code")
    priority: str = Field("medium", description="Priority level (high/medium/low)")
    context_depth: int = Field(3, description="Context depth for related code")
    analysis_focus: Optional[str] = Field(None, description="Specific analysis focus")
    
    @validator('context_depth')
    def validate_context_depth(cls, v: int) -> int:
        """Validate that context depth is positive."""
        if v <= 0:
            raise ValueError("Context depth must be positive")
        return v


class AuditContext(BaseModel):
    """Context information for an audit session."""
    module: Module = Field(..., description="Module being audited")
    project_info: Dict[str, Any] = Field(default_factory=dict, description="Project information")
    security_rules: Dict[str, bool] = Field(default_factory=dict, description="Security rules")
    code_index: Dict[str, Any] = Field(default_factory=dict, description="Code index")
    session_config: Dict[str, Any] = Field(default_factory=dict, description="Session configuration")
    isolation_boundary: List[str] = Field(default_factory=list, description="Isolation boundary")


class AuditRequest(BaseModel):
    """Request for audit analysis."""
    type: str = Field(..., description="Request type")
    context: AuditContext = Field(..., description="Audit context")
    code_requests: List[CodeRequest] = Field(default_factory=list, description="Code requests")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class AuditResponse(BaseModel):
    """Response from audit analysis."""
    findings: List[SecurityFinding] = Field(default_factory=list, description="Security findings")
    code_requests: List[CodeRequest] = Field(default_factory=list, description="Additional code requests")
    analysis_summary: str = Field("", description="Analysis summary")
    confidence_score: float = Field(0.0, description="Confidence score")
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v: float) -> float:
        """Validate that confidence score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
