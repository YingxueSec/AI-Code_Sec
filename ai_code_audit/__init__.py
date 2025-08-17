"""
AI Code Audit System

A comprehensive AI-powered code security audit system that provides
intelligent analysis of source code for security vulnerabilities,
code quality issues, and best practice violations.
"""

__version__ = "0.1.0"
__author__ = "AI Code Audit Team"
__email__ = "team@example.com"

from ai_code_audit.core.models import (
    ProjectInfo,
    FileInfo,
    Module,
    SecurityFinding,
    AuditResult,
    AuditContext,
)

__all__ = [
    "ProjectInfo",
    "FileInfo", 
    "Module",
    "SecurityFinding",
    "AuditResult",
    "AuditContext",
]
