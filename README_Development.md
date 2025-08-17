# AI Code Audit System - Development Guide

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Run the automated setup script
python setup_dev_environment.py

# Activate Poetry environment
poetry shell

# Test basic functionality
python test_basic_functionality.py
```

### 2. Test CLI Commands
```bash
# Show help
ai-audit --help

# Initialize a project
ai-audit init sample_project

# Test other commands (not yet implemented)
ai-audit scan --help
ai-audit audit --help
ai-audit report --help
```

## 📁 Current Project Structure

```
ai-code-audit/
├── pyproject.toml                    # ✅ Poetry configuration
├── ai_code_audit/
│   ├── __init__.py                   # ✅ Package initialization
│   ├── core/
│   │   ├── __init__.py               # ✅ Core module exports
│   │   ├── models.py                 # ✅ Pydantic data models
│   │   ├── exceptions.py             # ✅ Custom exceptions
│   │   └── constants.py              # ✅ Constants and mappings
│   ├── cli/
│   │   ├── __init__.py               # ✅ CLI module exports
│   │   └── main.py                   # ✅ Main CLI commands
│   ├── database/
│   │   ├── __init__.py               # ✅ Database module exports
│   │   ├── connection.py             # ✅ Async database connection
│   │   ├── models.py                 # ✅ SQLAlchemy ORM models
│   │   └── services.py               # ✅ Database service layer
│   ├── analysis/
│   │   ├── __init__.py               # ✅ Analysis module exports
│   │   ├── file_scanner.py           # ✅ File discovery and scanning
│   │   ├── language_detector.py      # ✅ Advanced language detection
│   │   ├── dependency_analyzer.py    # ✅ Dependency analysis
│   │   └── project_analyzer.py       # ✅ Comprehensive project analysis
│   └── llm/
│       ├── __init__.py               # ✅ LLM module exports
│       ├── base.py                   # ✅ Base LLM classes and models
│       ├── qwen_provider.py          # ✅ Qwen (SiliconFlow) provider
│       ├── kimi_provider.py          # ✅ Kimi (MoonshotAI) provider
│       ├── manager.py                # ✅ LLM manager with load balancing
│       └── prompts.py                # ✅ Prompt templates and management
├── tests/
│   ├── __init__.py                   # ✅ Test package
│   └── unit/
│       ├── __init__.py               # ✅ Unit tests package
│       ├── test_models.py            # ✅ Model validation tests
│       ├── test_database.py          # ✅ Database functionality tests
│       ├── test_project_analyzer.py  # ✅ Project analysis tests
│       └── test_llm.py               # ✅ LLM integration tests
├── scripts/
│   ├── __init__.py                   # ✅ Scripts package
│   └── init_database.py             # ✅ Database initialization script
├── test_basic_functionality.py       # ✅ Development test script
├── test_database_functionality.py    # ✅ Database integration test script
├── test_project_scanner.py           # ✅ Project analysis test script
├── test_llm_integration.py           # ✅ LLM integration test script
├── check_database_status.py          # ✅ Database status check script
├── setup_dev_environment.py          # ✅ Environment setup script
└── sample_project/                   # ✅ Test project with vulnerabilities
    ├── app.py                        # Sample Flask app with security issues
    └── requirements.txt              # Sample dependencies
```

## ✅ Completed Features

### Core Infrastructure
- [x] **Project Structure**: Complete Poetry-based project setup
- [x] **Data Models**: Comprehensive Pydantic models with validation
- [x] **Exception Handling**: Custom exception hierarchy
- [x] **Constants**: Security rules, language mappings, CWE/OWASP mappings
- [x] **CLI Framework**: Click-based command structure with Rich output

### CLI Commands (Basic Structure)
- [x] **ai-audit init**: Project initialization with basic validation
- [x] **ai-audit scan**: Command structure (implementation pending)
- [x] **ai-audit audit**: Command structure (implementation pending)  
- [x] **ai-audit report**: Command structure (implementation pending)
- [x] **ai-audit version**: Version information

### Database Infrastructure
- [x] **SQLAlchemy Models**: Complete ORM models with relationships
- [x] **Async Connection**: MySQL connection with aiomysql
- [x] **Service Layer**: High-level database operations
- [x] **Migration Support**: Database initialization and table creation

### Testing Infrastructure
- [x] **Unit Tests**: Model validation and database functionality tests
- [x] **Test Scripts**: Automated testing and environment validation
- [x] **Sample Project**: Test project with intentional vulnerabilities

## 🔧 Development Status

### Phase 1: Basic Framework ✅ (100% Complete)
- [x] Project initialization ✅
- [x] Core data models ✅
- [x] CLI framework ✅
- [x] Configuration management (basic) ✅
- [x] Database integration ✅

### Phase 2: Core Functionality ✅ (67% Complete)
- [x] Project scanner ✅
- [x] LLM integration ✅
- [ ] Audit engine (next)

### Project Analysis Infrastructure
- [x] **File Scanner**: Multi-language file discovery and analysis
- [x] **Language Detector**: Advanced language detection with heuristics
- [x] **Dependency Analyzer**: Package manager integration (pip, npm, go, cargo)
- [x] **Project Analyzer**: Comprehensive project structure analysis
- [x] **CLI Integration**: `ai-audit scan` command with multiple output formats

### LLM Integration Infrastructure
- [x] **Base LLM Framework**: Abstract provider interface and data models
- [x] **Qwen Provider**: SiliconFlow API integration with retry logic
- [x] **Kimi Provider**: MoonshotAI API integration with long context support
- [x] **LLM Manager**: Multi-provider management with load balancing and fallback
- [x] **Prompt System**: Template-based prompt generation for different analysis types
- [x] **CLI Integration**: `ai-audit audit` command with AI-powered analysis

### Next Immediate Tasks
1. **Audit Engine**: Core audit logic and session management
2. **Code Analysis**: AST parsing and semantic analysis
3. **Report Generation**: Structured report generation and export

## 🧪 Testing

### Run All Tests
```bash
# Unit tests
poetry run pytest tests/unit/ -v

