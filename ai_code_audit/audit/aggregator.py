"""
Result aggregator for collecting and processing analysis results.

This module provides result aggregation capabilities including:
- Result collection and standardization
- Vulnerability deduplication and classification
- Severity assessment and priority ranking
- Statistical analysis and insights
"""

import re
import hashlib
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(Enum):
    """Vulnerability categories."""
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SENSITIVE_DATA = "sensitive_data"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    SESSION_MANAGEMENT = "session_management"
    CONFIGURATION = "configuration"
    CODE_QUALITY = "code_quality"
    DEPENDENCY = "dependency"
    OTHER = "other"


@dataclass
class VulnerabilityFinding:
    """Individual vulnerability finding."""
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    category: VulnerabilityCategory
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            content = f"{self.title}_{self.file_path}_{self.line_number or 0}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class CodeQualityIssue:
    """Code quality issue finding."""
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditResult:
    """Complete audit result for a session."""
    session_id: str
    project_path: str
    project_name: str
    vulnerabilities: List[VulnerabilityFinding] = field(default_factory=list)
    quality_issues: List[CodeQualityIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_findings(self) -> int:
        """Get total number of findings."""
        return len(self.vulnerabilities) + len(self.quality_issues)
    
    @property
    def critical_count(self) -> int:
        """Get count of critical findings."""
        return len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        """Get count of high severity findings."""
        return len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.HIGH])
    
    @property
    def risk_score(self) -> float:
        """Calculate overall risk score."""
        if not self.vulnerabilities:
            return 0.0
        
        severity_weights = {
            VulnerabilitySeverity.CRITICAL: 10.0,
            VulnerabilitySeverity.HIGH: 7.0,
            VulnerabilitySeverity.MEDIUM: 4.0,
            VulnerabilitySeverity.LOW: 2.0,
            VulnerabilitySeverity.INFO: 0.5,
        }
        
        total_score = sum(severity_weights.get(v.severity, 0) * v.confidence for v in self.vulnerabilities)
        max_possible = len(self.vulnerabilities) * 10.0
        
        return min(10.0, (total_score / max_possible) * 10.0) if max_possible > 0 else 0.0


