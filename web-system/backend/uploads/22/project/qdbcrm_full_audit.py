#!/usr/bin/env python3
"""
qdbcrm-v3.0.2 完整代码审计脚本
基于我们验证过的修复逻辑，提供完整的安全审计功能
"""
import os
import sys
import time
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """文件信息"""
    path: str
    full_path: str
    size: int
    size_mb: float
    language: str = "php"

@dataclass
class SecurityIssue:
    """安全问题"""
    type: str
    severity: str
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None

@dataclass
class AuditResult:
    """审计结果"""
    file_path: str
    language: str
    issues: List[SecurityIssue]
    summary: str
    lines_analyzed: int
    analysis_time: float

class SmartFileFilter:
    """智能文件过滤器 - 基于我们验证的修复逻辑"""

    def __init__(self):
        # 基于测试验证的过滤规则
        self.ignore_patterns = [
            '*.js', '*.css', '*.min.js', '*.min.css',
            '*.jpg', '*.png', '*.gif', '*.ico', '*.svg',
            '*.woff', '*.ttf', '*.eot',
            '*.json', '*.xml', '*.txt', '*.md', '*.log',
            '*.zip', '*.tar', '*.gz'
        ]

        self.ignore_dirs = [
            'install', 'theme', 'vendor', 'node_modules',
            '.git', '.idea', '.vscode', 'cache', 'logs'
        ]

        self.max_file_size = 10 * 1024 * 1024  # 10MB

    def should_filter_file(self, file_path: str, project_root: str) -> tuple[bool, str]:
        """判断文件是否应该被过滤"""
        rel_path = os.path.relpath(file_path, project_root)

        # 扩展名过滤
        for pattern in self.ignore_patterns:
            if file_path.endswith(pattern.replace('*', '')):
                return True, f'扩展名过滤: {pattern}'

        # 目录过滤
        for ignore_dir in self.ignore_dirs:
            if ignore_dir in rel_path:
                return True, f'目录过滤: {ignore_dir}'

        # 文件大小过滤
        try:
            if os.path.getsize(file_path) > self.max_file_size:
                return True, f'文件过大: >{self.max_file_size/1024/1024:.1f}MB'
        except:
            pass

        # 只保留PHP文件
        if not file_path.endswith('.php'):
            return True, '非PHP文件'

        return False, '需要审计'

class LargeFileHandler:
    """大文件处理器 - 基于我们验证的分块逻辑"""

    def __init__(self, chunk_size: int = 50000):
        self.chunk_size = chunk_size

    def should_chunk_file(self, file_size: int) -> bool:
        """判断是否需要分块"""
        return file_size > 3 * 1024 * 1024  # 3MB

    def chunk_file_content(self, content: str) -> List[str]:
        """将文件内容分块"""
        if len(content) <= self.chunk_size:
            return [content]

        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

class SecurityAnalyzer:
    """安全分析器 - 基于我们验证的检测逻辑"""

    def __init__(self):
        self.security_patterns = {
            'SQL注入风险': {
                'patterns': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'mysql_query', 'mysqli_query'],
                'severity': 'High'
            },
            'XSS风险': {
                'patterns': ['echo', 'print', '$_GET', '$_POST', '$_REQUEST'],
                'severity': 'High'
            },
            '文件操作风险': {
                'patterns': ['include', 'require', 'file_get_contents', 'fopen'],
                'severity': 'Medium'
            },
            '代码执行风险': {
                'patterns': ['eval', 'exec', 'system', 'shell_exec'],
                'severity': 'Critical'
            },
            '认证绕过风险': {
                'patterns': ['password', 'login', 'auth', 'session'],
                'severity': 'High'
            },
            '文件上传风险': {
                'patterns': ['upload', 'move_uploaded_file', '$_FILES'],
                'severity': 'High'
            },
            '信息泄露风险': {
                'patterns': ['phpinfo', 'var_dump', 'print_r'],
                'severity': 'Medium'
            },
            '权限控制风险': {
                'patterns': ['admin', 'role', 'permission', 'access'],
                'severity': 'Medium'
            }
        }

    def analyze_content(self, content: str, file_path: str) -> List[SecurityIssue]:
        """分析文件内容"""
        issues = []
        lines = content.split('\n')

        for category, config in self.security_patterns.items():
            patterns = config['patterns']
            severity = config['severity']

            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                for pattern in patterns:
                    if pattern.lower() in line_lower:
                        issue = SecurityIssue(
                            type=category,
                            severity=severity,
                            description=f'发现 {pattern} 模式',
                            line_number=i,
                            code_snippet=line.strip()[:100]
                        )
                        issues.append(issue)

        return issues

