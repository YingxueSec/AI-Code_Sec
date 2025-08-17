"""
Coverage reporting system for AI Code Audit System.

This module provides comprehensive coverage reporting including:
- Visual coverage reports with charts and graphs
- Gap analysis and recommendations
- Coverage trend tracking
- Interactive HTML reports
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging

from .coverage_tracker import CoverageTracker, CoverageReport, CoverageStats, CodeUnit, Priority

logger = logging.getLogger(__name__)


@dataclass
class CoverageInsight:
    """Coverage analysis insight."""
    title: str
    description: str
    severity: str  # info, warning, critical
    recommendation: str
    affected_files: List[str]
    metrics: Dict[str, Any]


class CoverageReporter:
    """Comprehensive coverage reporting system."""
    
    def __init__(self, coverage_tracker: CoverageTracker):
        """Initialize coverage reporter."""
        self.tracker = coverage_tracker
    
    def generate_html_report(self, output_path: str) -> str:
        """Generate interactive HTML coverage report."""
        report = self.tracker.generate_coverage_report()
        insights = self._analyze_coverage_gaps(report)
        
        html_content = self._build_html_report(report, insights)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML coverage report generated: {output_path}")
        return html_content
    
    def generate_json_report(self, output_path: str) -> Dict[str, Any]:
        """Generate JSON coverage report."""
        report = self.tracker.generate_coverage_report()
        insights = self._analyze_coverage_gaps(report)
        
        json_data = {
            'project_path': report.project_path,
            'generated_at': report.generated_at.isoformat(),
            'summary': {
                'total_units': report.total_stats.total_units,
                'analyzed_units': report.total_stats.analyzed_units,
                'coverage_percentage': report.total_stats.coverage_percentage,
                'success_rate': report.total_stats.success_rate,
                'pending_units': report.total_stats.pending_units,
                'failed_units': report.total_stats.failed_units,
                'skipped_units': report.total_stats.skipped_units
            },
            'file_coverage': {
                file_path: {
                    'total': stats.total_units,
                    'analyzed': stats.analyzed_units,
                    'coverage': stats.coverage_percentage,
                    'pending': stats.pending_units,
                    'failed': stats.failed_units
                }
                for file_path, stats in report.file_stats.items()
            },
            'uncovered_units': [
                {
                    'id': unit.id,
                    'name': unit.name,
                    'file_path': unit.file_path,
                    'unit_type': unit.unit_type.value,
                    'priority': unit.priority.value,
                    'line_range': f"{unit.start_line}-{unit.end_line}",
                    'line_count': unit.line_count
                }
                for unit in report.uncovered_units
            ],
            'high_priority_gaps': [
                {
                    'id': unit.id,
                    'name': unit.name,
                    'file_path': unit.file_path,
                    'priority': unit.priority.value,
                    'reason': self._get_priority_reason(unit)
                }
                for unit in report.high_priority_gaps
            ],
            'insights': [
                {
                    'title': insight.title,
                    'description': insight.description,
                    'severity': insight.severity,
                    'recommendation': insight.recommendation,
                    'affected_files': insight.affected_files,
                    'metrics': insight.metrics
                }
                for insight in insights
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON coverage report generated: {output_path}")
        return json_data
    
    def generate_markdown_report(self, output_path: str) -> str:
        """Generate Markdown coverage report."""
        report = self.tracker.generate_coverage_report()
        insights = self._analyze_coverage_gaps(report)
        
        md_content = self._build_markdown_report(report, insights)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown coverage report generated: {output_path}")
        return md_content
    
    def _analyze_coverage_gaps(self, report: CoverageReport) -> List[CoverageInsight]:
        """Analyze coverage gaps and generate insights."""
        insights = []
        
        # Overall coverage analysis
        if report.total_stats.coverage_percentage < 50:
            insights.append(CoverageInsight(
                title="Low Overall Coverage",
                description=f"Only {report.total_stats.coverage_percentage:.1f}% of code units have been analyzed.",
                severity="critical",
                recommendation="Increase analysis scope or reduce file filtering to improve coverage.",
                affected_files=[],
                metrics={'coverage_percentage': report.total_stats.coverage_percentage}
            ))
        elif report.total_stats.coverage_percentage < 80:
            insights.append(CoverageInsight(
                title="Moderate Coverage",
                description=f"Coverage is at {report.total_stats.coverage_percentage:.1f}%. Consider analyzing more units.",
                severity="warning",
                recommendation="Focus on high-priority uncovered units to improve security coverage.",
                affected_files=[],
                metrics={'coverage_percentage': report.total_stats.coverage_percentage}
            ))
        
        # High-priority gaps analysis
        if report.high_priority_gaps:
            critical_gaps = [u for u in report.high_priority_gaps if u.priority == Priority.CRITICAL]
            if critical_gaps:
                insights.append(CoverageInsight(
                    title="Critical Security Gaps",
                    description=f"Found {len(critical_gaps)} critical security-related units that haven't been analyzed.",
                    severity="critical",
                    recommendation="Prioritize analysis of critical security functions and authentication code.",
                    affected_files=list(set(u.file_path for u in critical_gaps)),
                    metrics={'critical_gaps': len(critical_gaps)}
                ))
        
        # File-level coverage analysis
        low_coverage_files = []
        for file_path, stats in report.file_stats.items():
            if stats.coverage_percentage < 30 and stats.total_units > 1:
                low_coverage_files.append((file_path, stats.coverage_percentage))
        
        if low_coverage_files:
            insights.append(CoverageInsight(
                title="Files with Low Coverage",
                description=f"Found {len(low_coverage_files)} files with less than 30% coverage.",
                severity="warning",
                recommendation="Review these files for important functions that may have been skipped.",
                affected_files=[f[0] for f in low_coverage_files],
                metrics={'low_coverage_files': len(low_coverage_files)}
            ))
        
        # Failed analysis insights
        if report.total_stats.failed_units > 0:
            failure_rate = (report.total_stats.failed_units / report.total_stats.total_units) * 100
            insights.append(CoverageInsight(
                title="Analysis Failures",
                description=f"{report.total_stats.failed_units} units failed analysis ({failure_rate:.1f}% failure rate).",
                severity="warning" if failure_rate < 10 else "critical",
                recommendation="Review failed units for syntax errors or configuration issues.",
                affected_files=[],
                metrics={'failed_units': report.total_stats.failed_units, 'failure_rate': failure_rate}
            ))
        
        return insights
    
    def _get_priority_reason(self, unit: CodeUnit) -> str:
        """Get reason why unit has high priority."""
        name_lower = unit.name.lower()
        path_lower = unit.file_path.lower()
        
        if any(pattern in name_lower or pattern in path_lower for pattern in [
            'auth', 'login', 'password'
        ]):
            return "Authentication-related code"
        elif any(pattern in name_lower or pattern in path_lower for pattern in [
            'admin', 'security', 'crypto'
        ]):
            return "Security-critical functionality"
        elif any(pattern in name_lower or pattern in path_lower for pattern in [
            'api', 'endpoint', 'controller'
        ]):
            return "API endpoint or controller"
        else:
            return "High business impact"
    
    def _build_html_report(self, report: CoverageReport, insights: List[CoverageInsight]) -> str:
        """Build HTML coverage report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Coverage Report - {project_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-box {{ background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-box h3 {{ margin: 0; font-size: 2em; }}
        .stat-box p {{ margin: 5px 0 0 0; color: #666; }}
        .coverage-bar {{ width: 100%; height: 20px; background: #ddd; border-radius: 10px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); }}
        .insight {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .insight.critical {{ border-left: 5px solid #dc3545; }}
        .insight.warning {{ border-left: 5px solid #ffc107; }}
        .insight.info {{ border-left: 5px solid #17a2b8; }}
        .file-list {{ max-height: 300px; overflow-y: auto; }}
        .unit-item {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .priority-critical {{ color: #dc3545; font-weight: bold; }}
        .priority-high {{ color: #fd7e14; font-weight: bold; }}
        .priority-medium {{ color: #ffc107; }}
        .priority-low {{ color: #28a745; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Code Coverage Report</h1>
        <p><strong>Project:</strong> {project_path}</p>
        <p><strong>Generated:</strong> {generated_at}</p>
    </div>
    
    <div class="summary">
        <div class="stat-box">
            <h3>{total_units}</h3>
            <p>Total Units</p>
        </div>
        <div class="stat-box">
            <h3>{analyzed_units}</h3>
            <p>Analyzed</p>
        </div>
        <div class="stat-box">
            <h3>{coverage_percentage:.1f}%</h3>
            <p>Coverage</p>
            <div class="coverage-bar">
                <div class="coverage-fill" style="width: {coverage_percentage}%;"></div>
            </div>
        </div>
        <div class="stat-box">
            <h3>{pending_units}</h3>
            <p>Pending</p>
        </div>
    </div>
    
    <h2>Coverage Insights</h2>
    {insights_html}
    
    <h2>File Coverage Details</h2>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Total Units</th>
                <th>Analyzed</th>
                <th>Coverage</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {file_coverage_html}
        </tbody>
    </table>
    
    <h2>High Priority Gaps</h2>
    <div class="file-list">
        {high_priority_gaps_html}
    </div>
    
    <h2>Uncovered Units</h2>
    <div class="file-list">
        {uncovered_units_html}
    </div>
</body>
</html>
        """
        
        # Generate insights HTML
        insights_html = ""
        for insight in insights:
            insights_html += f"""
            <div class="insight {insight.severity}">
                <h3>{insight.title}</h3>
                <p>{insight.description}</p>
                <p><strong>Recommendation:</strong> {insight.recommendation}</p>
                {f'<p><strong>Affected Files:</strong> {", ".join(insight.affected_files[:5])}</p>' if insight.affected_files else ''}
            </div>
            """
        
        # Generate file coverage HTML
        file_coverage_html = ""
        for file_path, stats in report.file_stats.items():
            status_class = "success" if stats.coverage_percentage > 80 else "warning" if stats.coverage_percentage > 50 else "danger"
            file_coverage_html += f"""
            <tr>
                <td>{Path(file_path).name}</td>
                <td>{stats.total_units}</td>
                <td>{stats.analyzed_units}</td>
                <td>{stats.coverage_percentage:.1f}%</td>
                <td><span class="{status_class}">{stats.coverage_percentage:.1f}%</span></td>
            </tr>
            """
        
        # Generate high priority gaps HTML
        high_priority_gaps_html = ""
        for unit in report.high_priority_gaps[:20]:  # Limit to top 20
            priority_class = f"priority-{unit.priority.name.lower()}"
            high_priority_gaps_html += f"""
            <div class="unit-item">
                <strong class="{priority_class}">{unit.name}</strong> 
                <span style="color: #666;">({unit.unit_type.value})</span><br>
                <small>{unit.file_path}:{unit.start_line}-{unit.end_line}</small><br>
                <small>{self._get_priority_reason(unit)}</small>
            </div>
            """
        
        # Generate uncovered units HTML
        uncovered_units_html = ""
        for unit in report.uncovered_units[:50]:  # Limit to top 50
            priority_class = f"priority-{unit.priority.name.lower()}"
            uncovered_units_html += f"""
            <div class="unit-item">
                <strong class="{priority_class}">{unit.name}</strong> 
                <span style="color: #666;">({unit.unit_type.value})</span><br>
                <small>{unit.file_path}:{unit.start_line}-{unit.end_line} ({unit.line_count} lines)</small>
            </div>
            """
        
        return html_template.format(
            project_name=Path(report.project_path).name,
            project_path=report.project_path,
            generated_at=report.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            total_units=report.total_stats.total_units,
            analyzed_units=report.total_stats.analyzed_units,
            coverage_percentage=report.total_stats.coverage_percentage,
            pending_units=report.total_stats.pending_units,
            insights_html=insights_html,
            file_coverage_html=file_coverage_html,
            high_priority_gaps_html=high_priority_gaps_html,
            uncovered_units_html=uncovered_units_html
        )
    
    def _build_markdown_report(self, report: CoverageReport, insights: List[CoverageInsight]) -> str:
        """Build Markdown coverage report."""
        md_content = f"""# Code Coverage Report

## Project Information
- **Project:** {report.project_path}
- **Generated:** {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}

## Coverage Summary
- **Total Units:** {report.total_stats.total_units}
- **Analyzed Units:** {report.total_stats.analyzed_units}
- **Coverage:** {report.total_stats.coverage_percentage:.1f}%
- **Success Rate:** {report.total_stats.success_rate:.1f}%
- **Pending:** {report.total_stats.pending_units}
- **Failed:** {report.total_stats.failed_units}
- **Skipped:** {report.total_stats.skipped_units}

## Coverage Insights

"""
        
        for insight in insights:
            severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(insight.severity, "ℹ️")
            md_content += f"""### {severity_emoji} {insight.title}

{insight.description}

**Recommendation:** {insight.recommendation}

"""
            if insight.affected_files:
                md_content += f"**Affected Files:** {', '.join(insight.affected_files[:5])}\n\n"
        
        md_content += """## File Coverage Details

| File | Total | Analyzed | Coverage | Status |
|------|-------|----------|----------|--------|
"""
        
        for file_path, stats in report.file_stats.items():
            status_emoji = "✅" if stats.coverage_percentage > 80 else "⚠️" if stats.coverage_percentage > 50 else "❌"
            md_content += f"| {Path(file_path).name} | {stats.total_units} | {stats.analyzed_units} | {stats.coverage_percentage:.1f}% | {status_emoji} |\n"
        
        if report.high_priority_gaps:
            md_content += f"""
## High Priority Gaps ({len(report.high_priority_gaps)} items)

"""
            for unit in report.high_priority_gaps[:10]:
                priority_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(unit.priority.name, "⚪")
                md_content += f"- {priority_emoji} **{unit.name}** ({unit.unit_type.value}) - `{unit.file_path}:{unit.start_line}-{unit.end_line}`\n"
                md_content += f"  - {self._get_priority_reason(unit)}\n"
        
        return md_content
