"""
Analysis module for AI Code Audit System.

This module provides project analysis, file scanning, language detection,
and dependency analysis functionality.
"""

from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
from ai_code_audit.analysis.file_scanner import FileScanner
from ai_code_audit.analysis.language_detector import LanguageDetector
from ai_code_audit.analysis.dependency_analyzer import DependencyAnalyzer

__all__ = [
    "ProjectAnalyzer",
    "FileScanner", 
    "LanguageDetector",
    "DependencyAnalyzer",
]
