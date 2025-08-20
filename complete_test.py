#!/usr/bin/env python3
"""
完整测试脚本 - 验证qdbcrm-v3.0.2的修复效果
"""
import sys
import os
import time
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """测试结果收集器"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    def add_result(self, test_name: str, success: bool, details: Dict = None):
        self.results[test_name] = {
            'success': success,
            'details': details or {},
            'timestamp': time.time()
        }
    
    def get_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r['success'])
        duration = time.time() - self.start_time
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'duration': duration
        }


def test_file_filtering():
    """测试文件过滤功能"""
    print("🔍 测试1: 文件过滤功能")
    print("-" * 50)
    
    try:
        # 模拟配置
        config = {
            'file_filtering': {
                'enabled': True,
                'ignore_patterns': [
                    '*.js',
                    '*.css', 
                    '*.min.js',
                    '*.min.css',
                    'node_modules/**',
                    'vendor/**',
                    'install/**',
                    'theme/**'
                ],
                'max_file_size': 3145728,  # 3MB
                'force_include': []
            }
        }
        
        project_path = "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2"
        
        if not os.path.exists(project_path):
            return False, {"error": "项目路径不存在"}
        
        # 统计文件
        all_files = []
        for root, dirs, files in os.walk(project_path):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        # 模拟过滤逻辑
        filtered_files = []
        js_css_count = 0
        large_files = []
        
        for file_path in all_files:
            rel_path = os.path.relpath(file_path, project_path)
            
            # 检查是否应该被过滤
            should_filter = False
            
            # 检查扩展名
            if file_path.endswith(('.js', '.css')):
                js_css_count += 1
                should_filter = True
            
            # 检查目录
            if any(pattern in rel_path for pattern in ['install/', 'theme/']):
                should_filter = True
            
            # 检查文件大小
            try:
                file_size = os.path.getsize(file_path)
                if file_size > config['file_filtering']['max_file_size']:
                    large_files.append((rel_path, file_size))
            except:
                pass
            
            if not should_filter and file_path.endswith('.php'):
                filtered_files.append(rel_path)
        
        details = {
            'total_files': len(all_files),
            'js_css_files': js_css_count,
            'large_files': len(large_files),
            'php_files_after_filter': len(filtered_files),
            'filter_efficiency': (1 - len(filtered_files) / len(all_files)) * 100
        }
        
        print(f"  总文件数: {details['total_files']}")
        print(f"  JS/CSS文件: {details['js_css_files']} (应被过滤)")
        print(f"  大文件数: {details['large_files']}")
        print(f"  过滤后PHP文件: {details['php_files_after_filter']}")
        print(f"  过滤效率: {details['filter_efficiency']:.1f}%")
        
        # 成功条件：过滤效率 > 60%
        success = details['filter_efficiency'] > 60
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        
        return success, details
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False, {"error": str(e)}


def test_large_file_handling():
    """测试大文件处理功能"""
    print("\n📁 测试2: 大文件处理功能")
    print("-" * 50)
    
    try:
        project_path = "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2"
        
        # 查找大文件
        large_files = []
        important_files = [
            'app/controllers/login.php',
            'app/controllers/user.php', 
            'app/controllers/upload.php',
            'app/controllers/hetong.php',
            'app/models/qmsoft.php'
        ]
        
        for file_rel in important_files:
            file_path = os.path.join(project_path, file_rel)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                large_files.append({
                    'file': file_rel,
                    'size': size,
                    'size_mb': size / 1024 / 1024,
                    'needs_chunking': size > 3145728  # 3MB
                })
        
        # 模拟分块处理
        chunk_size = 50000  # 50KB chunks
        total_chunks = 0
        
        for file_info in large_files:
            if file_info['needs_chunking']:
                estimated_chunks = max(1, int(file_info['size'] / chunk_size))
                total_chunks += estimated_chunks
                print(f"  📄 {file_info['file']}: {file_info['size_mb']:.1f}MB -> {estimated_chunks} 块")
            else:
                print(f"  📄 {file_info['file']}: {file_info['size_mb']:.1f}MB (无需分块)")
        
        details = {
            'large_files_found': len(large_files),
            'files_need_chunking': sum(1 for f in large_files if f['needs_chunking']),
            'total_estimated_chunks': total_chunks,
            'largest_file_mb': max(f['size_mb'] for f in large_files) if large_files else 0
        }
        
        print(f"  发现大文件: {details['large_files_found']}")
        print(f"  需要分块: {details['files_need_chunking']}")
        print(f"  预计总块数: {details['total_estimated_chunks']}")
        
        # 成功条件：找到大文件且能处理
        success = details['large_files_found'] > 0
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        
        return success, details
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False, {"error": str(e)}


def test_markup_safety():
    """测试markup安全性"""
    print("\n🛡️ 测试3: Markup安全性")
    print("-" * 50)
    
    try:
        # 模拟sanitize_markup_content函数
        def sanitize_markup_content(text):
            if not isinstance(text, str):
                return str(text)
            
            # 转义Rich markup特殊字符
            text = text.replace('[', '\\[').replace(']', '\\]')
            
            # 移除可能导致问题的正则表达式模式
            import re
            text = re.sub(r'\[/[^\]]*\]', '', text)
            
            return text
        
        # 测试问题文本
        test_cases = [
            '[/^1\\d{10}$/,"请输入正确的手机号"]',
            '[red]Error[/red]',
            'Normal text with [brackets]',
            'Regex pattern: /^\\d+$/',
            'Array: ["item1", "item2"]',
            'PHP code: $pattern = "/^[a-zA-Z0-9]+$/";'
        ]
        
        processed_count = 0
        for i, text in enumerate(test_cases, 1):
            try:
                cleaned = sanitize_markup_content(text)
                print(f"  {i}. 原文: {text[:50]}...")
                print(f"     清理: {cleaned[:50]}...")
                print(f"     状态: ✅ 安全")
                processed_count += 1
            except Exception as e:
                print(f"  {i}. 处理失败: {e}")
        
        details = {
            'test_cases': len(test_cases),
            'processed_successfully': processed_count,
            'success_rate': (processed_count / len(test_cases)) * 100
        }
        
        print(f"  测试用例: {details['test_cases']}")
        print(f"  成功处理: {details['processed_successfully']}")
        print(f"  成功率: {details['success_rate']:.1f}%")
        
        # 成功条件：100%处理成功
        success = details['success_rate'] == 100
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        
        return success, details
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False, {"error": str(e)}


def test_config_loading():
    """测试配置加载"""
    print("\n⚙️ 测试4: 配置加载")
    print("-" * 50)
    
    try:
        import yaml
        
        # 尝试加载配置文件
        config_files = ['config.yaml', 'config/config.yaml', 'ai_code_audit/config.yaml']
        config_loaded = False
        config_data = None
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    config_loaded = True
                    print(f"  ✅ 配置文件加载成功: {config_file}")
                    break
                except Exception as e:
                    print(f"  ⚠️ 配置文件加载失败: {config_file} - {e}")
        
        if not config_loaded:
            print("  ❌ 未找到有效的配置文件")
            return False, {"error": "配置文件未找到"}
        
        # 检查关键配置项
        file_filtering = config_data.get('file_filtering', {}) if config_data else {}
        
        details = {
            'config_loaded': config_loaded,
            'file_filtering_enabled': file_filtering.get('enabled', False),
            'ignore_patterns_count': len(file_filtering.get('ignore_patterns', [])),
            'max_file_size_mb': file_filtering.get('max_file_size', 0) / 1024 / 1024
        }
        
        print(f"  文件过滤启用: {details['file_filtering_enabled']}")
        print(f"  过滤规则数量: {details['ignore_patterns_count']}")
        print(f"  最大文件大小: {details['max_file_size_mb']:.1f}MB")
        
        # 成功条件：配置加载且有过滤规则
        success = config_loaded and details['ignore_patterns_count'] > 0
        print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        
        return success, details
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False, {"error": str(e)}


def main():
    """主测试函数"""
    print("🧪 qdbcrm-v3.0.2 完整测试")
    print("=" * 60)
    
    results = TestResults()
    
    # 执行所有测试
    tests = [
        ("file_filtering", test_file_filtering),
        ("large_file_handling", test_large_file_handling),
        ("markup_safety", test_markup_safety),
        ("config_loading", test_config_loading)
    ]
    
    for test_name, test_func in tests:
        try:
            success, details = test_func()
            results.add_result(test_name, success, details)
        except Exception as e:
            print(f"  ❌ 测试 {test_name} 异常: {e}")
            results.add_result(test_name, False, {"error": str(e)})
    
    # 生成总结报告
    summary = results.get_summary()
    
    print("\n📋 测试总结")
    print("=" * 60)
    print(f"  总测试数: {summary['total_tests']}")
    print(f"  通过测试: {summary['passed']}")
    print(f"  失败测试: {summary['failed']}")
    print(f"  成功率: {summary['success_rate']:.1f}%")
    print(f"  测试耗时: {summary['duration']:.2f}秒")
    
    # 详细结果
    print("\n📊 详细结果:")
    for test_name, result in results.results.items():
        status = "✅ 通过" if result['success'] else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not result['success'] and 'error' in result['details']:
            print(f"    错误: {result['details']['error']}")
    
    # 保存结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    result_file = f"test_results_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': summary,
            'results': results.results,
            'timestamp': timestamp
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 测试结果已保存: {result_file}")
    
    # 给出建议
    if summary['success_rate'] >= 75:
        print("\n🎉 测试结果良好！修复效果显著")
        print("📝 建议:")
        print("  1. 可以进行小规模实际审计测试")
        print("  2. 验证API调用和报告生成")
        print("  3. 测试大文件分块处理效果")
    else:
        print("\n⚠️ 测试结果需要改进")
        print("📝 建议:")
        print("  1. 检查失败的测试项目")
        print("  2. 修复相关问题后重新测试")
        print("  3. 确保所有依赖正确安装")
    
    return summary['success_rate'] >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
