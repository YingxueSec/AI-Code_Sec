"""
Core module for AI Code Audit System

This module contains the fundamental data structures, models, and utilities
that are used throughout the application.
"""

from ai_code_audit.core.models import (
    ProjectType,
    SeverityLevel,
    VulnerabilityType,
    ProjectInfo,
    FileInfo,
    DependencyInfo,
    Module,
    SecurityFinding,
    AuditResult,
    AuditContext,
    CodeRequest,
    AuditRequest,
    AuditResponse,
)

from ai_code_audit.core.exceptions import (
    AuditError,
    ConfigurationError,
    ProjectAnalysisError,
    LLMError,
    DatabaseError,
    ValidationError,
)

from ai_code_audit.core.constants import (
    SUPPORTED_LANGUAGES,
    DEFAULT_SECURITY_RULES,
    VULNERABILITY_SEVERITY_MAPPING,
    PROJECT_TYPE_PATTERNS,
)

__all__ = [
    # Enums
    "ProjectType",
    "SeverityLevel", 
    "VulnerabilityType",
    # Models
    "ProjectInfo",
    "FileInfo",
    "DependencyInfo",
    "Module",
    "SecurityFinding",
    "AuditResult",
    "AuditContext",
    "CodeRequest",
    "AuditRequest",
    "AuditResponse",
    # Exceptions
    "AuditError",
    "ConfigurationError",
    "ProjectAnalysisError",
    "LLMError",
    "DatabaseError",
    "ValidationError",
    # Constants
    "SUPPORTED_LANGUAGES",
    "DEFAULT_SECURITY_RULES",
    "VULNERABILITY_SEVERITY_MAPPING",
    "PROJECT_TYPE_PATTERNS",
]
