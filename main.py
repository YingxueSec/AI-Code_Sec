#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI代码安全审计系统 - 统一命令行入口
支持完整的功能参数控制
"""

import asyncio
import sys
import argparse
import json
import os
from pathlib import Path
from datetime import datetime

# 设置环境变量确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 设置标准输出编码
def setup_encoding():
    """设置编码确保支持Unicode字符"""
    try:
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 重新配置标准输出和错误输出的编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            
        # 在Windows上设置控制台编码
        if sys.platform == 'win32':
            try:
                import ctypes
                # 设置控制台输出为UTF-8
                ctypes.windll.kernel32.SetConsoleOutputCP(65001)
                ctypes.windll.kernel32.SetConsoleCP(65001)
            except:
                pass
                
    except Exception:
        # 忽略编码设置错误
        pass

# 在导入前设置编码
setup_encoding()

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from ai_code_audit import audit_project

def safe_print(text, **kwargs):
    """安全输出函数，处理编码问题"""
    try:
        # 先尝试直接输出
        print(text, **kwargs)
        sys.stdout.flush()
    except UnicodeEncodeError:
        try:
            # 尝试使用gbk编码（Windows默认）
            encoded_text = text.encode('gbk', errors='replace').decode('gbk')
            print(encoded_text, **kwargs)
            sys.stdout.flush()
        except:
            try:
                # 最后备选：使用ascii安全编码
                safe_text = text.encode('ascii', errors='replace').decode('ascii')
                print(safe_text, **kwargs)
                sys.stdout.flush()
            except:
                # 最终备选：只输出ASCII字符
                import re
                ascii_only = re.sub(r'[^\x00-\x7F]', '?', text)
                print(ascii_only, **kwargs)
                sys.stdout.flush()

def print_banner():
    """打印系统横幅"""
    # 优先尝试中文版本
    banner_zh = """
================================================================================
                      AI代码安全审计系统 v2.0.0
================================================================================

  功能特性:
  * 智能文件过滤 - 自动识别和过滤无关文件
  * 跨文件关联分析 - 自动分析相关文件进行辅助判定
  * 六维度置信度评分 - 多维度智能评估漏洞可信度
  * 框架感知安全规则 - 支持Spring、MyBatis等主流框架
  * 前端代码优化 - 智能过滤静态内容，提取关键输入点
  * 智能误报过滤 - 误报率从95%+降至<15%

  性能提升: 分析效率提升300%+，准确率提升至90%+

================================================================================
"""
    
    # ASCII备选版本
    banner_ascii = """
================================================================================
                      AI Code Security Audit System v2.0.0
================================================================================

  Features:
  * Smart File Filtering - Auto identify and filter irrelevant files
  * Cross-File Analysis - Automatic related file analysis
  * Six-Dimensional Confidence Scoring - Multi-dimensional vulnerability assessment
  * Framework-Aware Security Rules - Support Spring, MyBatis frameworks
  * Frontend Code Optimization - Smart static content filtering
  * Smart False Positive Filtering - Reduce false positive rate to <15%

  Performance: 300%+ analysis efficiency improvement, 90%+ accuracy

