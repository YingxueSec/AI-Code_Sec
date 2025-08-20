"""
Project analyzer for AI Code Audit System.

This module provides comprehensive project analysis including file scanning,
language detection, dependency analysis, and project type identification.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
import logging

from ai_code_audit.core.models import ProjectInfo, FileInfo, DependencyInfo, ProjectType
from ai_code_audit.core.constants import PROJECT_TYPE_PATTERNS, SUPPORTED_LANGUAGES
from ai_code_audit.core.exceptions import ProjectAnalysisError
from ai_code_audit.analysis.file_scanner import FileScanner
from ai_code_audit.analysis.language_detector import LanguageDetector
from ai_code_audit.analysis.dependency_analyzer import DependencyAnalyzer
from ai_code_audit.analysis.context_analyzer import ContextAnalyzer

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    """Comprehensive project analysis and information extraction."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize project analyzer with component analyzers."""
        self.config = config
        self.file_scanner = FileScanner(config=config)
        self.language_detector = LanguageDetector()
        self.dependency_analyzer = DependencyAnalyzer()
        self.context_analyzer = ContextAnalyzer()
    
    async def analyze_project(self, project_path: str, save_to_db: bool = True) -> ProjectInfo:
        """
        Perform comprehensive project analysis.
        
        Args:
            project_path: Path to the project directory
            save_to_db: Whether to save results to database
            
        Returns:
            ProjectInfo object with complete analysis results
        """
        try:
            project_path = Path(project_path).resolve()
            
            if not project_path.exists():
                raise ProjectAnalysisError(f"Project path does not exist: {project_path}")
            
            if not project_path.is_dir():
                raise ProjectAnalysisError(f"Project path is not a directory: {project_path}")
            
            logger.info(f"Starting comprehensive analysis of: {project_path}")
            
            # Step 1: Basic project information
            project_name = project_path.name
            
            # Step 2: Scan files
            logger.info("Scanning project files...")
            files = self.file_scanner.scan_directory(str(project_path))
            
            # Step 3: Enhanced language detection
            logger.info("Performing enhanced language detection...")
            files = await self._enhance_language_detection(files)
            
            # Step 4: Analyze dependencies
            logger.info("Analyzing project dependencies...")
            dependencies = self.dependency_analyzer.analyze_dependencies(str(project_path))
            
            # Step 5: Detect project type
            logger.info("Detecting project type...")
            project_type = self._detect_project_type(project_path, files, dependencies)
            
            # Step 6: Identify architecture pattern
            logger.info("Identifying architecture pattern...")
            architecture_pattern = self._identify_architecture_pattern(project_path, files)
            
            # Step 7: Find entry points
            logger.info("Finding entry points...")
            entry_points = self._find_entry_points(files, project_type)
            
            # Step 8: Calculate statistics
            languages = self._get_project_languages(files)
            total_lines = await self._calculate_total_lines(files)
            
            # Step 9: Create ProjectInfo object
            project_info = ProjectInfo(
                path=str(project_path),
                name=project_name,
                project_type=project_type,
                files=files,
                dependencies=dependencies,
                entry_points=entry_points,
                languages=languages,
                architecture_pattern=architecture_pattern,
                total_lines=total_lines,
                created_at=datetime.now(),
            )
            
            # Step 10: Save to database if requested
            if save_to_db:
                await self._save_to_database(project_info)
            
            logger.info(f"Project analysis completed: {len(files)} files, {len(languages)} languages, {len(dependencies)} dependencies")
            
            return project_info
            
        except Exception as e:
            logger.error(f"Project analysis failed: {e}")
            raise ProjectAnalysisError(f"Failed to analyze project: {e}")
    
    async def _enhance_language_detection(self, files: List[FileInfo]) -> List[FileInfo]:
        """Enhance language detection using advanced heuristics."""
        enhanced_files = []
        
        for file_info in files:
            try:
                # Use advanced language detection
                file_path = Path(file_info.absolute_path)
                detected_language = self.language_detector.detect_language(file_path)
                
                # Update language if detection improved
                if detected_language and detected_language != file_info.language:
                    file_info.language = detected_language
                
                enhanced_files.append(file_info)
                
            except Exception as e:
                logger.warning(f"Language detection failed for {file_info.path}: {e}")
                enhanced_files.append(file_info)  # Keep original
        
        return enhanced_files
    
    def _detect_project_type(self, project_path: Path, files: List[FileInfo], dependencies: List[DependencyInfo]) -> ProjectType:
        """Detect project type based on files and dependencies."""
        try:
            # Check for specific files that indicate project type
            file_names = {f.path.lower() for f in files}
            file_names.update({Path(f.path).name.lower() for f in files})
            
            # Score different project types
            type_scores = {project_type: 0 for project_type in ProjectType}
            
            # Check against known patterns
            for project_type, patterns in PROJECT_TYPE_PATTERNS.items():
                for pattern in patterns:
                    pattern_lower = pattern.lower()
                    
                    # Check exact matches
                    if pattern_lower in file_names:
                        type_scores[ProjectType(project_type)] += 2
                    
                    # Check partial matches
                    for file_name in file_names:
                        if pattern_lower in file_name:
                            type_scores[ProjectType(project_type)] += 1
            
            # Additional heuristics based on dependencies
            dependency_names = {dep.name.lower() for dep in dependencies}
            
            # Web application indicators
            web_deps = {'flask', 'django', 'fastapi', 'express', 'react', 'vue', 'angular'}
            if dependency_names & web_deps:
                type_scores[ProjectType.WEB_APPLICATION] += 3
            
            # API service indicators
            api_deps = {'fastapi', 'flask-restful', 'express', 'gin', 'actix-web'}
            if dependency_names & api_deps:
                type_scores[ProjectType.API_SERVICE] += 3
            
            # Library indicators
            if any(f.path == 'setup.py' for f in files) or any(f.path == 'pyproject.toml' for f in files):
                type_scores[ProjectType.LIBRARY] += 2
            
            # Microservice indicators
            if any('docker' in f.path.lower() for f in files):
                type_scores[ProjectType.MICROSERVICE] += 2
            
            # Return type with highest score
            if max(type_scores.values()) > 0:
                return max(type_scores, key=type_scores.get)
            
            return ProjectType.UNKNOWN
            
        except Exception as e:
            logger.warning(f"Project type detection failed: {e}")
            return ProjectType.UNKNOWN
    
    def _identify_architecture_pattern(self, project_path: Path, files: List[FileInfo]) -> Optional[str]:
        """Identify common architecture patterns."""
        try:
            file_paths = {f.path.lower() for f in files}
            dir_names = set()
            
            # Extract directory names
            for file_info in files:
                path_parts = Path(file_info.path).parts
                dir_names.update(part.lower() for part in path_parts[:-1])  # Exclude filename
            
            # Check for common patterns
            patterns = {
                'MVC': {'models', 'views', 'controllers'},
                'MVP': {'models', 'views', 'presenters'},
                'MVVM': {'models', 'views', 'viewmodels'},
                'Clean Architecture': {'entities', 'usecases', 'adapters', 'frameworks'},
                'Hexagonal': {'domain', 'application', 'infrastructure'},
                'Layered': {'presentation', 'business', 'data', 'persistence'},
                'Microservices': {'services', 'api', 'gateway'},
                'Component-based': {'components', 'modules', 'widgets'},
            }
            
            for pattern_name, required_dirs in patterns.items():
                if len(required_dirs & dir_names) >= len(required_dirs) * 0.6:  # 60% match
                    return pattern_name
            
            # Check for specific framework patterns
            if 'src' in dir_names and 'test' in dir_names:
                return 'Standard Source Layout'
            
            return None
            
        except Exception as e:
            logger.warning(f"Architecture pattern detection failed: {e}")
            return None
    
    def _find_entry_points(self, files: List[FileInfo], project_type: ProjectType) -> List[str]:
        """Find likely entry points for the project."""
        entry_points = []
        
        try:
            # Common entry point patterns
            entry_patterns = {
                'main.py', 'app.py', 'server.py', 'index.py', 'run.py',
                'main.js', 'app.js', 'server.js', 'index.js',
                'main.java', 'Application.java', 'Main.java',
                'main.go', 'main.rs', 'main.cpp', 'main.c',
                'index.html', 'index.php'
            }
            
            # Find files matching entry patterns
            for file_info in files:
                filename = Path(file_info.path).name.lower()
                if filename in entry_patterns:
                    entry_points.append(file_info.path)
            
            # Project type specific entry points
            if project_type == ProjectType.WEB_APPLICATION:
                web_entries = [f.path for f in files if any(
                    pattern in f.path.lower() 
                    for pattern in ['wsgi.py', 'asgi.py', 'manage.py', 'app.py']
                )]
                entry_points.extend(web_entries)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_entries = []
            for entry in entry_points:
                if entry not in seen:
                    seen.add(entry)
                    unique_entries.append(entry)
            
            return unique_entries
            
        except Exception as e:
            logger.warning(f"Entry point detection failed: {e}")
            return []
    
    def _get_project_languages(self, files: List[FileInfo]) -> List[str]:
        """Get list of programming languages used in the project."""
        languages = set()
        
        for file_info in files:
            if file_info.language and file_info.language in SUPPORTED_LANGUAGES:
                languages.add(file_info.language)
        
        return sorted(list(languages))
    
    async def _calculate_total_lines(self, files: List[FileInfo]) -> int:
        """Calculate total lines of code (estimate based on file sizes)."""
        try:
            total_lines = 0
            
            for file_info in files:
                if file_info.language and file_info.size > 0:
                    # Rough estimate: average 50 characters per line
                    estimated_lines = max(1, file_info.size // 50)
                    total_lines += estimated_lines
            
            return total_lines
            
        except Exception as e:
            logger.warning(f"Line count calculation failed: {e}")
            return 0
    
    async def _save_to_database(self, project_info: ProjectInfo) -> None:
        """Save project information to database."""
        try:
            from ai_code_audit.database.connection import get_db_session, init_database
            from ai_code_audit.database.services import ProjectService, FileService

            # Ensure database is initialized
            try:
                await init_database()
            except Exception:
                pass  # May already be initialized

            async with get_db_session() as session:
                # Create project record
                project = await ProjectService.create_project(
                    session,
                    name=project_info.name,
                    path=project_info.path,
                    project_type=project_info.project_type,
                    languages=project_info.languages,
                    architecture_pattern=project_info.architecture_pattern,
                )

                # Create file records (limit to avoid overwhelming database)
                for file_info in project_info.files[:100]:  # Limit to first 100 files
                    await FileService.create_file(
                        session,
                        project_id=project.id,
                        path=file_info.path,
                        absolute_path=file_info.absolute_path,
                        language=file_info.language,
                        size=file_info.size,
                        hash=file_info.hash,
                        last_modified=file_info.last_modified,
                        functions=file_info.functions,
                        classes=file_info.classes,
                        imports=file_info.imports,
                    )

                # Update project statistics
                await ProjectService.update_project_stats(
                    session,
                    project.id,
                    total_files=len(project_info.files),
                    total_lines=project_info.total_lines,
                )

                logger.info(f"Project saved to database with ID: {project.id}")

        except Exception as e:
            logger.error(f"Failed to save project to database: {e}")
            # Don't raise exception - analysis can continue without DB save
    
    def get_analysis_summary(self, project_info: ProjectInfo) -> Dict[str, Any]:
        """Generate a summary of the project analysis."""
        return {
            'project_name': project_info.name,
            'project_type': project_info.project_type.value,
            'total_files': len(project_info.files),
            'total_lines': project_info.total_lines,
            'languages': project_info.languages,
            'dependencies_count': len(project_info.dependencies),
            'entry_points': project_info.entry_points,
            'architecture_pattern': project_info.architecture_pattern,
            'file_breakdown': self.file_scanner.get_file_count_by_language(project_info.files),
            'total_size_bytes': self.file_scanner.get_total_size(project_info.files),
        }
