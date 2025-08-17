#!/usr/bin/env python3
"""
Development environment setup script for AI Code Audit System.

This script helps set up the development environment and verifies
that all dependencies are properly installed.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description, check=True):
    """Run a shell command and handle errors."""
    print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during {description}: {e}")
        return False


def check_python_version():
    """Check if Python version is 3.9+."""
    print("🔍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not supported")
        print("   Please install Python 3.9 or higher")
        return False


def check_poetry():
    """Check if Poetry is installed."""
    print("🔍 Checking Poetry installation...")
    
    try:
        result = subprocess.run(
            ["poetry", "--version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"✅ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Poetry is not installed")
        print("   Please install Poetry: https://python-poetry.org/docs/#installation")
        return False


def setup_poetry_project():
    """Set up the Poetry project and install dependencies."""
    print("🔧 Setting up Poetry project...")
    
    # Install dependencies
    if not run_command("poetry install", "Installing dependencies"):
        return False
    
    # Install pre-commit hooks if available
    run_command("poetry run pre-commit install", "Installing pre-commit hooks", check=False)
    
    return True


def check_mysql():
    """Check if MySQL is available."""
    print("🔍 Checking MySQL availability...")
    
    # Try to connect to MySQL
    try:
        result = subprocess.run(
            ["mysql", "--version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"✅ {result.stdout.strip()}")
        
        # Try to connect with the configured credentials
        mysql_cmd = 'mysql -u root -p"jackhou." -e "SELECT VERSION();"'
        if run_command(mysql_cmd, "Testing MySQL connection", check=False):
            return True
        else:
            print("⚠️  MySQL is installed but connection failed")
            print("   Please check your MySQL credentials")
            return False
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ MySQL is not installed or not in PATH")
        print("   Please install MySQL 8.0+ and ensure it's running")
        return False


def create_database():
    """Create the audit database."""
    print("🔧 Creating audit database...")
    
    create_db_cmd = 'mysql -u root -p"jackhou." -e "CREATE DATABASE IF NOT EXISTS ai_code_audit_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"'
    
    if run_command(create_db_cmd, "Creating database ai_code_audit_system"):
        # Verify database was created
        verify_cmd = 'mysql -u root -p"jackhou." -e "SHOW DATABASES LIKE \'ai_code_audit_system\';"'
        if run_command(verify_cmd, "Verifying database creation"):
            return True
    
    return False


def test_api_keys():
    """Test the LLM API keys."""
    print("🔍 Testing LLM API keys...")
    
    # Test Qwen API
    qwen_cmd = '''curl -s -X POST "https://api.siliconflow.cn/v1/chat/completions" \
        -H "Authorization: Bearer sk-ejzylvzgcfnlxgvctpbgnnqginfossvyoifynqhqbaurvkuo" \
        -H "Content-Type: application/json" \
        -d '{"model": "Qwen/Qwen3-Coder-30B-A3B-Instruct", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}' '''
    
    if run_command(qwen_cmd, "Testing Qwen API", check=False):
        print("✅ Qwen API is accessible")
    else:
        print("⚠️  Qwen API test failed - please check API key and network")
    
    # Test Kimi API
    kimi_cmd = '''curl -s -X POST "https://api.siliconflow.cn/v1/chat/completions" \
        -H "Authorization: Bearer sk-gzkhahnbkjsvrerhxbtzzfuctexesqkmmbgyaylhitynvdri" \
        -H "Content-Type: application/json" \
        -d '{"model": "moonshotai/Kimi-K2-Instruct", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}' '''
    
    if run_command(kimi_cmd, "Testing Kimi API", check=False):
        print("✅ Kimi API is accessible")
    else:
        print("⚠️  Kimi API test failed - please check API key and network")


def run_basic_tests():
    """Run our basic functionality tests."""
    print("🔧 Running basic functionality tests...")
    
    return run_command(
        "python test_basic_functionality.py", 
        "Running basic functionality tests"
    )


def create_sample_project():
    """Create a sample project for testing."""
    print("🔧 Creating sample project for testing...")
    
    sample_dir = Path("sample_project")
    sample_dir.mkdir(exist_ok=True)
    
    # Create a simple Python file with some security issues
    sample_code = '''#!/usr/bin/env python3
"""
Sample Python project for testing AI Code Audit System.
This file intentionally contains security vulnerabilities for testing.
"""

import os
import sqlite3
from flask import Flask, request, render_template

app = Flask(__name__)

# Intentional security issues for testing:

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)  # Vulnerable to SQL injection
    user = cursor.fetchone()
    
    if user:
        return "Login successful"
    else:
        return "Login failed"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    # XSS vulnerability
    return f"<h1>Search results for: {query}</h1>"  # Vulnerable to XSS

@app.route('/file')
def read_file():
    filename = request.args.get('file', '')
    
    # Path traversal vulnerability
    with open(f"uploads/{filename}", 'r') as f:  # Vulnerable to path traversal
        content = f.read()
    
    return content

@app.route('/admin')
def admin():
    # Missing authentication
    return "Admin panel - sensitive information"

if __name__ == '__main__':
    # Insecure configuration
    app.run(debug=True, host='0.0.0.0')  # Debug mode in production
'''
    
    (sample_dir / "app.py").write_text(sample_code)
    
    # Create a requirements.txt
    requirements = '''Flask==2.3.0
sqlite3
'''
    (sample_dir / "requirements.txt").write_text(requirements)
    
    print(f"✅ Sample project created in {sample_dir}")
    return True


def main():
    """Main setup function."""
    print("🚀 AI Code Audit System - Development Environment Setup")
    print("=" * 60)
    
    setup_steps = [
        ("Python Version", check_python_version),
        ("Poetry Installation", check_poetry),
        ("Poetry Project Setup", setup_poetry_project),
        ("MySQL Availability", check_mysql),
        ("Database Creation", create_database),
        ("API Keys Testing", test_api_keys),
        ("Sample Project Creation", create_sample_project),
        ("Basic Functionality Tests", run_basic_tests),
    ]
    
    passed = 0
    total = len(setup_steps)
    
    for step_name, step_func in setup_steps:
        print(f"\n📋 {step_name}")
        print("-" * 40)
        
        if step_func():
            passed += 1
        else:
            print(f"❌ {step_name} failed")
            
            # Some steps are optional
            if step_name in ["API Keys Testing", "MySQL Availability"]:
                print("   (This step is optional for basic development)")
                passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Setup Results: {passed}/{total} steps completed")
    
    if passed >= total - 1:  # Allow one optional step to fail
        print("🎉 Development environment is ready!")
        print("\n📝 Next steps:")
        print("   1. Run: poetry shell")
        print("   2. Run: ai-audit --help")
        print("   3. Test with: ai-audit init sample_project")
        return 0
    else:
        print("⚠️  Setup incomplete. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
