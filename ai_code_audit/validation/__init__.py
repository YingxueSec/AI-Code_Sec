"""
Validation module for AI Code Audit System.

This module provides validation and verification capabilities including:
- Hallucination detection and prevention
- Code consistency checking
- Line number reference validation
- Duplicate detection and deduplication
- Failure strategies and graceful degradation
"""

from .hallucination_detector import HallucinationDetector, ValidationResult, ValidationSeverity
from .consistency_checker import ConsistencyChecker, ConsistencyResult, ConsistencyIssue
from .duplicate_detector import DuplicateDetector, DuplicateResult, SimilarityMetric
from .failure_handler import FailureHandler, FailureStrategy, RecoveryAction

__all__ = [
    # Hallucination detection
    'HallucinationDetector',
    'ValidationResult',
    'ValidationSeverity',
    
    # Consistency checking
    'ConsistencyChecker',
    'ConsistencyResult',
    'ConsistencyIssue',
    
    # Duplicate detection
    'DuplicateDetector',
    'DuplicateResult',
    'SimilarityMetric',
    
    # Failure handling
    'FailureHandler',
    'FailureStrategy',
    'RecoveryAction',
]
