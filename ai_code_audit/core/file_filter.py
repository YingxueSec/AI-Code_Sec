"""
File filtering module for AI Code Audit System.

This module provides intelligent file filtering to exclude irrelevant files
from security audits, improving efficiency and reducing false positives.
"""

import os
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Tuple
import logging
from dataclasses import dataclass

from .config import FileFilteringConfig

logger = logging.getLogger(__name__)


@dataclass
class FilterStats:
    """Statistics about file filtering"""
    total_files: int = 0
    filtered_files: int = 0
    included_files: int = 0
    filtered_by_pattern: int = 0
    filtered_by_size: int = 0
    filtered_by_gitignore: int = 0
    filtered_by_library: int = 0
    force_included: int = 0


class FileFilter:
    """Intelligent file filter for code auditing"""
    
    def __init__(self, config: FileFilteringConfig, project_root: str):
        self.config = config
        self.project_root = Path(project_root).resolve()
        self.stats = FilterStats()
        self._gitignore_patterns = []
        
        if config.use_gitignore:
            self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """Load patterns from .gitignore file"""
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self._gitignore_patterns.append(line)
                logger.info(f"Loaded {len(self._gitignore_patterns)} patterns from .gitignore")
            except Exception as e:
                logger.warning(f"Failed to load .gitignore: {e}")
    
    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file matches any of the given patterns"""
        try:
            file_path_obj = Path(file_path).resolve()
            # Check if file is within project root
            if not str(file_path_obj).startswith(str(self.project_root)):
                return False

            rel_path = str(file_path_obj.relative_to(self.project_root))
        except (ValueError, OSError):
            # If we can't get relative path, use the basename
            rel_path = os.path.basename(file_path)

        for pattern in patterns:
            # Handle directory patterns
            if pattern.endswith('/'):
                if rel_path.startswith(pattern[:-1] + '/') or rel_path == pattern[:-1]:
                    return True
            # Handle glob patterns
            elif fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
            # Handle directory wildcards
            elif '**' in pattern:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True

        return False
    
    def _is_library_file(self, file_path: str) -> bool:
        """Detect if file is a library file based on content"""
        if not self.config.detect_libraries:
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to check for library indicators
                first_lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # Only check first 10 lines
                        break
                    first_lines.append(line.lower())
                
                content = ''.join(first_lines)
                
                # Check for library keywords
                for keyword in self.config.library_keywords:
                    if keyword.lower() in content:
                        return True
                        
        except Exception:
            # If we can't read the file, don't filter it
            pass
        
        return False
    
    def _should_force_include(self, file_path: str) -> bool:
        """Check if file should be force included despite other filters"""
        return self._matches_patterns(file_path, self.config.force_include)
    
    def _is_too_large(self, file_path: str) -> bool:
        """Check if file is too large"""
        try:
            return os.path.getsize(file_path) > self.config.max_file_size
        except OSError:
            return False
    
    def should_include_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Determine if a file should be included in the audit.
        
        Returns:
            Tuple[bool, str]: (should_include, reason)
        """
        if not self.config.enabled:
            return True, "filtering_disabled"
        
        file_path = str(Path(file_path).resolve())
        self.stats.total_files += 1
        
        # Force include check (highest priority)
        if self._should_force_include(file_path):
            self.stats.force_included += 1
            self.stats.included_files += 1
            return True, "force_included"
        
        # Check absolute ignore patterns
        if self._matches_patterns(file_path, self.config.ignore_patterns):
            self.stats.filtered_by_pattern += 1
            self.stats.filtered_files += 1
            return False, "ignore_pattern"
        
        # Check gitignore patterns
        if self.config.use_gitignore and self._matches_patterns(file_path, self._gitignore_patterns):
            self.stats.filtered_by_gitignore += 1
            self.stats.filtered_files += 1
            return False, "gitignore"
        
        # Check file size
        if self._is_too_large(file_path):
            self.stats.filtered_by_size += 1
            self.stats.filtered_files += 1
            return False, "too_large"
        
        # Check conditional ignores
        conditional = self.config.conditional_ignore
        
        if conditional.css_files and self._matches_patterns(file_path, self.config.css_patterns):
            self.stats.filtered_files += 1
            return False, "css_file"
        
        if conditional.test_files and self._matches_patterns(file_path, self.config.test_patterns):
            self.stats.filtered_files += 1
            return False, "test_file"
        
        if conditional.doc_files and self._matches_patterns(file_path, self.config.doc_patterns):
            self.stats.filtered_files += 1
            return False, "doc_file"
        
        if conditional.log_files and self._matches_patterns(file_path, self.config.log_patterns):
            self.stats.filtered_files += 1
            return False, "log_file"
        
        # Check if it's a library file
        if self._is_library_file(file_path):
            self.stats.filtered_by_library += 1
            self.stats.filtered_files += 1
            return False, "library_file"
        
        # File should be included
        self.stats.included_files += 1
        return True, "included"
    
    def filter_files(self, file_paths: List[str]) -> Tuple[List[str], FilterStats]:
        """
        Filter a list of file paths.
        
        Returns:
            Tuple[List[str], FilterStats]: (included_files, filter_stats)
        """
        included_files = []
        
        for file_path in file_paths:
            should_include, reason = self.should_include_file(file_path)
            if should_include:
                included_files.append(file_path)
            else:
                logger.debug(f"Filtered out {file_path}: {reason}")
        
        logger.info(f"File filtering complete: {self.stats.included_files}/{self.stats.total_files} files included")
        return included_files, self.stats
    
    def get_filter_summary(self) -> str:
        """Get a human-readable summary of filtering results"""
        if self.stats.total_files == 0:
            return "No files processed"
        
        efficiency = (self.stats.filtered_files / self.stats.total_files) * 100
        
        summary = f"""📊 File Filtering Summary:
• Total files scanned: {self.stats.total_files:,}
• Files included for audit: {self.stats.included_files:,}
• Files filtered out: {self.stats.filtered_files:,}
• Filtering efficiency: {efficiency:.1f}%

📋 Filtering breakdown:
• Filtered by patterns: {self.stats.filtered_by_pattern:,}
• Filtered by .gitignore: {self.stats.filtered_by_gitignore:,}
• Filtered by file size: {self.stats.filtered_by_size:,}
• Filtered as libraries: {self.stats.filtered_by_library:,}
• Force included: {self.stats.force_included:,}"""
        
        return summary