class ResultAggregator:
    """Aggregator for processing and analyzing audit results."""
    
    def __init__(self):
        """Initialize result aggregator."""
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.quality_patterns = self._load_quality_patterns()
        self.deduplication_cache: Set[str] = set()
    
    async def aggregate_results(
        self,
        session_id: str,
        project_path: str,
        project_name: str,
        raw_results: List[Dict[str, Any]]
    ) -> AuditResult:
        """Aggregate raw analysis results into structured audit result."""
        logger.info(f"Aggregating results for session {session_id}")
        
        audit_result = AuditResult(
            session_id=session_id,
            project_path=project_path,
            project_name=project_name
        )
        
        # Process each raw result
        for raw_result in raw_results:
            try:
                findings = await self._extract_findings(raw_result)
                
                for finding in findings:
                    if isinstance(finding, VulnerabilityFinding):
                        # Check for duplicates
                        if not self._is_duplicate_vulnerability(finding, audit_result.vulnerabilities):
                            audit_result.vulnerabilities.append(finding)
                    elif isinstance(finding, CodeQualityIssue):
                        audit_result.quality_issues.append(finding)
                
            except Exception as e:
                logger.error(f"Error processing result for {raw_result.get('file_path', 'unknown')}: {e}")
        
        # Sort findings by severity and confidence
        audit_result.vulnerabilities.sort(
            key=lambda x: (x.severity.value, -x.confidence, x.file_path)
        )
        
        # Generate statistics
        audit_result.statistics = self._generate_statistics(audit_result)
        
        # Add metadata
        audit_result.metadata = {
            'total_files_analyzed': len(raw_results),
            'analysis_duration': self._calculate_analysis_duration(raw_results),
            'models_used': list(set(r.get('model', 'unknown') for r in raw_results)),
            'templates_used': list(set(r.get('template', 'unknown') for r in raw_results)),
        }
        
        logger.info(f"Aggregation complete: {audit_result.total_findings} findings")
        return audit_result
    
    async def _extract_findings(self, raw_result: Dict[str, Any]) -> List[Any]:
        """Extract structured findings from raw analysis result."""
        findings = []
        
        analysis_text = raw_result.get('analysis', '')
        file_path = raw_result.get('file_path', 'unknown')
        
        if not analysis_text:
            return findings
        
        # Extract vulnerabilities
        vulnerabilities = self._extract_vulnerabilities(analysis_text, file_path)
        findings.extend(vulnerabilities)
        
        # Extract quality issues
        quality_issues = self._extract_quality_issues(analysis_text, file_path)
        findings.extend(quality_issues)
        
        return findings
    
    def _extract_vulnerabilities(self, analysis_text: str, file_path: str) -> List[VulnerabilityFinding]:
        """Extract vulnerability findings from analysis text."""
        vulnerabilities = []
        
        # Look for structured vulnerability reports
        vuln_patterns = [
            r'(?i)vulnerability[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?i)security\s+issue[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?i)potential\s+risk[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)',
        ]
        
        for pattern in vuln_patterns:
            matches = re.finditer(pattern, analysis_text, re.DOTALL)
            for match in matches:
                vuln_text = match.group(1).strip()
                
                # Parse vulnerability details
                vulnerability = self._parse_vulnerability_text(vuln_text, file_path)
                if vulnerability:
                    vulnerabilities.append(vulnerability)
        
        # Look for specific vulnerability types
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, analysis_text, re.IGNORECASE):
                    vulnerability = self._create_vulnerability_from_pattern(
                        vuln_type, analysis_text, file_path
                    )
                    if vulnerability:
                        vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    def _extract_quality_issues(self, analysis_text: str, file_path: str) -> List[CodeQualityIssue]:
        """Extract code quality issues from analysis text."""
        quality_issues = []
        
        # Look for quality-related patterns
        quality_patterns = [
            r'(?i)code\s+quality[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?i)improvement[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?i)suggestion[:\s]+(.+?)(?=\n\n|\n[A-Z]|\Z)',
        ]
        
        for pattern in quality_patterns:
            matches = re.finditer(pattern, analysis_text, re.DOTALL)
            for match in matches:
                issue_text = match.group(1).strip()
                
                quality_issue = self._parse_quality_issue_text(issue_text, file_path)
                if quality_issue:
                    quality_issues.append(quality_issue)
        
        return quality_issues
    
    def _parse_vulnerability_text(self, vuln_text: str, file_path: str) -> Optional[VulnerabilityFinding]:
        """Parse vulnerability from text description."""
        try:
            # Extract title (first line or sentence)
            lines = vuln_text.split('\n')
            title = lines[0].strip()
            
            # Extract line number if present
            line_match = re.search(r'line\s+(\d+)', vuln_text, re.IGNORECASE)
            line_number = int(line_match.group(1)) if line_match else None
            
            # Determine severity
            severity = self._determine_severity(vuln_text)
            
            # Determine category
            category = self._determine_category(vuln_text)
            
            # Extract code snippet
            code_match = re.search(r'```[\w]*\n(.*?)\n```', vuln_text, re.DOTALL)
            code_snippet = code_match.group(1).strip() if code_match else None
            
            # Extract CWE ID
            cwe_match = re.search(r'CWE-(\d+)', vuln_text, re.IGNORECASE)
            cwe_id = f"CWE-{cwe_match.group(1)}" if cwe_match else None
            
            return VulnerabilityFinding(
                id="",  # Will be auto-generated
                title=title,
                description=vuln_text,
                severity=severity,
                category=category,
                file_path=file_path,
                line_number=line_number,
                code_snippet=code_snippet,
                cwe_id=cwe_id,
                confidence=self._calculate_confidence(vuln_text)
            )
            
        except Exception as e:
            logger.error(f"Error parsing vulnerability text: {e}")
            return None
    
    def _parse_quality_issue_text(self, issue_text: str, file_path: str) -> Optional[CodeQualityIssue]:
        """Parse quality issue from text description."""
        try:
            lines = issue_text.split('\n')
            title = lines[0].strip()
            
            # Extract line number
            line_match = re.search(r'line\s+(\d+)', issue_text, re.IGNORECASE)
            line_number = int(line_match.group(1)) if line_match else None
            
            # Determine severity
            severity = self._determine_quality_severity(issue_text)
            
            return CodeQualityIssue(
                id=hashlib.md5(f"{title}_{file_path}_{line_number or 0}".encode()).hexdigest()[:12],
                title=title,
                description=issue_text,
                severity=severity,
                file_path=file_path,
                line_number=line_number
            )
            
        except Exception as e:
            logger.error(f"Error parsing quality issue text: {e}")
            return None
    
    def _determine_severity(self, text: str) -> VulnerabilitySeverity:
        """Determine vulnerability severity from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'severe', 'dangerous', 'exploit']):
            return VulnerabilitySeverity.CRITICAL
        elif any(word in text_lower for word in ['high', 'important', 'significant']):
            return VulnerabilitySeverity.HIGH
        elif any(word in text_lower for word in ['medium', 'moderate', 'potential']):
            return VulnerabilitySeverity.MEDIUM
        elif any(word in text_lower for word in ['low', 'minor', 'informational']):
            return VulnerabilitySeverity.LOW
        else:
            return VulnerabilitySeverity.MEDIUM
    
    def _determine_category(self, text: str) -> VulnerabilityCategory:
        """Determine vulnerability category from text."""
        text_lower = text.lower()
        
        category_keywords = {
            VulnerabilityCategory.INJECTION: ['injection', 'sql', 'xss', 'command', 'ldap'],
            VulnerabilityCategory.AUTHENTICATION: ['authentication', 'login', 'password', 'credential'],
            VulnerabilityCategory.AUTHORIZATION: ['authorization', 'access control', 'permission'],
            VulnerabilityCategory.SENSITIVE_DATA: ['sensitive', 'data exposure', 'information disclosure'],
            VulnerabilityCategory.CRYPTOGRAPHY: ['crypto', 'encryption', 'hash', 'certificate'],
            VulnerabilityCategory.INPUT_VALIDATION: ['validation', 'sanitization', 'input'],
            VulnerabilityCategory.SESSION_MANAGEMENT: ['session', 'cookie', 'token'],
            VulnerabilityCategory.CONFIGURATION: ['configuration', 'config', 'setting'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return VulnerabilityCategory.OTHER
    
    def _determine_quality_severity(self, text: str) -> VulnerabilitySeverity:
        """Determine quality issue severity."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'major', 'serious']):
            return VulnerabilitySeverity.HIGH
        elif any(word in text_lower for word in ['important', 'significant']):
            return VulnerabilitySeverity.MEDIUM
        else:
            return VulnerabilitySeverity.LOW
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for finding."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for specific indicators
        if re.search(r'line\s+\d+', text, re.IGNORECASE):
            confidence += 0.2
        
        if '```' in text:  # Code snippet present
            confidence += 0.2
        
        if re.search(r'CWE-\d+', text, re.IGNORECASE):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _is_duplicate_vulnerability(
        self,
        new_vuln: VulnerabilityFinding,
        existing_vulns: List[VulnerabilityFinding]
    ) -> bool:
        """Check if vulnerability is a duplicate."""
        for existing in existing_vulns:
            # Same file and similar title
            if (existing.file_path == new_vuln.file_path and
                self._similarity_score(existing.title, new_vuln.title) > 0.8):
                return True
            
            # Same category and line number
            if (existing.category == new_vuln.category and
                existing.line_number == new_vuln.line_number and
                existing.file_path == new_vuln.file_path):
                return True
        
        return False
    
    def _similarity_score(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _generate_statistics(self, audit_result: AuditResult) -> Dict[str, Any]:
        """Generate statistics for audit result."""
        vulns = audit_result.vulnerabilities
        
        # Severity distribution
        severity_counts = {}
        for severity in VulnerabilitySeverity:
            severity_counts[severity.value] = len([v for v in vulns if v.severity == severity])
        
        # Category distribution
        category_counts = {}
        for category in VulnerabilityCategory:
            category_counts[category.value] = len([v for v in vulns if v.category == category])
        
        # File distribution
        file_counts = {}
        for vuln in vulns:
            file_counts[vuln.file_path] = file_counts.get(vuln.file_path, 0) + 1
        
        return {
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'file_distribution': dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'total_vulnerabilities': len(vulns),
            'total_quality_issues': len(audit_result.quality_issues),
            'risk_score': audit_result.risk_score,
            'average_confidence': sum(v.confidence for v in vulns) / len(vulns) if vulns else 0.0,
        }
    
    def _calculate_analysis_duration(self, raw_results: List[Dict[str, Any]]) -> float:
        """Calculate total analysis duration in seconds."""
        # This would need to be implemented based on timing data in raw_results
        return 0.0
    
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Load vulnerability detection patterns."""
        return {
            'sql_injection': [
                r'sql.*injection',
                r'execute.*query.*user.*input',
                r'concatenat.*sql.*string',
            ],
            'xss': [
                r'cross.*site.*script',
                r'user.*input.*html',
                r'innerHTML.*user',
            ],
            'path_traversal': [
                r'path.*traversal',
                r'\.\./',
                r'directory.*traversal',
            ],
        }
    
    def _load_quality_patterns(self) -> Dict[str, List[str]]:
        """Load code quality patterns."""
        return {
            'complexity': [
                r'complex.*function',
                r'too.*many.*parameters',
                r'nested.*loops',
            ],
            'maintainability': [
                r'duplicate.*code',
                r'long.*method',
                r'large.*class',
            ],
        }
    
    def _create_vulnerability_from_pattern(
        self,
        vuln_type: str,
        analysis_text: str,
        file_path: str
    ) -> Optional[VulnerabilityFinding]:
        """Create vulnerability finding from pattern match."""
        # This would create a standardized vulnerability based on the pattern type
        # Implementation would depend on specific vulnerability types
        return None