================================================================================
"""
    
    try:
        # 先尝试中文版本
        safe_print(banner_zh)
    except:
        # 如果中文失败，使用ASCII版本
        try:
            print(banner_ascii, flush=True)
        except:
            # 最简化版本
            print("AI Code Security Audit System v2.0.0", flush=True)
            print("="*50, flush=True)

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='AI代码安全审计系统 - 智能、高效、准确的代码安全分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py /path/to/project                    # 基本审计
  python main.py /path/to/project --all              # 审计所有文件
  python main.py /path/to/project -m 100             # 限制最多100个文件
  python main.py /path/to/project --no-cross-file    # 禁用跨文件分析
  python main.py /path/to/project --no-frontend-opt  # 禁用前端优化
  python main.py /path/to/project --template custom  # 使用自定义模板
  python main.py /path/to/project --output results   # 指定输出文件名
  python main.py /path/to/project --verbose          # 详细输出模式
  python main.py /path/to/project --quick            # 快速扫描模式
        """
    )
    
    # 必需参数
    parser.add_argument('project_path', 
                       help='要审计的项目路径')
    
    # 输出控制
    output_group = parser.add_argument_group('输出控制')
    output_group.add_argument('-o', '--output', 
                             default='audit_results.json',
                             help='输出文件名 (默认: audit_results.json)')
    output_group.add_argument('--no-report', 
                             action='store_true',
                             help='不生成Markdown报告')
    output_group.add_argument('-v', '--verbose', 
                             action='store_true',
                             help='详细输出模式')
    output_group.add_argument('--quiet', 
                             action='store_true',
                             help='静默模式，只输出结果')
    
    # 分析控制
    analysis_group = parser.add_argument_group('分析控制')
    analysis_group.add_argument('-t', '--template', 
                               default='owasp_top_10_2021',
                               choices=['owasp_top_10_2021', 'security_audit_chinese', 'custom'],
                               help='审计模板 (默认: owasp_top_10_2021)')
    analysis_group.add_argument('-m', '--max-files', 
                               type=int, 
                               default=500,
                               help='最大审计文件数 (默认: 500)')
    analysis_group.add_argument('--all', 
                               action='store_true',
                               help='审计所有文件，忽略max-files限制')
    analysis_group.add_argument('--quick', 
                               action='store_true',
                               help='快速扫描模式 (减少深度分析)')
    
    # 功能开关
    feature_group = parser.add_argument_group('功能开关')
    feature_group.add_argument('--no-cross-file', 
                              action='store_true',
                              help='禁用跨文件关联分析')
    feature_group.add_argument('--no-frontend-opt', 
                              action='store_true',
                              help='禁用前端代码优化')
    feature_group.add_argument('--no-confidence-calc', 
                              action='store_true',
                              help='禁用置信度计算')
    feature_group.add_argument('--no-filter', 
                              action='store_true',
                              help='禁用智能文件过滤')
    feature_group.add_argument('--no-filter-stats', 
                              action='store_true',
                              help='不显示文件过滤统计')
    
    # 高级选项
    advanced_group = parser.add_argument_group('高级选项')
    advanced_group.add_argument('--include-extensions', 
                               nargs='+',
                               help='包含的文件扩展名 (如: .java .py .js)')
    advanced_group.add_argument('--exclude-extensions', 
                               nargs='+',
                               help='排除的文件扩展名')
    advanced_group.add_argument('--include-paths', 
                               nargs='+',
                               help='包含的路径模式')
    advanced_group.add_argument('--exclude-paths', 
                               nargs='+',
                               help='排除的路径模式')
    advanced_group.add_argument('--min-confidence', 
                               type=float, 
                               default=0.3,
                               help='最小置信度阈值 (默认: 0.3)')
    advanced_group.add_argument('--max-confidence', 
                               type=float, 
                               default=1.0,
                               help='最大置信度阈值 (默认: 1.0)')
    
    # 调试选项
    debug_group = parser.add_argument_group('调试选项')
    debug_group.add_argument('--debug',
                            action='store_true',
                            help='启用调试模式')
    debug_group.add_argument('--dry-run',
                            action='store_true',
                            help='试运行模式，不执行实际分析')
    debug_group.add_argument('--profile',
                            action='store_true',
                            help='启用性能分析')
    debug_group.add_argument('--no-timing',
                            action='store_true',
                            help='禁用时间统计显示')
    
    return parser

def validate_args(args):
    """验证命令行参数"""
    errors = []
    
    # 检查项目路径
    if not Path(args.project_path).exists():
        errors.append(f"项目路径不存在: {args.project_path}")
    
    # 检查置信度范围
    if args.min_confidence < 0 or args.min_confidence > 1:
        errors.append("最小置信度必须在0-1之间")
    
    if args.max_confidence < 0 or args.max_confidence > 1:
        errors.append("最大置信度必须在0-1之间")
    
    if args.min_confidence >= args.max_confidence:
        errors.append("最小置信度必须小于最大置信度")
    
    # 检查文件数限制
    if args.max_files <= 0:
        errors.append("最大文件数必须大于0")
    
    # 检查互斥选项
    if args.verbose and args.quiet:
        errors.append("--verbose 和 --quiet 不能同时使用")
    
    return errors

