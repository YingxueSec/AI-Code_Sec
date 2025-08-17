"""
Database module for AI Code Audit System.

This module provides database connectivity, ORM models, and data persistence
functionality using SQLAlchemy with async MySQL support.
"""

from ai_code_audit.database.connection import (
    DatabaseManager,
    get_db_session,
    init_database,
    close_database,
)

from ai_code_audit.database.models import (
    Base,
    Project,
    File,
    Module,
    AuditSession,
    SecurityFinding,
    AuditReport,
    CacheEntry,
)

__all__ = [
    # Connection management
    "DatabaseManager",
    "get_db_session", 
    "init_database",
    "close_database",
    # ORM Models
    "Base",
    "Project",
    "File", 
    "Module",
    "AuditSession",
    "SecurityFinding",
    "AuditReport",
    "CacheEntry",
]
