"""
Custom exceptions for the AI Code Audit System.

This module defines all custom exceptions used throughout the application
to provide clear error handling and debugging information.
"""

from typing import Optional, Any, Dict


class AuditError(Exception):
    """Base exception for all audit-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# Alias for backward compatibility
AICodeAuditError = AuditError


class ConfigurationError(AuditError):
    """Raised when there's an error in configuration."""
    pass


class ProjectAnalysisError(AuditError):
    """Raised when project analysis fails."""
    pass


class LLMError(AuditError):
    """Raised when LLM API calls fail."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code
        self.response_text = response_text


class DatabaseError(AuditError):
    """Raised when database operations fail."""
    pass


class ValidationError(AuditError):
    """Raised when data validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.field = field
        self.value = value


class SessionError(AuditError):
    """Raised when audit session operations fail."""
    pass


class EvidenceError(AuditError):
    """Raised when evidence retrieval or validation fails."""
    pass


class CoverageError(AuditError):
    """Raised when coverage tracking operations fail."""
    pass


class HallucinationError(AuditError):
    """Raised when LLM hallucination is detected."""
    
    def __init__(
        self,
        message: str,
        confidence_score: Optional[float] = None,
        validation_errors: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.confidence_score = confidence_score
        self.validation_errors = validation_errors or []


class RetryableError(AuditError):
    """Base class for errors that can be retried."""
    
    def __init__(
        self,
        message: str,
        retry_count: int = 0,
        max_retries: int = 3,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.retry_count = retry_count
        self.max_retries = max_retries
    
    @property
    def can_retry(self) -> bool:
        """Check if this error can be retried."""
        return self.retry_count < self.max_retries


class APIRateLimitError(RetryableError):
    """Raised when API rate limit is exceeded."""
    pass


class TemporaryError(RetryableError):
    """Raised for temporary errors that should be retried."""
    pass


class LLMError(AICodeAuditError):
    """Base class for LLM-related errors."""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API calls fail."""

    def __init__(self, message: str, status_code: Optional[int] = None, is_retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.is_retryable = is_retryable


class LLMRateLimitError(LLMAPIError):
    """Raised when LLM API rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", status_code: Optional[int] = None):
        super().__init__(message, status_code, is_retryable=True)


class LLMAuthenticationError(LLMAPIError):
    """Raised when LLM API authentication fails."""

    def __init__(self, message: str = "Authentication failed", status_code: Optional[int] = None):
        super().__init__(message, status_code, is_retryable=False)


class LLMContextLengthError(LLMError):
    """Raised when input exceeds LLM context length limits."""
    pass


class LLMProviderError(LLMError):
    """Raised when LLM provider configuration or initialization fails."""
    pass