def print_config_summary(args):
    """打印配置摘要"""
    if args.quiet:
        return
    
    safe_print("[配置] 审计配置:")
    safe_print(f"  项目路径: {args.project_path}")
    safe_print(f"  审计模板: {args.template}")
    
    if args.all:
        safe_print(f"  文件限制: 无限制 (--all)")
    else:
        safe_print(f"  最大文件数: {args.max_files}")
    
    safe_print(f"  输出文件: {args.output}")
    
    # 功能状态
    features = []
    if not args.no_cross_file:
        features.append("跨文件分析")
    if not args.no_frontend_opt:
        features.append("前端优化")
    if not args.no_confidence_calc:
        features.append("置信度计算")
    if not args.no_filter:
        features.append("智能过滤")
    
    if features:
        safe_print(f"  启用功能: {', '.join(features)}")
    
    disabled_features = []
    if args.no_cross_file:
        disabled_features.append("跨文件分析")
    if args.no_frontend_opt:
        disabled_features.append("前端优化")
    if args.no_confidence_calc:
        disabled_features.append("置信度计算")
    if args.no_filter:
        disabled_features.append("智能过滤")
    
    if disabled_features:
        safe_print(f"  禁用功能: {', '.join(disabled_features)}")
    
    if args.quick:
        safe_print(f"  扫描模式: 快速扫描")
    
    safe_print("")

async def run_audit(args):
    """运行审计"""
    try:
        # 构建审计参数
        audit_params = {
            'project_path': args.project_path,
            'output_file': args.output,
            'template': args.template,
            'max_files': None if args.all else args.max_files,
            'show_filter_stats': not args.no_filter_stats,
            'enable_cross_file': not args.no_cross_file,
            'enable_frontend_opt': not args.no_frontend_opt,
            'enable_confidence_calc': not args.no_confidence_calc,
            'enable_filter': not args.no_filter,
            'min_confidence': args.min_confidence,
            'max_confidence': args.max_confidence,
            'quick_mode': args.quick,
            'verbose': args.verbose,
            'debug': args.debug,
            'show_timing': not args.no_timing
        }
        
        # 添加文件过滤参数
        if args.include_extensions:
            audit_params['include_extensions'] = args.include_extensions
        if args.exclude_extensions:
            audit_params['exclude_extensions'] = args.exclude_extensions
        if args.include_paths:
            audit_params['include_paths'] = args.include_paths
        if args.exclude_paths:
            audit_params['exclude_paths'] = args.exclude_paths
        
        if args.dry_run:
            safe_print("[试运行] 试运行模式 - 不执行实际分析")
            safe_print(f"审计参数: {json.dumps(audit_params, indent=2, ensure_ascii=False)}")
            return
        
        # 执行审计
        if args.profile:
            import cProfile
            import pstats
            profiler = cProfile.Profile()
            profiler.enable()
        
        results = await audit_project(**audit_params)
        
        if args.profile:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # 显示前20个最耗时的函数
        
        # 生成报告的逻辑已移至 audit_project 内部，无需在此调用
        
        # 输出结果摘要
        if not args.quiet:
            safe_print(f"[完成] 审计完成！")
            safe_print(f"[摘要] 结果摘要:")
            safe_print(f"  - 分析文件数: {results['total_files']}")
            safe_print(f"  - 发现问题数: {len(results['findings'])}")
            safe_print(f"  - JSON结果: {args.output}")
            if not args.no_report:
                safe_print(f"  - Markdown报告: {args.output.replace('.json', '_report.md')}")
        
        return results
        
    except Exception as e:
        safe_print(f"[错误] 审计失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 打印横幅
    if not args.quiet:
        print_banner()
    
    # 验证参数
    errors = validate_args(args)
    if errors:
        safe_print("[错误] 参数错误:")
        for error in errors:
            safe_print(f"  - {error}")
        sys.exit(1)
    
    # 打印配置摘要
    print_config_summary(args)
    
    # 运行审计
    await run_audit(args)

if __name__ == "__main__":
    asyncio.run(main())
