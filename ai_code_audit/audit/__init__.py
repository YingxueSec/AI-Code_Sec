"""
Audit engine module for AI Code Audit System.

This module contains the core audit engine components including:
- Session management
- Analysis orchestration  
- Result aggregation
- Report generation
"""

from .session_manager import AuditSessionManager, AuditSession, SessionStatus
from .orchestrator import AnalysisOrchestrator, AnalysisTask, TaskStatus
from .aggregator import ResultAggregator, AuditResult, VulnerabilityFinding
from .report_generator import ReportGenerator, ReportFormat, AuditReport

__all__ = [
    # Session management
    'AuditSessionManager',
    'AuditSession', 
    'SessionStatus',
    
    # Analysis orchestration
    'AnalysisOrchestrator',
    'AnalysisTask',
    'TaskStatus',
    
    # Result aggregation
    'ResultAggregator',
    'AuditResult',
    'VulnerabilityFinding',
    
    # Report generation
    'ReportGenerator',
    'ReportFormat',
    'AuditReport',
]