class QdbcrmAuditor:
    """qdbcrm完整审计器"""

    def __init__(self):
        self.file_filter = SmartFileFilter()
        self.large_file_handler = LargeFileHandler()
        self.security_analyzer = SecurityAnalyzer()
        self.results = []
        self.stats = {
            'total_files_scanned': 0,
            'files_filtered': 0,
            'files_analyzed': 0,
            'large_files_chunked': 0,
            'total_issues_found': 0,
            'analysis_time': 0
        }

    def scan_project(self, project_path: str) -> List[FileInfo]:
        """扫描项目文件"""
        logger.info(f"开始扫描项目: {project_path}")

        if not os.path.exists(project_path):
            raise ValueError(f"项目路径不存在: {project_path}")

        files_to_analyze = []
        filter_stats = {}

        start_time = time.time()

        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.stats['total_files_scanned'] += 1

                should_filter, reason = self.file_filter.should_filter_file(file_path, project_path)

                if should_filter:
                    self.stats['files_filtered'] += 1
                    filter_stats[reason] = filter_stats.get(reason, 0) + 1
                else:
                    try:
                        size = os.path.getsize(file_path)
                        file_info = FileInfo(
                            path=os.path.relpath(file_path, project_path),
                            full_path=file_path,
                            size=size,
                            size_mb=size / 1024 / 1024
                        )
                        files_to_analyze.append(file_info)
                    except Exception as e:
                        logger.warning(f"无法获取文件信息: {file_path} - {e}")

        scan_time = time.time() - start_time

        logger.info(f"扫描完成: {scan_time:.2f}秒")
        logger.info(f"总文件数: {self.stats['total_files_scanned']}")
        logger.info(f"过滤文件数: {self.stats['files_filtered']}")
        logger.info(f"待分析文件数: {len(files_to_analyze)}")

        logger.info("过滤统计:")
        for reason, count in sorted(filter_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {reason}: {count}个")

        return files_to_analyze

    def analyze_file(self, file_info: FileInfo) -> AuditResult:
        """分析单个文件"""
        start_time = time.time()

        try:
            with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 检查是否需要分块
            if self.large_file_handler.should_chunk_file(file_info.size):
                logger.info(f"大文件分块处理: {file_info.path} ({file_info.size_mb:.1f}MB)")
                chunks = self.large_file_handler.chunk_file_content(content)
                self.stats['large_files_chunked'] += 1

                all_issues = []
                for i, chunk in enumerate(chunks):
                    chunk_issues = self.security_analyzer.analyze_content(chunk, file_info.path)
                    all_issues.extend(chunk_issues)
                    logger.debug(f"  块 {i+1}/{len(chunks)}: {len(chunk_issues)} 个问题")
            else:
                all_issues = self.security_analyzer.analyze_content(content, file_info.path)

            analysis_time = time.time() - start_time
            lines_count = len(content.split('\n'))

            # 生成摘要
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue.type] = issue_counts.get(issue.type, 0) + 1

            summary_parts = []
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                summary_parts.append(f"{issue_type}: {count}")

            summary = f"发现 {len(all_issues)} 个安全问题。" + (
                " 主要问题: " + ", ".join(summary_parts[:3]) if summary_parts else ""
            )

            result = AuditResult(
                file_path=file_info.path,
                language=file_info.language,
                issues=all_issues,
                summary=summary,
                lines_analyzed=lines_count,
                analysis_time=analysis_time
            )

            self.stats['total_issues_found'] += len(all_issues)
            self.stats['analysis_time'] += analysis_time

            return result

        except Exception as e:
            logger.error(f"分析文件失败: {file_info.path} - {e}")
            return AuditResult(
                file_path=file_info.path,
                language=file_info.language,
                issues=[],
                summary=f"分析失败: {str(e)}",
                lines_analyzed=0,
                analysis_time=time.time() - start_time
            )

    def run_audit(self, project_path: str, max_files: int = 0) -> Dict[str, Any]:
        """运行完整审计"""
        logger.info("🚀 开始qdbcrm-v3.0.2完整代码审计")
        logger.info("=" * 60)

        audit_start_time = time.time()

        # 1. 扫描项目
        files_to_analyze = self.scan_project(project_path)

        # 2. 限制文件数量（如果指定）
        if max_files > 0:
            files_to_analyze = files_to_analyze[:max_files]
            logger.info(f"限制分析文件数: {max_files}")

        # 3. 分析文件
        logger.info(f"\n🔍 开始安全分析 ({len(files_to_analyze)} 个文件)")
        logger.info("-" * 40)

        for i, file_info in enumerate(files_to_analyze, 1):
            logger.info(f"[{i}/{len(files_to_analyze)}] 分析: {file_info.path} ({file_info.size_mb:.2f}MB)")

            result = self.analyze_file(file_info)
            self.results.append(result)
            self.stats['files_analyzed'] += 1

            if result.issues:
                logger.info(f"  ✅ 完成 - 发现 {len(result.issues)} 个问题")
            else:
                logger.info(f"  ✅ 完成 - 未发现问题")

        total_audit_time = time.time() - audit_start_time

        # 4. 生成最终报告
        report = self.generate_report(project_path, total_audit_time)

        logger.info("\n🎯 审计完成!")
        logger.info("=" * 60)
        logger.info(f"总耗时: {total_audit_time:.2f}秒")
        logger.info(f"分析文件: {self.stats['files_analyzed']}")
        logger.info(f"发现问题: {self.stats['total_issues_found']}")
        logger.info(f"大文件分块: {self.stats['large_files_chunked']}")

        return report

    def generate_report(self, project_path: str, total_time: float) -> Dict[str, Any]:
        """生成审计报告"""
        # 统计问题类型
        issue_stats = {}
        severity_stats = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}

        for result in self.results:
            for issue in result.issues:
                issue_stats[issue.type] = issue_stats.get(issue.type, 0) + 1
                severity_stats[issue.severity] = severity_stats.get(issue.severity, 0) + 1

        # 找出高风险文件
        high_risk_files = []
        for result in self.results:
            critical_issues = [i for i in result.issues if i.severity == 'Critical']
            high_issues = [i for i in result.issues if i.severity == 'High']

            if critical_issues or len(high_issues) > 5:
                high_risk_files.append({
                    'file': result.file_path,
                    'critical_issues': len(critical_issues),
                    'high_issues': len(high_issues),
                    'total_issues': len(result.issues)
                })

        # 生成报告
        report = {
            'project_info': {
                'project_path': project_path,
                'audit_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_audit_time': total_time,
                'auditor_version': 'qdbcrm-auditor-v1.0'
            },
            'scan_statistics': {
                'total_files_scanned': self.stats['total_files_scanned'],
                'files_filtered': self.stats['files_filtered'],
                'files_analyzed': self.stats['files_analyzed'],
                'large_files_chunked': self.stats['large_files_chunked'],
                'filter_efficiency': (self.stats['files_filtered'] / self.stats['total_files_scanned']) * 100
            },
            'security_summary': {
                'total_issues': self.stats['total_issues_found'],
                'severity_distribution': severity_stats,
                'issue_categories': issue_stats,
                'high_risk_files_count': len(high_risk_files)
            },
            'high_risk_files': high_risk_files[:10],  # 只显示前10个
            'detailed_results': [
                {
                    'file_path': result.file_path,
                    'language': result.language,
                    'summary': result.summary,
                    'lines_analyzed': result.lines_analyzed,
                    'analysis_time': result.analysis_time,
                    'issues_count': len(result.issues),
                    'issues': [
                        {
                            'type': issue.type,
                            'severity': issue.severity,
                            'description': issue.description,
                            'line_number': issue.line_number,
                            'code_snippet': issue.code_snippet
                        } for issue in result.issues[:5]  # 只显示前5个问题
                    ]
                } for result in self.results
            ]
        }

        return report

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='qdbcrm-v3.0.2 完整代码审计')
    parser.add_argument('project_path', help='项目路径')
    parser.add_argument('--max-files', type=int, default=0, help='最大分析文件数 (0=无限制)')
    parser.add_argument('--output-file', help='输出文件路径')
    parser.add_argument('--show-filter-stats', action='store_true', help='显示过滤统计')

    args = parser.parse_args()

    try:
        auditor = QdbcrmAuditor()
        report = auditor.run_audit(args.project_path, args.max_files)

        # 保存报告
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 报告已保存: {args.output_file}")

        # 显示摘要
        print("\n" + "="*60)
        print("🎯 审计摘要")
        print("="*60)
        print(f"项目路径: {report['project_info']['project_path']}")
        print(f"审计时间: {report['project_info']['audit_time']}")
        print(f"总耗时: {report['project_info']['total_audit_time']:.2f}秒")
        print(f"扫描文件: {report['scan_statistics']['total_files_scanned']}")
        print(f"过滤文件: {report['scan_statistics']['files_filtered']}")
        print(f"分析文件: {report['scan_statistics']['files_analyzed']}")
        print(f"过滤效率: {report['scan_statistics']['filter_efficiency']:.1f}%")
        print(f"发现问题: {report['security_summary']['total_issues']}")
        print(f"高风险文件: {report['security_summary']['high_risk_files_count']}")

        print(f"\n🔍 问题分布:")
        for severity, count in report['security_summary']['severity_distribution'].items():
            if count > 0:
                print(f"  {severity}: {count}")

        print(f"\n📊 问题类型 (前5):")
        sorted_issues = sorted(report['security_summary']['issue_categories'].items(),
                             key=lambda x: x[1], reverse=True)
        for issue_type, count in sorted_issues[:5]:
            print(f"  {issue_type}: {count}")

        if report['high_risk_files']:
            print(f"\n⚠️  高风险文件 (前5):")
            for file_info in report['high_risk_files'][:5]:
                print(f"  {file_info['file']}: {file_info['total_issues']} 问题")

        return 0

    except Exception as e:
        logger.error(f"审计失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())