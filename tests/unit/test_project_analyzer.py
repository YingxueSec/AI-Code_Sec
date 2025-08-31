"""
Unit tests for project analysis functionality.

This module tests the project analyzer, file scanner, language detector,
and dependency analyzer components.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_code_audit.analysis.file_scanner import FileScanner
from ai_code_audit.analysis.language_detector import LanguageDetector
from ai_code_audit.analysis.dependency_analyzer import DependencyAnalyzer
from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
from ai_code_audit.core.models import ProjectType, FileInfo, DependencyInfo
from ai_code_audit.core.exceptions import ProjectAnalysisError


class TestFileScanner:
    """Test file scanner functionality."""
    
    def test_file_scanner_initialization(self):
        """Test file scanner initialization."""
        scanner = FileScanner()
        
        assert scanner.ignore_patterns is not None
        assert len(scanner.ignore_patterns) > 0
        assert scanner.supported_extensions is not None
        assert '.py' in scanner.supported_extensions
    
    def test_should_ignore_file(self):
        """Test file ignore logic."""
        scanner = FileScanner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / 'test.py').touch()
            (temp_path / '__pycache__').mkdir()
            (temp_path / '__pycache__' / 'test.pyc').touch()
            (temp_path / '.git').mkdir()
            (temp_path / '.git' / 'config').touch()
            
            # Test ignore logic
            assert not scanner._should_ignore_file(temp_path / 'test.py', temp_path)
            assert scanner._should_ignore_file(temp_path / '__pycache__' / 'test.pyc', temp_path)
            assert scanner._should_ignore_file(temp_path / '.git' / 'config', temp_path)
    
    def test_is_source_file(self):
        """Test source file detection."""
        scanner = FileScanner()
        
        # Test various file types
        assert scanner._is_source_file(Path('test.py'))
        assert scanner._is_source_file(Path('test.js'))
        assert scanner._is_source_file(Path('test.java'))
        assert scanner._is_source_file(Path('Makefile'))
        assert scanner._is_source_file(Path('Dockerfile'))
        
        assert not scanner._is_source_file(Path('test.txt'))
        assert not scanner._is_source_file(Path('test.log'))
        assert not scanner._is_source_file(Path('test.pyc'))
    
    def test_scan_directory_with_sample_project(self):
        """Test directory scanning with sample project."""
        scanner = FileScanner()
        
        # Use the sample project we created
        sample_project_path = Path('sample_project')
        if sample_project_path.exists():
            files = scanner.scan_directory(str(sample_project_path))
            
            assert len(files) > 0
            assert any(f.path == 'app.py' for f in files)
            assert any(f.language == 'python' for f in files)
    
    def test_scan_nonexistent_directory(self):
        """Test scanning non-existent directory."""
        scanner = FileScanner()
        
        with pytest.raises(ProjectAnalysisError):
            scanner.scan_directory('/nonexistent/path')
    
    def test_get_file_count_by_language(self):
        """Test file count by language."""
        scanner = FileScanner()
        
        files = [
            FileInfo(path='test1.py', absolute_path='/test1.py', language='python'),
            FileInfo(path='test2.py', absolute_path='/test2.py', language='python'),
            FileInfo(path='test.js', absolute_path='/test.js', language='javascript'),
        ]
        
        counts = scanner.get_file_count_by_language(files)
        
        assert counts['python'] == 2
        assert counts['javascript'] == 1


class TestLanguageDetector:
    """Test language detector functionality."""
    
    def test_language_detector_initialization(self):
        """Test language detector initialization."""
        detector = LanguageDetector()
        
        assert detector.shebang_patterns is not None
        assert detector.content_patterns is not None
        assert 'python' in detector.shebang_patterns
        assert 'python' in detector.content_patterns
    
    def test_detect_by_extension(self):
        """Test extension-based language detection."""
        detector = LanguageDetector()
        
        assert detector._detect_by_extension(Path('test.py')) == 'python'
        assert detector._detect_by_extension(Path('test.js')) == 'javascript'
        assert detector._detect_by_extension(Path('test.java')) == 'java'
        assert detector._detect_by_extension(Path('test.unknown')) is None
    
    def test_detect_by_filename(self):
        """Test filename-based language detection."""
        detector = LanguageDetector()
        
        assert detector._detect_by_filename(Path('setup.py')) == 'python'
        assert detector._detect_by_filename(Path('package.json')) == 'javascript'
        assert detector._detect_by_filename(Path('pom.xml')) == 'java'
    
    def test_detect_by_shebang(self):
        """Test shebang-based language detection."""
        detector = LanguageDetector()
        
        python_content = "#!/usr/bin/env python3\nprint('hello')"
        assert detector._detect_by_shebang(python_content) == 'python'
        
        node_content = "#!/usr/bin/env node\nconsole.log('hello')"
        assert detector._detect_by_shebang(node_content) == 'javascript'
        
        no_shebang = "print('hello')"
        assert detector._detect_by_shebang(no_shebang) is None
    
    def test_detect_by_content(self):
        """Test content-based language detection."""
        detector = LanguageDetector()
        
        python_content = """
