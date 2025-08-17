#!/usr/bin/env python3
"""
Configuration system test script for AI Code Audit System.

This script tests the configuration management functionality including
file loading, environment variables, and configuration validation.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_config_loading():
    """Test configuration loading from file."""
    print("🔍 Testing configuration loading...")
    
    try:
        from ai_code_audit.core.config import get_config, ConfigManager
        
        # Test loading configuration
        config = get_config()
        print("✅ Configuration loaded successfully")
        
        # Test database configuration
        print(f"✅ Database: {config.database.host}:{config.database.port}/{config.database.database}")
        
        # Test LLM configuration
        if config.llm.qwen:
            print(f"✅ Qwen provider configured: {config.llm.qwen.enabled}")
            print(f"   API Key: {'*' * 20 + config.llm.qwen.api_key[-8:] if config.llm.qwen.api_key else 'Not set'}")
        
        if config.llm.kimi:
            print(f"✅ Kimi provider configured: {config.llm.kimi.enabled}")
            print(f"   API Key: {'*' * 20 + config.llm.kimi.api_key[-8:] if config.llm.kimi.api_key else 'Not set'}")
        
        # Test audit configuration
        print(f"✅ Audit config: max {config.audit.max_files_per_audit} files, {len(config.audit.supported_languages)} languages")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


def test_environment_override():
    """Test environment variable override."""
    print("\n🔍 Testing environment variable override...")
    
    try:
        # Set test environment variables
        original_qwen_key = os.environ.get('QWEN_API_KEY')
        original_kimi_key = os.environ.get('KIMI_API_KEY')
        
        os.environ['QWEN_API_KEY'] = 'test-qwen-key-from-env'
        os.environ['KIMI_API_KEY'] = 'test-kimi-key-from-env'
        os.environ['LOG_LEVEL'] = 'DEBUG'
        
        # Reload configuration
        from ai_code_audit.core.config import reload_config
        config = reload_config()
        
        # Check if environment variables took effect
        if config.llm.qwen and config.llm.qwen.api_key == 'test-qwen-key-from-env':
            print("✅ Environment variable override works for Qwen")
        else:
            print("❌ Environment variable override failed for Qwen")
        
        if config.llm.kimi and config.llm.kimi.api_key == 'test-kimi-key-from-env':
            print("✅ Environment variable override works for Kimi")
        else:
            print("❌ Environment variable override failed for Kimi")
        
        if config.log_level == 'DEBUG':
            print("✅ Environment variable override works for log level")
        else:
            print("❌ Environment variable override failed for log level")
        
        # Restore original environment
        if original_qwen_key:
            os.environ['QWEN_API_KEY'] = original_qwen_key
        else:
            os.environ.pop('QWEN_API_KEY', None)
        
        if original_kimi_key:
            os.environ['KIMI_API_KEY'] = original_kimi_key
        else:
            os.environ.pop('KIMI_API_KEY', None)
        
        os.environ.pop('LOG_LEVEL', None)
        
        return True
        
    except Exception as e:
        print(f"❌ Environment override test failed: {e}")
        return False


def test_config_validation():
    """Test configuration validation."""
    print("\n🔍 Testing configuration validation...")
    
    try:
        from ai_code_audit.core.config import ConfigManager, AppConfig, DatabaseConfig
        
        # Test with invalid database config
        try:
            config = AppConfig()
            config.database.host = ""  # Invalid empty host
            
            manager = ConfigManager()
            manager._validate_config(config)
            print("❌ Validation should have failed for empty host")
            return False
            
        except ValueError as e:
            print("✅ Validation correctly caught empty host")
        
        # Test with valid config
        config = AppConfig()
        config.database = DatabaseConfig(
            host="localhost",
            username="test",
            database="test_db"
        )
        
        manager = ConfigManager()
        manager._validate_config(config)
        print("✅ Validation passed for valid config")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


def test_config_file_discovery():
    """Test configuration file discovery."""
    print("\n🔍 Testing configuration file discovery...")
    
    try:
        from ai_code_audit.core.config import ConfigManager
        
        manager = ConfigManager()
        config_path = manager._find_config_file()
        
        if config_path:
            print(f"✅ Found configuration file: {config_path}")
            
            # Check if file exists
            if Path(config_path).exists():
                print("✅ Configuration file exists and is readable")
            else:
                print("❌ Configuration file path found but file doesn't exist")
                return False
        else:
            print("⚠️  No configuration file found (using defaults)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration file discovery failed: {e}")
        return False


def test_llm_manager_integration():
    """Test LLM manager integration with configuration."""
    print("\n🔍 Testing LLM manager integration...")
    
    try:
        from ai_code_audit.llm.manager import LLMManager
        
        # Initialize LLM manager (should use configuration system)
        manager = LLMManager()
        
        print(f"✅ LLM manager initialized with {len(manager.providers)} providers")
        
        # Check provider configuration
        for name, provider in manager.providers.items():
            config = manager.provider_configs[name]
            print(f"   {name}: enabled={config.enabled}, priority={config.priority}")
        
        # Test provider stats
        stats = manager.get_provider_stats()
        print(f"✅ Provider stats: {list(stats.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM manager integration test failed: {e}")
        return False


def test_cli_config_command():
    """Test CLI config command."""
    print("\n🔍 Testing CLI config command...")
    
    try:
        import subprocess
        
        # Test config command
        result = subprocess.run([
            sys.executable, '-m', 'ai_code_audit.cli.main', 'config'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ CLI config command executed successfully")
            
            # Check if output contains expected sections
            output = result.stdout
            if "Database Configuration" in output:
                print("✅ Database configuration displayed")
            if "LLM Configuration" in output:
                print("✅ LLM configuration displayed")
            if "Audit Configuration" in output:
                print("✅ Audit configuration displayed")
            
        else:
            print(f"❌ CLI config command failed: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI config command test failed: {e}")
        return False


def main():
    """Run all configuration system tests."""
    print("🚀 AI Code Audit System - Configuration System Test")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Environment Override", test_environment_override),
        ("Configuration Validation", test_config_validation),
        ("Config File Discovery", test_config_file_discovery),
        ("LLM Manager Integration", test_llm_manager_integration),
        ("CLI Config Command", test_cli_config_command),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Configuration System Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All configuration tests passed! Configuration system is ready.")
        print("\n📝 Configuration is loaded from:")
        print("   1. config.yaml (if exists)")
        print("   2. Environment variables (override)")
        print("   3. Default values (fallback)")
        print("\n🔧 Available commands:")
        print("   python -m ai_code_audit.cli.main config")
        print("   python -m ai_code_audit.cli.main config --show-keys")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