# Basic functionality test
python test_basic_functionality.py

# Database functionality test
python test_database_functionality.py

# Project scanner test
python test_project_scanner.py

# LLM integration test
python test_llm_integration.py

# Initialize database
python scripts/init_database.py

# CLI testing
python -m ai_code_audit.cli.main --help
python -m ai_code_audit.cli.main scan .
python -m ai_code_audit.cli.main scan . --save-to-db
python -m ai_code_audit.cli.main scan . --output-format json

# AI audit testing (requires API keys)
export QWEN_API_KEY=your_qwen_key
export KIMI_API_KEY=your_kimi_key
python -m ai_code_audit.cli.main audit . --max-files 2
python -m ai_code_audit.cli.main audit . --template code_review --max-files 1
```

### Test Coverage
Current test coverage focuses on:
- ✅ Data model validation
- ✅ Exception handling
- ✅ CLI command structure
- ✅ Import verification

## 🔍 Code Quality

### Linting and Formatting
```bash
# Format code
poetry run black ai_code_audit/ tests/

# Sort imports
poetry run isort ai_code_audit/ tests/

# Lint code
poetry run flake8 ai_code_audit/ tests/

# Type checking
poetry run mypy ai_code_audit/
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## 🐛 Known Issues

### Current Limitations
1. **Code Analysis**: AST parsing and semantic analysis not implemented
2. **Audit Engine**: Core audit logic not implemented
3. **Session Management**: Audit session workflow not implemented
4. **Report Generation**: Structured report generation not implemented

### Development Notes
- Project scanning fully functional with CLI integration
- Database fully integrated and tested
- LLM integration complete with multi-provider support
- AI-powered audit functionality ready for use with API keys
- Comprehensive test coverage for all core components

## 📝 Development Workflow

### Adding New Features
1. **Write Tests First**: Add tests in `tests/unit/`
2. **Implement Feature**: Add code in appropriate module
3. **Test Locally**: Run `python test_basic_functionality.py`
4. **Update CLI**: Add/modify CLI commands if needed
5. **Document**: Update this README

### Debugging
```bash
# Enable debug mode
ai-audit --debug init sample_project

# Verbose output
ai-audit --verbose scan

# Python debugging
python -c "from ai_code_audit.core.models import FileInfo; print(FileInfo.__doc__)"
```

## 🎯 Next Development Session

### Priority Tasks
1. **Database Integration** (2-3 hours)
   - Create SQLAlchemy models
   - Set up async database connection
   - Test database operations

2. **Project Scanner** (3-4 hours)
   - Implement file discovery
   - Add language detection
   - Create project analysis logic

3. **LLM Integration** (2-3 hours)
   - Create API adapters
   - Test API connections
   - Implement basic request/response handling

### Success Criteria
- Database connection working
- Project scanning functional
- LLM API calls successful
- All tests passing

## 🚨 Important Notes

### Security
- API keys are currently hardcoded for development
- Sample project contains intentional vulnerabilities
- Database credentials are in configuration files

### Performance
- No optimization implemented yet
- Single-threaded processing
- No caching mechanisms

### Dependencies
- Requires Python 3.9+
- Requires MySQL 8.0+
- Requires internet connection for LLM APIs

---

**Status**: ✅ Ready for next development phase
**Last Updated**: Current session
**Next Milestone**: Database integration and project scanning
