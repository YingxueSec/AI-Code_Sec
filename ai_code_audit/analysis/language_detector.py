"""
Language detector for AI Code Audit System.

This module provides advanced language detection capabilities beyond
simple file extension matching.
"""

import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

from ai_code_audit.core.constants import LANGUAGE_EXTENSIONS, SUPPORTED_LANGUAGES
from ai_code_audit.core.exceptions import ProjectAnalysisError

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Advanced programming language detection."""
    
    def __init__(self):
        """Initialize language detector with patterns and heuristics."""
        self.shebang_patterns = {
            'python': [r'#!/.*python[0-9.]*', r'#!/usr/bin/env python[0-9.]*'],
            'javascript': [r'#!/.*node', r'#!/usr/bin/env node'],
            'ruby': [r'#!/.*ruby', r'#!/usr/bin/env ruby'],
            'php': [r'#!/.*php', r'#!/usr/bin/env php'],
            'go': [r'#!/.*go'],
        }
        
        self.content_patterns = {
            'python': [
                r'import\s+\w+',
                r'from\s+\w+\s+import',
                r'def\s+\w+\s*\(',
                r'class\s+\w+\s*\(',
                r'if\s+__name__\s*==\s*["\']__main__["\']',
            ],
            'javascript': [
                r'function\s+\w+\s*\(',
                r'var\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'const\s+\w+\s*=',
                r'require\s*\(',
                r'module\.exports',
                r'export\s+(default\s+)?',
            ],
            'typescript': [
                r'interface\s+\w+',
                r'type\s+\w+\s*=',
                r':\s*(string|number|boolean|any)',
                r'export\s+(interface|type|class)',
                r'import.*from\s+["\'].*["\']',
            ],
            'java': [
                r'public\s+class\s+\w+',
                r'private\s+\w+\s+\w+',
                r'public\s+static\s+void\s+main',
                r'import\s+java\.',
                r'package\s+\w+',
            ],
            'go': [
                r'package\s+\w+',
                r'import\s+\(',
                r'func\s+\w+\s*\(',
                r'type\s+\w+\s+struct',
                r'var\s+\w+\s+\w+',
            ],
            'rust': [
                r'fn\s+\w+\s*\(',
                r'let\s+\w+\s*=',
                r'struct\s+\w+',
                r'impl\s+\w+',
                r'use\s+\w+',
                r'extern\s+crate',
            ],
            'cpp': [
                r'#include\s*<.*>',
                r'#include\s*".*"',
                r'using\s+namespace',
                r'class\s+\w+',
                r'int\s+main\s*\(',
                r'std::',
            ],
            'c': [
                r'#include\s*<.*\.h>',
                r'int\s+main\s*\(',
                r'printf\s*\(',
                r'malloc\s*\(',
                r'typedef\s+struct',
            ],
            'csharp': [
                r'using\s+System',
                r'namespace\s+\w+',
                r'public\s+class\s+\w+',
                r'static\s+void\s+Main',
                r'Console\.WriteLine',
            ],
            'php': [
                r'<\?php',
                r'\$\w+\s*=',
                r'function\s+\w+\s*\(',
                r'class\s+\w+',
                r'echo\s+',
                r'require_once',
            ],
            'ruby': [
                r'def\s+\w+',
                r'class\s+\w+',
                r'require\s+["\']',
                r'puts\s+',
                r'end\s*$',
                r'@\w+\s*=',
            ],
            'kotlin': [
                r'fun\s+\w+\s*\(',
                r'class\s+\w+',
                r'val\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'package\s+\w+',
            ],
            'swift': [
                r'func\s+\w+\s*\(',
                r'class\s+\w+',
                r'var\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'import\s+\w+',
            ],
            'scala': [
                r'object\s+\w+',
                r'class\s+\w+',
                r'def\s+\w+\s*\(',
                r'val\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'import\s+\w+',
            ],
        }
        
        self.filename_patterns = {
            'python': ['setup.py', 'manage.py', '__init__.py'],
            'javascript': ['package.json', 'webpack.config.js', 'gulpfile.js'],
            'typescript': ['tsconfig.json'],
            'java': ['pom.xml', 'build.gradle'],
            'go': ['go.mod', 'go.sum'],
            'rust': ['Cargo.toml', 'Cargo.lock'],
            'cpp': ['CMakeLists.txt', 'Makefile'],
            'csharp': ['*.csproj', '*.sln'],
            'php': ['composer.json', 'composer.lock'],
            'ruby': ['Gemfile', 'Gemfile.lock', 'Rakefile'],
        }
    
    def detect_language(self, file_path: Path, content: Optional[str] = None) -> Optional[str]:
        """
        Detect programming language using multiple heuristics.
        
        Args:
            file_path: Path to the file
            content: File content (optional, will be read if not provided)
            
        Returns:
            Detected language name or None if not detected
        """
        try:
            # First try extension-based detection
            extension_lang = self._detect_by_extension(file_path)
            
            # If we have a clear match from extension, use it
            if extension_lang and extension_lang in SUPPORTED_LANGUAGES:
                return extension_lang
            
            # Try filename-based detection
            filename_lang = self._detect_by_filename(file_path)
            if filename_lang:
                return filename_lang
            
            # If no content provided, try to read it
            if content is None:
                content = self._read_file_content(file_path)
            
            if not content:
                return extension_lang  # Fall back to extension
            
            # Try shebang detection
            shebang_lang = self._detect_by_shebang(content)
            if shebang_lang:
                return shebang_lang
            
            # Try content pattern detection
            content_lang = self._detect_by_content(content)
            if content_lang:
                return content_lang
            
            # Fall back to extension-based detection
            return extension_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed for {file_path}: {e}")
            return self._detect_by_extension(file_path)
    
    def _detect_by_extension(self, file_path: Path) -> Optional[str]:
        """Detect language by file extension."""
        extension = file_path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(extension)
    
    def _detect_by_filename(self, file_path: Path) -> Optional[str]:
        """Detect language by specific filename patterns."""
        filename = file_path.name.lower()
        
        for language, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if filename == pattern.lower() or filename.endswith(pattern.lower()):
                    return language
        
        return None
    
    def _detect_by_shebang(self, content: str) -> Optional[str]:
        """Detect language by shebang line."""
        lines = content.split('\n', 1)
        if not lines or not lines[0].startswith('#!'):
            return None
        
        shebang = lines[0]
        
        for language, patterns in self.shebang_patterns.items():
            for pattern in patterns:
                if re.search(pattern, shebang, re.IGNORECASE):
                    return language
        
        return None
    
    def _detect_by_content(self, content: str) -> Optional[str]:
        """Detect language by content patterns."""
        # Limit content analysis to first 10KB for performance
        analysis_content = content[:10240]
        
        language_scores = {}
        
        for language, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, analysis_content, re.MULTILINE | re.IGNORECASE))
                score += matches
            
            if score > 0:
                language_scores[language] = score
        
        if not language_scores:
            return None
        
        # Return language with highest score
        best_language = max(language_scores, key=language_scores.get)
        
        # Only return if we have a reasonable confidence
        if language_scores[best_language] >= 2:
            return best_language
        
        return None
    
    def _read_file_content(self, file_path: Path, max_size: int = 10240) -> str:
        """Read file content for analysis."""
        try:
            # Only read first part of file for performance
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_size)
        except Exception as e:
            logger.debug(f"Failed to read file {file_path}: {e}")
            return ""
    
    def get_language_confidence(self, file_path: Path, content: Optional[str] = None) -> Dict[str, float]:
        """
        Get confidence scores for all possible languages.
        
        Returns:
            Dictionary mapping language names to confidence scores (0.0-1.0)
        """
        try:
            if content is None:
                content = self._read_file_content(file_path)
            
            scores = {}
            
            # Extension-based score
            ext_lang = self._detect_by_extension(file_path)
            if ext_lang:
                scores[ext_lang] = scores.get(ext_lang, 0) + 0.5
            
            # Filename-based score
            filename_lang = self._detect_by_filename(file_path)
            if filename_lang:
                scores[filename_lang] = scores.get(filename_lang, 0) + 0.3
            
            # Shebang-based score
            shebang_lang = self._detect_by_shebang(content)
            if shebang_lang:
                scores[shebang_lang] = scores.get(shebang_lang, 0) + 0.8
            
            # Content-based scores
            for language, patterns in self.content_patterns.items():
                pattern_score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content[:10240], re.MULTILINE | re.IGNORECASE))
                    pattern_score += matches
                
                if pattern_score > 0:
                    # Normalize pattern score to 0-0.7 range
                    normalized_score = min(pattern_score * 0.1, 0.7)
                    scores[language] = scores.get(language, 0) + normalized_score
            
            # Normalize all scores to 0-1 range
            if scores:
                max_score = max(scores.values())
                if max_score > 1.0:
                    scores = {lang: score / max_score for lang, score in scores.items()}
            
            return scores
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed for {file_path}: {e}")
            return {}
    
    def is_supported_language(self, language: str) -> bool:
        """Check if language is supported by the system."""
        return language in SUPPORTED_LANGUAGES
