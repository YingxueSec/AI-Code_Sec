"""
File scanner for AI Code Audit System.

This module provides functionality to scan project directories,
identify source files, and extract basic file information.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
import fnmatch
import logging

from ai_code_audit.core.models import FileInfo
from ai_code_audit.core.constants import LANGUAGE_EXTENSIONS, IGNORE_PATTERNS
from ai_code_audit.core.exceptions import ProjectAnalysisError

logger = logging.getLogger(__name__)


class FileScanner:
    """Scans project directories and identifies source files."""
    
    def __init__(self, ignore_patterns: Optional[List[str]] = None):
        """Initialize file scanner with ignore patterns."""
        self.ignore_patterns = ignore_patterns or IGNORE_PATTERNS.copy()
        self.supported_extensions = set(LANGUAGE_EXTENSIONS.keys())
    
    def scan_directory(self, project_path: str) -> List[FileInfo]:
        """
        Scan a directory and return list of source files.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of FileInfo objects for discovered source files
            
        Raises:
            ProjectAnalysisError: If scanning fails
        """
        try:
            project_path = Path(project_path).resolve()
            
            if not project_path.exists():
                raise ProjectAnalysisError(f"Project path does not exist: {project_path}")
            
            if not project_path.is_dir():
                raise ProjectAnalysisError(f"Project path is not a directory: {project_path}")
            
            logger.info(f"Scanning directory: {project_path}")
            
            files = []
            total_scanned = 0
            
            for file_path in self._walk_directory(project_path):
                total_scanned += 1
                
                if self._should_ignore_file(file_path, project_path):
                    continue
                
                if not self._is_source_file(file_path):
                    continue
                
                try:
                    file_info = self._create_file_info(file_path, project_path)
                    files.append(file_info)
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue
            
            logger.info(f"Scanned {total_scanned} files, found {len(files)} source files")
            return files
            
        except Exception as e:
            raise ProjectAnalysisError(f"Failed to scan directory: {e}")
    
    def _walk_directory(self, project_path: Path) -> List[Path]:
        """Walk directory and return all file paths."""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(project_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore_path(Path(root) / d, project_path)]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    files.append(file_path)
            
            return files
            
        except Exception as e:
            logger.error(f"Error walking directory {project_path}: {e}")
            return []
    
    def _should_ignore_file(self, file_path: Path, project_root: Path) -> bool:
        """Check if file should be ignored based on patterns."""
        try:
            # Get relative path for pattern matching
            rel_path = file_path.relative_to(project_root)
            
            return self._should_ignore_path(file_path, project_root)
            
        except Exception:
            return True  # Ignore files we can't process
    
    def _should_ignore_path(self, path: Path, project_root: Path) -> bool:
        """Check if path should be ignored based on patterns."""
        try:
            # Get relative path for pattern matching
            rel_path = path.relative_to(project_root)
            path_str = str(rel_path)
            
            # Check against ignore patterns
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                    return True
                
                # Check if any parent directory matches the pattern
                for parent in rel_path.parents:
                    if fnmatch.fnmatch(parent.name, pattern):
                        return True
            
            return False
            
        except Exception:
            return True  # Ignore paths we can't process
    
    def _is_source_file(self, file_path: Path) -> bool:
        """Check if file is a source code file."""
        try:
            # Check file extension
            if file_path.suffix.lower() in self.supported_extensions:
                return True
            
            # Check for files without extensions that might be source files
            if not file_path.suffix:
                # Check for common source file names
                common_source_names = {
                    'Makefile', 'makefile', 'Dockerfile', 'dockerfile',
                    'Jenkinsfile', 'Vagrantfile', 'Rakefile'
                }
                if file_path.name in common_source_names:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _create_file_info(self, file_path: Path, project_root: Path) -> FileInfo:
        """Create FileInfo object for a file."""
        try:
            # Get relative path
            rel_path = file_path.relative_to(project_root)
            
            # Get file stats
            stat = file_path.stat()
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Get modification time
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            return FileInfo(
                path=str(rel_path),
                absolute_path=str(file_path),
                language=language,
                size=stat.st_size,
                hash=file_hash,
                last_modified=last_modified,
                functions=[],  # Will be populated by code analyzer
                classes=[],    # Will be populated by code analyzer
                imports=[],    # Will be populated by code analyzer
            )
            
        except Exception as e:
            raise ProjectAnalysisError(f"Failed to create file info for {file_path}: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        try:
            hash_sha256 = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        try:
            extension = file_path.suffix.lower()
            return LANGUAGE_EXTENSIONS.get(extension)
            
        except Exception:
            return None
    
    def add_ignore_pattern(self, pattern: str) -> None:
        """Add a new ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
    
    def remove_ignore_pattern(self, pattern: str) -> None:
        """Remove an ignore pattern."""
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
    
    def get_file_count_by_language(self, files: List[FileInfo]) -> Dict[str, int]:
        """Get count of files by programming language."""
        counts = {}
        
        for file_info in files:
            if file_info.language:
                counts[file_info.language] = counts.get(file_info.language, 0) + 1
        
        return counts
    
    def get_total_size(self, files: List[FileInfo]) -> int:
        """Get total size of all files in bytes."""
        return sum(file_info.size for file_info in files)
    
    def filter_by_language(self, files: List[FileInfo], language: str) -> List[FileInfo]:
        """Filter files by programming language."""
        return [f for f in files if f.language == language]
    
    def filter_by_size(self, files: List[FileInfo], min_size: int = 0, max_size: Optional[int] = None) -> List[FileInfo]:
        """Filter files by size range."""
        filtered = [f for f in files if f.size >= min_size]
        
        if max_size is not None:
            filtered = [f for f in filtered if f.size <= max_size]
        
        return filtered
