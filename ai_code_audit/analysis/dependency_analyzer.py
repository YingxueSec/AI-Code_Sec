"""
Dependency analyzer for AI Code Audit System.

This module analyzes project dependencies from various package managers
and dependency files.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
import logging

from ai_code_audit.core.models import DependencyInfo
from ai_code_audit.core.constants import DEPENDENCY_FILES
from ai_code_audit.core.exceptions import ProjectAnalysisError

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes project dependencies from various sources."""
    
    def __init__(self):
        """Initialize dependency analyzer."""
        self.parsers = {
            'requirements.txt': self._parse_requirements_txt,
            'pyproject.toml': self._parse_pyproject_toml,
            'setup.py': self._parse_setup_py,
            'Pipfile': self._parse_pipfile,
            'package.json': self._parse_package_json,
            'yarn.lock': self._parse_yarn_lock,
            'package-lock.json': self._parse_package_lock,
            'pom.xml': self._parse_pom_xml,
            'build.gradle': self._parse_build_gradle,
            'Cargo.toml': self._parse_cargo_toml,
            'go.mod': self._parse_go_mod,
            'composer.json': self._parse_composer_json,
            'Gemfile': self._parse_gemfile,
        }
    
    def analyze_dependencies(self, project_path: str) -> List[DependencyInfo]:
        """
        Analyze all dependencies in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of DependencyInfo objects
        """
        try:
            project_path = Path(project_path).resolve()
            
            if not project_path.exists() or not project_path.is_dir():
                raise ProjectAnalysisError(f"Invalid project path: {project_path}")
            
            logger.info(f"Analyzing dependencies in: {project_path}")
            
            all_dependencies = []
            found_files = []
            
            # Find and parse dependency files
            for dep_file, language in DEPENDENCY_FILES.items():
                file_path = project_path / dep_file
                if file_path.exists():
                    found_files.append(dep_file)
                    try:
                        dependencies = self._parse_dependency_file(file_path, dep_file)
                        all_dependencies.extend(dependencies)
                    except Exception as e:
                        logger.warning(f"Failed to parse {dep_file}: {e}")
            
            # Remove duplicates while preserving order
            unique_dependencies = self._deduplicate_dependencies(all_dependencies)
            
            logger.info(f"Found {len(found_files)} dependency files, {len(unique_dependencies)} unique dependencies")
            
            return unique_dependencies
            
        except Exception as e:
            raise ProjectAnalysisError(f"Dependency analysis failed: {e}")
    
    def _parse_dependency_file(self, file_path: Path, filename: str) -> List[DependencyInfo]:
        """Parse a specific dependency file."""
        parser = self.parsers.get(filename)
        if not parser:
            logger.warning(f"No parser available for {filename}")
            return []
        
        try:
            return parser(file_path)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _parse_requirements_txt(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Python requirements.txt file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip -r, -e, -f options
                    if line.startswith(('-r', '-e', '-f')):
                        continue
                    
                    # Parse dependency
                    dep_info = self._parse_python_requirement(line)
                    if dep_info:
                        dependencies.append(dep_info)
        
        except Exception as e:
            logger.error(f"Error parsing requirements.txt: {e}")
        
        return dependencies
    
    def _parse_python_requirement(self, requirement: str) -> Optional[DependencyInfo]:
        """Parse a single Python requirement string."""
        try:
            # Remove inline comments
            requirement = requirement.split('#')[0].strip()
            
            # Handle different requirement formats
            # package==1.0.0, package>=1.0.0, package~=1.0.0, etc.
            match = re.match(r'^([a-zA-Z0-9_-]+)([><=!~]+)?([0-9.]+.*)?', requirement)
            
            if match:
                name = match.group(1)
                version = match.group(3) if match.group(3) else None
                
                return DependencyInfo(
                    name=name,
                    version=version,
                    source="pip"
                )
        
        except Exception as e:
            logger.debug(f"Failed to parse requirement '{requirement}': {e}")
        
        return None
    
    def _parse_pyproject_toml(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Python pyproject.toml file."""
        dependencies = []
        
        try:
            # Simple TOML parsing without external dependency
            content = self._read_file_content(file_path)
            
            # Look for dependencies section
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()
                
                if line == '[tool.poetry.dependencies]' or line == '[project.dependencies]':
                    in_dependencies = True
                    continue
                elif line.startswith('[') and in_dependencies:
                    in_dependencies = False
                    continue
                
                if in_dependencies and '=' in line:
                    # Parse dependency line
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        name = parts[0].strip().strip('"\'')
                        version = parts[1].strip().strip('"\'')
                        
                        if name != 'python':  # Skip Python version
                            dependencies.append(DependencyInfo(
                                name=name,
                                version=version,
                                source="poetry"
                            ))
        
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {e}")
        
        return dependencies
    
    def _parse_package_json(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Node.js package.json file."""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse dependencies
            for dep_type in ['dependencies', 'devDependencies']:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        source="npm"
                    ))
        
        except Exception as e:
            logger.error(f"Error parsing package.json: {e}")
        
        return dependencies
    
    def _parse_go_mod(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Go go.mod file."""
        dependencies = []
        
        try:
            content = self._read_file_content(file_path)
            
            in_require = False
            for line in content.split('\n'):
                line = line.strip()
                
                if line.startswith('require ('):
                    in_require = True
                    continue
                elif line == ')' and in_require:
                    in_require = False
                    continue
                elif line.startswith('require ') and not in_require:
                    # Single require statement
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[1]
                        version = parts[2]
                        dependencies.append(DependencyInfo(
                            name=name,
                            version=version,
                            source="go"
                        ))
                elif in_require and line and not line.startswith('//'):
                    # Dependency inside require block
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        dependencies.append(DependencyInfo(
                            name=name,
                            version=version,
                            source="go"
                        ))
        
        except Exception as e:
            logger.error(f"Error parsing go.mod: {e}")
        
        return dependencies
    
    def _parse_cargo_toml(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Rust Cargo.toml file."""
        dependencies = []
        
        try:
            content = self._read_file_content(file_path)
            
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()
                
                if line == '[dependencies]':
                    in_dependencies = True
                    continue
                elif line.startswith('[') and in_dependencies:
                    in_dependencies = False
                    continue
                
                if in_dependencies and '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        version = parts[1].strip().strip('"\'')
                        
                        dependencies.append(DependencyInfo(
                            name=name,
                            version=version,
                            source="cargo"
                        ))
        
        except Exception as e:
            logger.error(f"Error parsing Cargo.toml: {e}")
        
        return dependencies
    
    def _read_file_content(self, file_path: Path) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ""
    
    def _deduplicate_dependencies(self, dependencies: List[DependencyInfo]) -> List[DependencyInfo]:
        """Remove duplicate dependencies while preserving order."""
        seen = set()
        unique_deps = []
        
        for dep in dependencies:
            key = (dep.name, dep.source)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        
        return unique_deps
    
    # Placeholder methods for other parsers
    def _parse_setup_py(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Python setup.py file (basic implementation)."""
        return []  # Complex parsing would require AST analysis
    
    def _parse_pipfile(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Python Pipfile (basic implementation)."""
        return []  # Would need TOML parsing
    
    def _parse_yarn_lock(self, file_path: Path) -> List[DependencyInfo]:
        """Parse yarn.lock file (basic implementation)."""
        return []  # Complex format
    
    def _parse_package_lock(self, file_path: Path) -> List[DependencyInfo]:
        """Parse package-lock.json file (basic implementation)."""
        return []  # Very large files
    
    def _parse_pom_xml(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Maven pom.xml file (basic implementation)."""
        return []  # Would need XML parsing
    
    def _parse_build_gradle(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Gradle build.gradle file (basic implementation)."""
        return []  # Complex Groovy/Kotlin DSL
    
    def _parse_composer_json(self, file_path: Path) -> List[DependencyInfo]:
        """Parse PHP composer.json file (basic implementation)."""
        return []  # Similar to package.json
    
    def _parse_gemfile(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Ruby Gemfile (basic implementation)."""
        return []  # Ruby DSL parsing needed
