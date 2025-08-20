"""
Report generator for creating audit reports in multiple formats.

This module provides report generation capabilities including:
- Multi-format report generation (JSON, HTML, PDF, Markdown)
- Template-based report system
- Charts and visualizations
- Export and sharing functionality
"""

import json
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .aggregator import AuditResult, VulnerabilitySeverity, VulnerabilityCategory

logger = logging.getLogger(__name__)


def sanitize_markup_content(text: str) -> str:
    """
    清理可能导致Rich markup错误的内容

    Args:
        text: 原始文本

    Returns:
        清理后的安全文本
    """
    if not isinstance(text, str):
        return str(text)

    # 转义Rich markup特殊字符
    text = text.replace('[', '\\[').replace(']', '\\]')

    # 移除可能导致问题的正则表达式模式
    # 例如: [/^1\d{10}$/,"请输入正确的手机号"]
    text = re.sub(r'\[/[^\]]*\]', '', text)

    # 清理其他可能的markup模式
    text = re.sub(r'\[[^\]]*\]', lambda m: m.group(0).replace('[', '\\[').replace(']', '\\]'), text)

    return text


def safe_console_print(console, message: str, style: str = None):
    """
    安全的控制台打印函数

    Args:
        console: Rich Console对象
        message: 要打印的消息
        style: 样式（可选）
    """
    try:
        cleaned_message = sanitize_markup_content(message)
        if style:
            console.print(cleaned_message, style=style)
        else:
            console.print(cleaned_message)
    except Exception as e:
        # 降级到纯文本输出
        logger.warning(f"Rich markup error, falling back to plain text: {e}")
        print(f"{style}: {message}" if style else message)


class ReportFormat(Enum):
    """Report format enumeration."""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    CSV = "csv"


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    include_code_snippets: bool = True
    include_statistics: bool = True
    include_recommendations: bool = True
    max_snippet_length: int = 500
    severity_threshold: VulnerabilitySeverity = VulnerabilitySeverity.INFO
    group_by_file: bool = False
    group_by_category: bool = True
    include_metadata: bool = True


@dataclass
class AuditReport:
    """Generated audit report."""
    format: ReportFormat
    content: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()


