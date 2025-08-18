"""
Constants and configuration values for the AI Code Audit System.

This module contains all the constant values, mappings, and default
configurations used throughout the application.
"""

from typing import Dict, List, Set

# Supported programming languages
SUPPORTED_LANGUAGES: Set[str] = {
    "python",
    "javascript", 
    "typescript",
    "java",
    "go",
    "rust",
    "cpp",
    "c",
    "csharp",
    "php",
    "ruby",
    "kotlin",
    "swift",
    "scala",
}

# File extension to language mapping
LANGUAGE_EXTENSIONS: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript", 
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".kt": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
}

# Default security rules configuration
DEFAULT_SECURITY_RULES: Dict[str, bool] = {
    "sql_injection": True,
    "xss": True,
    "csrf": True,
    "authentication": True,
    "authorization": True,
    "data_validation": True,
    "sensitive_data_exposure": True,
    "insecure_crypto": True,
    "code_injection": True,
    "path_traversal": True,
    "buffer_overflow": True,
    "race_condition": True,
    "privilege_escalation": True,
    "session_management": True,
    "error_handling": True,
}

# Vulnerability type to severity mapping
VULNERABILITY_SEVERITY_MAPPING: Dict[str, str] = {
    "sql_injection": "high",
    "xss": "medium",
    "csrf": "medium", 
    "authentication_bypass": "critical",
    "authorization_failure": "high",
    "data_validation": "medium",
    "sensitive_data_exposure": "high",
    "insecure_crypto": "high",
    "code_injection": "critical",
    "path_traversal": "high",
    "buffer_overflow": "critical",
    "race_condition": "medium",
    "privilege_escalation": "critical",
    "session_management": "medium",
    "error_handling": "low",
}

# Project type detection patterns
PROJECT_TYPE_PATTERNS: Dict[str, List[str]] = {
    "web_application": [
        "package.json",
        "requirements.txt",
        "Gemfile",
        "composer.json",
        "app.py",
        "server.js",
        "index.html",
    ],
    "api_service": [
        "openapi.yaml",
        "swagger.json",
        "api/",
        "routes/",
        "controllers/",
        "endpoints/",
    ],
    "desktop_application": [
        "main.py",
        "main.java",
        "main.cpp",
        "Program.cs",
        "src/main/",
    ],
    "library": [
        "setup.py",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "Cargo.toml",
        "package.json",
    ],
    "microservice": [
        "Dockerfile",
        "docker-compose.yml",
        "kubernetes/",
        "k8s/",
        "helm/",
    ],
}

# High-risk security topics for coverage tracking
HIGH_RISK_TOPICS: List[str] = [
    "authentication",
    "authorization", 
    "input_validation",
    "sql_injection",
    "xss",
    "csrf",
    "file_upload",
    "session_management",
    "crypto_usage",
    "error_handling",
    "privilege_escalation",
    "data_exposure",
]

# Default LLM configuration (Kimi优先，更稳定)
DEFAULT_LLM_CONFIG: Dict[str, Dict[str, any]] = {
    "kimi": {
        "model_name": "moonshotai/Kimi-K2-Instruct",
        "max_tokens": 128000,
        "temperature": 0.1,
        "timeout": 60,
    },
    "qwen": {
        "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "max_tokens": 32768,
        "temperature": 0.1,
        "timeout": 30,
    },
}

# Audit session configuration
DEFAULT_AUDIT_CONFIG: Dict[str, any] = {
    "max_concurrent_sessions": 3,
    "cache_ttl": 86400,  # 24 hours
    "max_file_size": 1024 * 1024,  # 1MB
    "max_files_per_request": 50,
    "context_lines": 5,
    "max_context_depth": 3,
}

# Database configuration
DEFAULT_DATABASE_CONFIG: Dict[str, any] = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False,
}

# File patterns to ignore during scanning
IGNORE_PATTERNS: List[str] = [
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    "node_modules",
    "target",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".coverage",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.log",
    "*.tmp",
    "*.temp",
]

# Common dependency files
DEPENDENCY_FILES: Dict[str, str] = {
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "Pipfile": "python",
    "package.json": "javascript",
    "yarn.lock": "javascript",
    "package-lock.json": "javascript",
    "pom.xml": "java",
    "build.gradle": "java",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "composer.json": "php",
    "Gemfile": "ruby",
}

# CWE (Common Weakness Enumeration) mappings
CWE_MAPPINGS: Dict[str, str] = {
    "sql_injection": "CWE-89",
    "xss": "CWE-79",
    "csrf": "CWE-352",
    "authentication_bypass": "CWE-287",
    "authorization_failure": "CWE-285",
    "data_validation": "CWE-20",
    "sensitive_data_exposure": "CWE-200",
    "insecure_crypto": "CWE-327",
    "code_injection": "CWE-94",
    "path_traversal": "CWE-22",
    "buffer_overflow": "CWE-120",
    "race_condition": "CWE-362",
    "privilege_escalation": "CWE-269",
}

# OWASP Top 10 mappings
OWASP_MAPPINGS: Dict[str, str] = {
    "sql_injection": "A03:2021 – Injection",
    "xss": "A03:2021 – Injection", 
    "authentication_bypass": "A07:2021 – Identification and Authentication Failures",
    "authorization_failure": "A01:2021 – Broken Access Control",
    "sensitive_data_exposure": "A02:2021 – Cryptographic Failures",
    "insecure_crypto": "A02:2021 – Cryptographic Failures",
    "code_injection": "A03:2021 – Injection",
    "path_traversal": "A01:2021 – Broken Access Control",
}