import os
def main():
    print("Hello World")
if __name__ == "__main__":
    main()
"""
        assert detector._detect_by_content(python_content) == 'python'
        
        js_content = """
function main() {
    console.log("Hello World");
}
module.exports = main;
"""
        assert detector._detect_by_content(js_content) == 'javascript'
    
    def test_is_supported_language(self):
        """Test supported language check."""
        detector = LanguageDetector()
        
        assert detector.is_supported_language('python')
        assert detector.is_supported_language('javascript')
        assert not detector.is_supported_language('unknown_language')


class TestDependencyAnalyzer:
    """Test dependency analyzer functionality."""
    
    def test_dependency_analyzer_initialization(self):
        """Test dependency analyzer initialization."""
        analyzer = DependencyAnalyzer()
        
        assert analyzer.parsers is not None
        assert 'requirements.txt' in analyzer.parsers
        assert 'package.json' in analyzer.parsers
    
    def test_parse_python_requirement(self):
        """Test Python requirement parsing."""
        analyzer = DependencyAnalyzer()
        
        # Test various requirement formats
        dep1 = analyzer._parse_python_requirement('requests==2.28.0')
        assert dep1.name == 'requests'
        assert dep1.version == '2.28.0'
        assert dep1.source == 'pip'
        
        dep2 = analyzer._parse_python_requirement('flask>=1.0.0')
        assert dep2.name == 'flask'
        assert dep2.version == '1.0.0'
        
        dep3 = analyzer._parse_python_requirement('django')
        assert dep3.name == 'django'
        assert dep3.version is None
    
    def test_parse_requirements_txt(self):
        """Test requirements.txt parsing."""
        analyzer = DependencyAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
# This is a comment
requests==2.28.0
flask>=1.0.0
django
# Another comment
pytest>=6.0.0
""")
            f.flush()
            
            try:
                deps = analyzer._parse_requirements_txt(Path(f.name))
                
                assert len(deps) == 4
                assert any(d.name == 'requests' and d.version == '2.28.0' for d in deps)
                assert any(d.name == 'flask' for d in deps)
                assert any(d.name == 'django' for d in deps)
                assert any(d.name == 'pytest' for d in deps)
                
            finally:
                os.unlink(f.name)
    
    def test_parse_package_json(self):
        """Test package.json parsing."""
        analyzer = DependencyAnalyzer()
        
        package_json_content = {
            "name": "test-project",
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.21"
            },
            "devDependencies": {
                "jest": "^28.0.0"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(package_json_content, f)
            f.flush()
            
            try:
                deps = analyzer._parse_package_json(Path(f.name))
                
                assert len(deps) == 3
                assert any(d.name == 'express' and d.version == '^4.18.0' for d in deps)
                assert any(d.name == 'lodash' for d in deps)
                assert any(d.name == 'jest' for d in deps)
                
            finally:
                os.unlink(f.name)
    
    def test_deduplicate_dependencies(self):
        """Test dependency deduplication."""
        analyzer = DependencyAnalyzer()
        
        deps = [
            DependencyInfo(name='requests', version='2.28.0', source='pip'),
            DependencyInfo(name='flask', version='1.0.0', source='pip'),
            DependencyInfo(name='requests', version='2.28.1', source='pip'),  # Duplicate
        ]
        
        unique_deps = analyzer._deduplicate_dependencies(deps)
        
        assert len(unique_deps) == 2
        assert unique_deps[0].name == 'requests'
        assert unique_deps[1].name == 'flask'


class TestProjectAnalyzer:
    """Test project analyzer functionality."""
    
    def test_project_analyzer_initialization(self):
        """Test project analyzer initialization."""
        analyzer = ProjectAnalyzer()
        
        assert analyzer.file_scanner is not None
        assert analyzer.language_detector is not None
        assert analyzer.dependency_analyzer is not None
    
    def test_detect_project_type(self):
        """Test project type detection."""
        analyzer = ProjectAnalyzer()
        
        # Mock files and dependencies for web application
        files = [
            FileInfo(path='app.py', absolute_path='/app.py', language='python'),
            FileInfo(path='templates/index.html', absolute_path='/templates/index.html'),
        ]
        
        dependencies = [
            DependencyInfo(name='flask', version='2.0.0', source='pip'),
        ]
        
        project_type = analyzer._detect_project_type(Path('/test'), files, dependencies)
        
        assert project_type == ProjectType.WEB_APPLICATION
    
    def test_identify_architecture_pattern(self):
        """Test architecture pattern identification."""
        analyzer = ProjectAnalyzer()
        
        # Mock files for MVC pattern
        files = [
            FileInfo(path='models/user.py', absolute_path='/models/user.py'),
            FileInfo(path='views/user_view.py', absolute_path='/views/user_view.py'),
            FileInfo(path='controllers/user_controller.py', absolute_path='/controllers/user_controller.py'),
        ]
        
        pattern = analyzer._identify_architecture_pattern(Path('/test'), files)
        
        assert pattern == 'MVC'
    
    def test_find_entry_points(self):
        """Test entry point detection."""
        analyzer = ProjectAnalyzer()
        
        files = [
            FileInfo(path='main.py', absolute_path='/main.py'),
            FileInfo(path='app.py', absolute_path='/app.py'),
            FileInfo(path='utils.py', absolute_path='/utils.py'),
        ]
        
        entry_points = analyzer._find_entry_points(files, ProjectType.WEB_APPLICATION)
        
        assert 'main.py' in entry_points
        assert 'app.py' in entry_points
        assert 'utils.py' not in entry_points
    
    def test_get_project_languages(self):
        """Test project language extraction."""
        analyzer = ProjectAnalyzer()
        
        files = [
            FileInfo(path='test.py', absolute_path='/test.py', language='python'),
            FileInfo(path='test.js', absolute_path='/test.js', language='javascript'),
            FileInfo(path='test.py', absolute_path='/test2.py', language='python'),  # Duplicate
        ]
        
        languages = analyzer._get_project_languages(files)
        
        assert 'python' in languages
        assert 'javascript' in languages
        assert len(languages) == 2  # No duplicates
    
    @pytest.mark.asyncio
    async def test_calculate_total_lines(self):
        """Test total lines calculation."""
        analyzer = ProjectAnalyzer()
        
        files = [
            FileInfo(path='test1.py', absolute_path='/test1.py', language='python', size=1000),
            FileInfo(path='test2.js', absolute_path='/test2.js', language='javascript', size=500),
        ]
        
        total_lines = await analyzer._calculate_total_lines(files)
        
        assert total_lines > 0
        assert total_lines == (1000 // 50) + (500 // 50)  # Rough estimate
    
    def test_get_analysis_summary(self):
        """Test analysis summary generation."""
        analyzer = ProjectAnalyzer()
        
        from ai_code_audit.core.models import ProjectInfo
        
        project_info = ProjectInfo(
            path='/test',
            name='test_project',
            project_type=ProjectType.WEB_APPLICATION,
            files=[
                FileInfo(path='test.py', absolute_path='/test.py', language='python', size=1000),
            ],
            dependencies=[
                DependencyInfo(name='flask', version='2.0.0', source='pip'),
            ],
            entry_points=['app.py'],
            languages=['python'],
            architecture_pattern='MVC',
            total_lines=100,
        )
        
        summary = analyzer.get_analysis_summary(project_info)
        
        assert summary['project_name'] == 'test_project'
        assert summary['project_type'] == 'web_application'
        assert summary['total_files'] == 1
        assert summary['total_lines'] == 100
        assert summary['languages'] == ['python']
        assert summary['dependencies_count'] == 1
        assert summary['architecture_pattern'] == 'MVC'


if __name__ == "__main__":
    pytest.main([__file__])