class ReportGenerator:
    """Generator for creating audit reports in multiple formats."""
    
    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialize report generator."""
        self.config = config or ReportConfig()
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
    
    async def generate_report(
        self,
        audit_result: AuditResult,
        format: ReportFormat,
        output_path: Optional[str] = None
    ) -> AuditReport:
        """Generate audit report in specified format."""
        logger.info(f"Generating {format.value} report for session {audit_result.session_id}")
        
        # Filter findings by severity threshold
        filtered_vulns = [
            v for v in audit_result.vulnerabilities
            if self._severity_meets_threshold(v.severity)
        ]
        
        # Generate content based on format
        if format == ReportFormat.JSON:
            content = await self._generate_json_report(audit_result, filtered_vulns)
        elif format == ReportFormat.HTML:
            content = await self._generate_html_report(audit_result, filtered_vulns)
        elif format == ReportFormat.MARKDOWN:
            content = await self._generate_markdown_report(audit_result, filtered_vulns)
        elif format == ReportFormat.CSV:
            content = await self._generate_csv_report(audit_result, filtered_vulns)
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        # Save to file if output path provided
        if output_path:
            await self._save_report(content, output_path)
        
        return AuditReport(
            format=format,
            content=content,
            file_path=output_path,
            metadata={
                'session_id': audit_result.session_id,
                'total_findings': len(filtered_vulns),
                'generation_time': datetime.now().isoformat(),
            }
        )
    
    async def _generate_json_report(
        self,
        audit_result: AuditResult,
        vulnerabilities: List
    ) -> str:
        """Generate JSON format report."""
        report_data = {
            'audit_summary': {
                'session_id': audit_result.session_id,
                'project_name': audit_result.project_name,
                'project_path': audit_result.project_path,
                'generated_at': datetime.now().isoformat(),
                'total_findings': len(vulnerabilities),
                'risk_score': audit_result.risk_score,
            },
            'statistics': audit_result.statistics if self.config.include_statistics else {},
            'vulnerabilities': [
                {
                    'id': v.id,
                    'title': v.title,
                    'description': v.description if self.config.include_recommendations else v.title,
                    'severity': v.severity.value,
                    'category': v.category.value,
                    'file_path': v.file_path,
                    'line_number': v.line_number,
                    'code_snippet': self._truncate_snippet(v.code_snippet) if self.config.include_code_snippets and v.code_snippet else None,
                    'recommendation': v.recommendation if self.config.include_recommendations else None,
                    'cwe_id': v.cwe_id,
                    'confidence': v.confidence,
                }
                for v in vulnerabilities
            ],
            'quality_issues': [
                {
                    'id': q.id,
                    'title': q.title,
                    'description': q.description,
                    'severity': q.severity.value,
                    'file_path': q.file_path,
                    'line_number': q.line_number,
                    'suggestion': q.suggestion,
                }
                for q in audit_result.quality_issues
            ] if self.config.include_recommendations else [],
            'metadata': audit_result.metadata if self.config.include_metadata else {},
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    async def _generate_html_report(
        self,
        audit_result: AuditResult,
        vulnerabilities: List
    ) -> str:
        """Generate HTML format report."""
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Audit Report - {project_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
        .stat-box {{ background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
        .vulnerability {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .critical {{ border-left: 5px solid #dc3545; }}
        .high {{ border-left: 5px solid #fd7e14; }}
        .medium {{ border-left: 5px solid #ffc107; }}
        .low {{ border-left: 5px solid #28a745; }}
        .info {{ border-left: 5px solid #17a2b8; }}
        .code-snippet {{ background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }}
        .severity {{ font-weight: bold; text-transform: uppercase; }}
        .category {{ background: #6c757d; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Audit Report</h1>
        <p><strong>Project:</strong> {project_name}</p>
        <p><strong>Path:</strong> {project_path}</p>
        <p><strong>Generated:</strong> {generated_at}</p>
        <p><strong>Risk Score:</strong> {risk_score:.1f}/10</p>
    </div>
    
    <div class="summary">
        <div class="stat-box">
            <h3>{total_findings}</h3>
            <p>Total Findings</p>
        </div>
        <div class="stat-box">
            <h3>{critical_count}</h3>
            <p>Critical</p>
        </div>
        <div class="stat-box">
            <h3>{high_count}</h3>
            <p>High</p>
        </div>
        <div class="stat-box">
            <h3>{medium_count}</h3>
            <p>Medium</p>
        </div>
    </div>
    
    <h2>Vulnerabilities</h2>
    {vulnerabilities_html}
    
    {quality_issues_html}
</body>
</html>
        """
        
        # Generate vulnerability HTML
        vulnerabilities_html = ""
        for vuln in vulnerabilities:
            code_snippet_html = ""
            if self.config.include_code_snippets and vuln.code_snippet:
                code_snippet_html = f'<div class="code-snippet">{self._escape_html(self._truncate_snippet(vuln.code_snippet))}</div>'
            
            vulnerabilities_html += f"""
            <div class="vulnerability {vuln.severity.value}">
                <h3>{self._escape_html(vuln.title)} <span class="category">{vuln.category.value}</span></h3>
                <p><strong>File:</strong> {vuln.file_path} {f'(Line {vuln.line_number})' if vuln.line_number else ''}</p>
                <p><strong>Severity:</strong> <span class="severity {vuln.severity.value}">{vuln.severity.value}</span></p>
                <p>{self._escape_html(vuln.description)}</p>
                {code_snippet_html}
                {f'<p><strong>Recommendation:</strong> {self._escape_html(vuln.recommendation)}</p>' if vuln.recommendation else ''}
            </div>
            """
        
        # Generate quality issues HTML
        quality_issues_html = ""
        if audit_result.quality_issues and self.config.include_recommendations:
            quality_issues_html = "<h2>Code Quality Issues</h2>"
            for issue in audit_result.quality_issues:
                quality_issues_html += f"""
                <div class="vulnerability {issue.severity.value}">
                    <h3>{self._escape_html(issue.title)}</h3>
                    <p><strong>File:</strong> {issue.file_path} {f'(Line {issue.line_number})' if issue.line_number else ''}</p>
                    <p>{self._escape_html(issue.description)}</p>
                    {f'<p><strong>Suggestion:</strong> {self._escape_html(issue.suggestion)}</p>' if issue.suggestion else ''}
                </div>
                """
        
        # Count by severity
        severity_counts = {}
        for severity in VulnerabilitySeverity:
            severity_counts[severity.value] = len([v for v in vulnerabilities if v.severity == severity])
        
        return html_template.format(
            project_name=self._escape_html(audit_result.project_name),
            project_path=self._escape_html(audit_result.project_path),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_score=audit_result.risk_score,
            total_findings=len(vulnerabilities),
            critical_count=severity_counts.get('critical', 0),
            high_count=severity_counts.get('high', 0),
            medium_count=severity_counts.get('medium', 0),
            vulnerabilities_html=vulnerabilities_html,
            quality_issues_html=quality_issues_html,
        )
    
    async def _generate_markdown_report(
        self,
        audit_result: AuditResult,
        vulnerabilities: List
    ) -> str:
        """Generate Markdown format report."""
        md_content = f"""# Security Audit Report

## Project Information
- **Project Name:** {audit_result.project_name}
- **Project Path:** {audit_result.project_path}
- **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Risk Score:** {audit_result.risk_score:.1f}/10

## Summary
- **Total Findings:** {len(vulnerabilities)}
- **Critical:** {len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL])}
- **High:** {len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH])}
- **Medium:** {len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM])}
- **Low:** {len([v for v in vulnerabilities if v.severity == VulnerabilitySeverity.LOW])}

## Vulnerabilities

"""
        
        # Group by category if configured
        if self.config.group_by_category:
            categories = {}
            for vuln in vulnerabilities:
                if vuln.category not in categories:
                    categories[vuln.category] = []
                categories[vuln.category].append(vuln)
            
            for category, vulns in categories.items():
                if vulns:
                    md_content += f"### {category.value.replace('_', ' ').title()}\n\n"
                    for vuln in vulns:
                        md_content += self._format_vulnerability_markdown(vuln)
        else:
            for vuln in vulnerabilities:
                md_content += self._format_vulnerability_markdown(vuln)
        
        # Add quality issues if configured
        if audit_result.quality_issues and self.config.include_recommendations:
            md_content += "\n## Code Quality Issues\n\n"
            for issue in audit_result.quality_issues:
                md_content += f"""#### {issue.title}
- **File:** {issue.file_path}{f' (Line {issue.line_number})' if issue.line_number else ''}
- **Severity:** {issue.severity.value.upper()}

{issue.description}

{f'**Suggestion:** {issue.suggestion}' if issue.suggestion else ''}

---

"""
        
        return md_content
    
    async def _generate_csv_report(
        self,
        audit_result: AuditResult,
        vulnerabilities: List
    ) -> str:
        """Generate CSV format report."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Title', 'Severity', 'Category', 'File Path', 'Line Number',
            'Description', 'CWE ID', 'Confidence'
        ])
        
        # Write vulnerability data
        for vuln in vulnerabilities:
            writer.writerow([
                vuln.id,
                vuln.title,
                vuln.severity.value,
                vuln.category.value,
                vuln.file_path,
                vuln.line_number or '',
                vuln.description.replace('\n', ' '),
                vuln.cwe_id or '',
                vuln.confidence
            ])
        
        return output.getvalue()
    
    def _format_vulnerability_markdown(self, vuln) -> str:
        """Format single vulnerability for markdown."""
        md = f"""#### {vuln.title}
