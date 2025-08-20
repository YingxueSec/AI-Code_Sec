#!/usr/bin/env python3
"""
测试修复效果的脚本
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_file_filtering():
    """测试文件过滤修复"""
    print("🔍 测试文件过滤修复")
    print("=" * 50)
    
    try:
        from ai_code_audit.analysis.file_scanner import FileScanner
        from ai_code_audit.core.config import ConfigManager
        
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # 创建带配置的FileScanner
        scanner = FileScanner(config=config.dict() if hasattr(config, 'dict') else config)
        
        test_path = "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2"
        
        if os.path.exists(test_path):
            print(f"📁 扫描路径: {test_path}")
            files = scanner.scan_directory(test_path)
            
            # 统计文件类型
            file_types = {}
            for file_info in files:
                ext = os.path.splitext(file_info.path)[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            print(f"\n📊 扫描结果:")
            print(f"  总文件数: {len(files)}")
            print(f"  文件类型分布:")
            for ext, count in sorted(file_types.items()):
                print(f"    {ext or '无扩展名'}: {count}")
            
            # 检查是否有JS/CSS文件被包含
            js_css_files = [f for f in files if f.path.endswith(('.js', '.css'))]
            if js_css_files:
                print(f"\n❌ 发现 {len(js_css_files)} 个JS/CSS文件未被过滤:")
                for f in js_css_files[:5]:  # 只显示前5个
                    print(f"    {f.path}")
                if len(js_css_files) > 5:
                    print(f"    ... 还有 {len(js_css_files) - 5} 个")
                return False
            else:
                print("\n✅ 文件过滤正常工作 - 没有JS/CSS文件被包含")
                return True
        else:
            print(f"❌ 测试路径不存在: {test_path}")
            return False
            
    except Exception as e:
        print(f"❌ 文件过滤测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_large_file_handling():
    """测试大文件处理"""
    print("\n📁 测试大文件处理")
    print("=" * 50)
    
    try:
        from ai_code_audit.analysis.large_file_handler import LargeFileHandler
        
        handler = LargeFileHandler(max_chunk_size=50000)
        
        # 检查大文件是否存在
        large_files = [
            "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2/app/controllers/login.php",
            "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2/app/controllers/user.php",
            "/Users/admin/AnyProjects/AttackSec/A-AI/qdbcrm-v3.0.2/app/models/qmsoft.php"
        ]
        
        processed_files = 0
        for file_path in large_files:
            path_obj = Path(file_path)
            if path_obj.exists():
                size = path_obj.stat().st_size
                print(f"📄 {path_obj.name}: {size/1024/1024:.1f}MB")
                
                if handler.should_chunk_file(path_obj, 3145728):  # 3MB
                    print(f"  ⚡ 需要分块处理")
                    chunks = handler.chunk_php_file(path_obj)
                    if chunks:
                        print(f"  ✅ 成功分块为 {len(chunks)} 个块")
                        
                        # 显示重要块
                        important_chunks = handler.get_important_chunks(chunks, max_chunks=3)
                        print(f"  🎯 识别出 {len(important_chunks)} 个重要块:")
                        for i, chunk in enumerate(important_chunks):
                            print(f"    {i+1}. {chunk.chunk_type} (lines {chunk.start_line}-{chunk.end_line}, {chunk.size} chars)")
                        
                        processed_files += 1
                    else:
                        print(f"  ❌ 分块失败")
                else:
                    print(f"  ✅ 文件大小正常，无需分块")
        
        if processed_files > 0:
            print(f"\n✅ 成功处理 {processed_files} 个大文件")
            return True
        else:
            print("\n⚠️  未发现需要处理的大文件")
            return False
            
    except Exception as e:
        print(f"❌ 大文件处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_markup_safety():
    """测试markup安全性"""
    print("\n🛡️  测试Markup安全性")
    print("=" * 50)
    
    try:
        from ai_code_audit.audit.report_generator import sanitize_markup_content, safe_console_print
        from rich.console import Console
        
        console = Console()
        
        # 测试问题文本
        problematic_texts = [
            '[/^1\\d{10}$/,"请输入正确的手机号"]',
            '[red]Error[/red]',
            'Normal text with [brackets]',
            'Regex pattern: /^\\d+$/',
            'Array: ["item1", "item2"]'
        ]
        
        print("🧪 测试问题文本处理:")
        all_safe = True
        
        for text in problematic_texts:
            try:
                cleaned = sanitize_markup_content(text)
                print(f"  原文: {text}")
                print(f"  清理: {cleaned}")
                
                # 尝试安全打印
                safe_console_print(console, f"测试: {text}")
                print("  ✅ 安全打印成功")
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                all_safe = False
            
            print()
        
        if all_safe:
            print("✅ Markup安全性测试通过")
            return True
        else:
            print("❌ Markup安全性测试失败")
            return False
            
    except Exception as e:
        print(f"❌ Markup安全性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_integration():
    """测试配置集成"""
    print("\n⚙️  测试配置集成")
    print("=" * 50)
    
    try:
        from ai_code_audit.analysis.project_analyzer import ProjectAnalyzer
        from ai_code_audit.core.config import ConfigManager
        
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # 创建带配置的ProjectAnalyzer
        analyzer = ProjectAnalyzer(config=config.dict() if hasattr(config, 'dict') else config)
        
        print("✅ ProjectAnalyzer配置集成成功")
        print(f"  文件扫描器已配置: {hasattr(analyzer.file_scanner, 'ignore_patterns')}")
        print(f"  过滤规则数量: {len(analyzer.file_scanner.ignore_patterns)}")
        print(f"  最大文件大小: {analyzer.file_scanner.max_file_size/1024/1024:.1f}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🧪 修复效果测试")
    print("=" * 60)
    
    results = {}
    
    # 测试各项修复
    results['file_filtering'] = test_file_filtering()
    results['large_file_handling'] = test_large_file_handling()
    results['markup_safety'] = test_markup_safety()
    results['config_integration'] = test_config_integration()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有修复都正常工作！")
        print("\n📝 建议下一步:")
        print("  1. 运行完整的qdbcrm审计测试")
        print("  2. 验证大文件分块审计效果")
        print("  3. 检查审计报告生成稳定性")
    else:
        print("⚠️  仍有问题需要解决")
        
        # 给出具体建议
        if not results['file_filtering']:
            print("  - 需要进一步调试文件过滤逻辑")
        if not results['large_file_handling']:
            print("  - 需要检查大文件处理实现")
        if not results['markup_safety']:
            print("  - 需要完善markup安全处理")
        if not results['config_integration']:
            print("  - 需要修复配置传递问题")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
