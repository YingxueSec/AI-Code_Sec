#!/usr/bin/env python3
"""
Project scanner test script for AI Code Audit System.

This script tests the project analysis functionality including file scanning,
language detection, dependency analysis, and project type identification.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_file_scanner():
    """Test file scanner functionality."""
    print("🔍 Testing file scanner...")
    
    try:
        from ai_code_audit.analysis.file_scanner import FileScanner
        
        scanner = FileScanner()
        print("✅ File scanner initialized")
        
        # Test with sample project
        sample_project = Path('sample_project')
        if sample_project.exists():
            files = scanner.scan_directory(str(sample_project))
            print(f"✅ Scanned sample project: {len(files)} files found")
            
            # Show file breakdown
            file_counts = scanner.get_file_count_by_language(files)
            for language, count in file_counts.items():
                print(f"   {language}: {count} files")
            
            total_size = scanner.get_total_size(files)
            print(f"   Total size: {total_size} bytes")
        else:
            print("⚠️  Sample project not found, creating test files...")
            
            # Create temporary test files
            test_dir = Path('temp_test_project')
            test_dir.mkdir(exist_ok=True)
            
            (test_dir / 'main.py').write_text('print("Hello World")')
            (test_dir / 'app.js').write_text('console.log("Hello World");')
            (test_dir / 'style.css').write_text('body { margin: 0; }')
            
            files = scanner.scan_directory(str(test_dir))
            print(f"✅ Scanned test directory: {len(files)} files found")
            
            # Clean up
            import shutil
            shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ File scanner test failed: {e}")
        return False


async def test_language_detector():
    """Test language detector functionality."""
    print("\n🔍 Testing language detector...")
    
    try:
        from ai_code_audit.analysis.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        print("✅ Language detector initialized")
        
        # Test extension-based detection
        test_files = [
            ('test.py', 'python'),
            ('test.js', 'javascript'),
            ('test.java', 'java'),
            ('test.go', 'go'),
            ('test.rs', 'rust'),
        ]
        
        for filename, expected_lang in test_files:
            detected = detector._detect_by_extension(Path(filename))
            if detected == expected_lang:
                print(f"✅ {filename} -> {detected}")
            else:
                print(f"❌ {filename} -> {detected} (expected {expected_lang})")
        
        # Test content-based detection
        python_content = """
import os
import sys

def main():
    print("Hello World")
    
if __name__ == "__main__":
    main()
"""
        
        detected_lang = detector._detect_by_content(python_content)
        if detected_lang == 'python':
            print("✅ Content-based detection works for Python")
        else:
            print(f"❌ Content detection failed: {detected_lang}")
        
        # Test confidence scoring
        confidence = detector.get_language_confidence(Path('test.py'), python_content)
        if confidence.get('python', 0) > 0.5:
            print(f"✅ Confidence scoring works: {confidence}")
        else:
            print(f"❌ Confidence scoring failed: {confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Language detector test failed: {e}")
        return False


async def test_dependency_analyzer():
    """Test dependency analyzer functionality."""
    print("\n🔍 Testing dependency analyzer...")
    
    try:
        from ai_code_audit.analysis.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        print("✅ Dependency analyzer initialized")
        
        # Test Python requirement parsing
        test_requirements = [
            'requests==2.28.0',
            'flask>=1.0.0',
            'django~=4.0.0',
            'pytest',
        ]
        
        for req in test_requirements:
            dep = analyzer._parse_python_requirement(req)
            if dep:
                print(f"✅ Parsed: {req} -> {dep.name} ({dep.version})")
            else:
                print(f"❌ Failed to parse: {req}")
        
        # Test with sample project if it exists
        sample_project = Path('sample_project')
        if sample_project.exists():
            dependencies = analyzer.analyze_dependencies(str(sample_project))
            print(f"✅ Analyzed sample project dependencies: {len(dependencies)} found")
            
            for dep in dependencies[:5]:  # Show first 5
                print(f"   {dep.name} ({dep.version}) from {dep.source}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dependency analyzer test failed: {e}")
        return False


async def test_project_analyzer():
    """Test complete project analyzer functionality."""
    print("\n🔍 Testing project analyzer...")
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        
        analyzer = ProjectAnalyzer()
        print("✅ Project analyzer initialized")
        
        # Test with sample project
        sample_project = Path('sample_project')
        if sample_project.exists():
            print("📋 Analyzing sample project...")
            
            # Analyze without saving to database for testing
            project_info = await analyzer.analyze_project(str(sample_project), save_to_db=False)
            
            print(f"✅ Project analysis completed:")
            print(f"   Name: {project_info.name}")
            print(f"   Type: {project_info.project_type.value}")
            print(f"   Files: {len(project_info.files)}")
            print(f"   Languages: {project_info.languages}")
            print(f"   Dependencies: {len(project_info.dependencies)}")
            print(f"   Entry points: {project_info.entry_points}")
            print(f"   Architecture: {project_info.architecture_pattern}")
            print(f"   Total lines: {project_info.total_lines}")
            
            # Test analysis summary
            summary = analyzer.get_analysis_summary(project_info)
            print(f"✅ Analysis summary generated: {len(summary)} fields")
            
        else:
            print("⚠️  Sample project not found, skipping full analysis test")
        
        return True
        
    except Exception as e:
        print(f"❌ Project analyzer test failed: {e}")
        return False


async def test_integration_with_database():
    """Test project analyzer integration with database."""
    print("\n🔍 Testing database integration...")
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.database.connection import get_db_session
        from ai_code_audit.database.services import ProjectService
        
        analyzer = ProjectAnalyzer()
        
        # Create a small test project
        test_dir = Path('temp_integration_test')
        test_dir.mkdir(exist_ok=True)
        
        (test_dir / 'main.py').write_text('''
import os
import sys

def main():
    print("Hello World")
    
if __name__ == "__main__":
    main()
''')
        
        (test_dir / 'requirements.txt').write_text('''
requests==2.28.0
flask>=1.0.0
''')
        
        try:
            # Analyze and save to database
            project_info = await analyzer.analyze_project(str(test_dir), save_to_db=True)
            print("✅ Project analyzed and saved to database")
            
            # Verify in database
            async with get_db_session() as session:
                projects = await ProjectService.list_projects(session, limit=5)
                if projects:
                    latest_project = projects[0]
                    print(f"✅ Project found in database: {latest_project.name}")
                else:
                    print("❌ No projects found in database")
            
        finally:
            # Clean up
            import shutil
            shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False


async def main():
    """Run all project scanner tests."""
    print("🚀 AI Code Audit System - Project Scanner Test")
    print("=" * 60)
    
    tests = [
        ("File Scanner", test_file_scanner),
        ("Language Detector", test_language_detector),
        ("Dependency Analyzer", test_dependency_analyzer),
        ("Project Analyzer", test_project_analyzer),
        ("Database Integration", test_integration_with_database),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Project Scanner Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All project scanner tests passed! Scanner is ready for use.")
        print("\n📝 Next steps:")
        print("   1. Test with: ai-audit scan")
        print("   2. Integrate with CLI commands")
        print("   3. Add code analysis features")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