- **File:** {vuln.file_path}{f' (Line {vuln.line_number})' if vuln.line_number else ''}
- **Severity:** {vuln.severity.value.upper()}
- **Category:** {vuln.category.value.replace('_', ' ').title()}
- **Confidence:** {vuln.confidence:.1f}
{f'- **CWE:** {vuln.cwe_id}' if vuln.cwe_id else ''}

{vuln.description}

"""
        
        if self.config.include_code_snippets and vuln.code_snippet:
            md += f"""```
{self._truncate_snippet(vuln.code_snippet)}
```

"""
        
        if self.config.include_recommendations and vuln.recommendation:
            md += f"**Recommendation:** {vuln.recommendation}\n\n"
        
        md += "---\n\n"
        return md
    
    def _severity_meets_threshold(self, severity: VulnerabilitySeverity) -> bool:
        """Check if severity meets the configured threshold."""
        severity_order = {
            VulnerabilitySeverity.CRITICAL: 5,
            VulnerabilitySeverity.HIGH: 4,
            VulnerabilitySeverity.MEDIUM: 3,
            VulnerabilitySeverity.LOW: 2,
            VulnerabilitySeverity.INFO: 1,
        }
        
        return severity_order.get(severity, 0) >= severity_order.get(self.config.severity_threshold, 0)
    
    def _truncate_snippet(self, snippet: Optional[str]) -> Optional[str]:
        """Truncate code snippet to configured length."""
        if not snippet:
            return None
        
        if len(snippet) <= self.config.max_snippet_length:
            return snippet
        
        return snippet[:self.config.max_snippet_length] + "..."
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    
    async def _save_report(self, content: str, output_path: str):
        """Save report content to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Report saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save report to {output_path}: {e}")
            raise
