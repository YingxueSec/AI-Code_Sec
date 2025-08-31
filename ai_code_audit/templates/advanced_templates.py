"""
Advanced security analysis templates for AI Code Audit System.

This module provides professional security analysis templates including:
- OWASP Top 10 focused analysis
- CWE classification and mapping
- Industry-specific security standards
- Compliance-focused auditing templates
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SecurityStandard(Enum):
    """Security standards and frameworks."""
    OWASP_TOP_10 = "owasp_top_10"
    CWE_TOP_25 = "cwe_top_25"
    NIST_CYBERSECURITY = "nist_cybersecurity"
    ISO_27001 = "iso_27001"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOX = "sox"
    GDPR = "gdpr"


class VulnerabilityClass(Enum):
    """Vulnerability classification."""
    INJECTION = "injection"
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    XXE = "xml_external_entities"
    BROKEN_ACCESS = "broken_access_control"
    SECURITY_MISCONFIG = "security_misconfiguration"
    XSS = "cross_site_scripting"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_COMPONENTS = "vulnerable_components"
    INSUFFICIENT_LOGGING = "insufficient_logging"


@dataclass
class SecurityTemplate:
    """Security analysis template."""
    name: str
    description: str
    standard: SecurityStandard
    vulnerability_classes: List[VulnerabilityClass]
    system_prompt: str
    user_prompt: str
    analysis_focus: List[str]
    cwe_mappings: Dict[str, List[str]]
    compliance_requirements: List[str]
    severity_guidelines: Dict[str, str]


class AdvancedTemplateManager:
    """Manager for advanced security analysis templates."""
    
    def __init__(self):
        """Initialize template manager."""
        self.templates: Dict[str, SecurityTemplate] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all security templates."""
        # OWASP Top 10 2021 Template
        self.templates["owasp_top_10_2021"] = SecurityTemplate(
            name="OWASP Top 10 2021 Security Analysis",
            description="Comprehensive security analysis based on OWASP Top 10 2021",
            standard=SecurityStandard.OWASP_TOP_10,
            vulnerability_classes=[
                VulnerabilityClass.BROKEN_ACCESS,
                VulnerabilityClass.INJECTION,
                VulnerabilityClass.INSECURE_DESERIALIZATION,
                VulnerabilityClass.BROKEN_AUTH,
                VulnerabilityClass.SECURITY_MISCONFIG,
                VulnerabilityClass.VULNERABLE_COMPONENTS,
                VulnerabilityClass.SENSITIVE_DATA,
                VulnerabilityClass.INSUFFICIENT_LOGGING,
                VulnerabilityClass.XSS,
                VulnerabilityClass.XXE
            ],
            system_prompt=self._get_owasp_system_prompt(),
            user_prompt=self._get_owasp_user_prompt(),
            analysis_focus=[
                "Access control mechanisms",
                "Input validation and sanitization",
                "Authentication and session management",
                "Data protection and encryption",
                "Error handling and logging",
                "Third-party dependencies",
                "Configuration security"
            ],
            cwe_mappings=self._get_owasp_cwe_mappings(),
            compliance_requirements=[
                "Implement proper access controls",
                "Validate all inputs",
                "Use secure authentication",
                "Protect sensitive data",
                "Log security events",
                "Keep components updated"
            ],
            severity_guidelines={
                "critical": "Direct exploitation possible with high impact",
                "high": "Exploitation likely with significant impact",
                "medium": "Exploitation possible with moderate impact",
                "low": "Limited exploitation potential or impact"
            }
        )
        
        # CWE Top 25 Template
        self.templates["cwe_top_25"] = SecurityTemplate(
            name="CWE Top 25 Most Dangerous Weaknesses",
            description="Analysis focused on CWE Top 25 most dangerous software weaknesses",
            standard=SecurityStandard.CWE_TOP_25,
            vulnerability_classes=[
                VulnerabilityClass.INJECTION,
                VulnerabilityClass.BROKEN_ACCESS,
                VulnerabilityClass.XSS,
                VulnerabilityClass.SENSITIVE_DATA
            ],
            system_prompt=self._get_cwe_system_prompt(),
            user_prompt=self._get_cwe_user_prompt(),
            analysis_focus=[
                "Buffer overflows and memory corruption",
                "Injection vulnerabilities",
                "Cross-site scripting",
                "Path traversal",
                "Race conditions",
                "Cryptographic issues",
                "Input validation failures"
            ],
            cwe_mappings=self._get_cwe_top_25_mappings(),
            compliance_requirements=[
                "Implement secure coding practices",
                "Use memory-safe languages where possible",
                "Validate and sanitize all inputs",
                "Implement proper error handling"
            ],
            severity_guidelines={
                "critical": "CWE with CVSS 9.0+ potential",
                "high": "CWE with CVSS 7.0-8.9 potential",
                "medium": "CWE with CVSS 4.0-6.9 potential",
                "low": "CWE with CVSS below 4.0 potential"
            }
        )
        
        # PCI DSS Template
        self.templates["pci_dss"] = SecurityTemplate(
            name="PCI DSS Compliance Analysis",
            description="Security analysis focused on PCI DSS compliance requirements",
            standard=SecurityStandard.PCI_DSS,
            vulnerability_classes=[
                VulnerabilityClass.SENSITIVE_DATA,
                VulnerabilityClass.BROKEN_AUTH,
                VulnerabilityClass.SECURITY_MISCONFIG,
                VulnerabilityClass.INSUFFICIENT_LOGGING
            ],
            system_prompt=self._get_pci_system_prompt(),
            user_prompt=self._get_pci_user_prompt(),
            analysis_focus=[
                "Cardholder data protection",
                "Encryption in transit and at rest",
                "Access control and authentication",
                "Network security controls",
                "Vulnerability management",
                "Logging and monitoring"
            ],
            cwe_mappings=self._get_pci_cwe_mappings(),
            compliance_requirements=[
                "Protect stored cardholder data",
                "Encrypt transmission of cardholder data",
                "Use and regularly update anti-virus software",
                "Develop and maintain secure systems",
                "Restrict access by business need-to-know",
                "Assign unique ID to each person with computer access"
            ],
            severity_guidelines={
                "critical": "Direct PCI DSS violation with data exposure risk",
                "high": "Significant PCI DSS compliance gap",
                "medium": "Minor PCI DSS compliance issue",
                "low": "Best practice recommendation for PCI DSS"
            }
        )
        
        # GDPR Privacy Template
        self.templates["gdpr_privacy"] = SecurityTemplate(
            name="GDPR Privacy and Data Protection Analysis",
            description="Analysis focused on GDPR compliance and data privacy",
            standard=SecurityStandard.GDPR,
            vulnerability_classes=[
                VulnerabilityClass.SENSITIVE_DATA,
                VulnerabilityClass.BROKEN_ACCESS,
                VulnerabilityClass.INSUFFICIENT_LOGGING
            ],
            system_prompt=self._get_gdpr_system_prompt(),
            user_prompt=self._get_gdpr_user_prompt(),
            analysis_focus=[
                "Personal data identification and classification",
                "Data minimization principles",
                "Consent management",
                "Data subject rights implementation",
                "Data breach detection and notification",
                "Privacy by design implementation"
            ],
            cwe_mappings=self._get_gdpr_cwe_mappings(),
            compliance_requirements=[
                "Implement data protection by design",
                "Ensure lawful basis for processing",
                "Provide data subject rights",
                "Implement appropriate security measures",
                "Maintain processing records",
                "Report data breaches within 72 hours"
            ],
            severity_guidelines={
                "critical": "High risk to data subject rights and freedoms",
                "high": "Significant GDPR compliance violation",
                "medium": "Moderate privacy risk or compliance gap",
                "low": "Minor privacy consideration or best practice"
            }
        )
        
        logger.info(f"Loaded {len(self.templates)} advanced security templates")
    
    def get_template(self, template_name: str) -> Optional[SecurityTemplate]:
        """Get security template by name."""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List available template names."""
        return list(self.templates.keys())
    
    def get_templates_by_standard(self, standard: SecurityStandard) -> List[SecurityTemplate]:
        """Get templates for a specific security standard."""
        return [t for t in self.templates.values() if t.standard == standard]
    
    def _get_owasp_system_prompt(self) -> str:
        """Get OWASP Top 10 system prompt."""
        return """You are a senior security analyst specializing in OWASP Top 10 vulnerabilities. 
Your task is to perform a comprehensive security analysis of the provided code, focusing specifically on the OWASP Top 10 2021 categories:

1. A01:2021 – Broken Access Control
2. A02:2021 – Cryptographic Failures  
3. A03:2021 – Injection
4. A04:2021 – Insecure Design
5. A05:2021 – Security Misconfiguration
6. A06:2021 – Vulnerable and Outdated Components
7. A07:2021 – Identification and Authentication Failures
8. A08:2021 – Software and Data Integrity Failures
9. A09:2021 – Security Logging and Monitoring Failures
10. A10:2021 – Server-Side Request Forgery (SSRF)

For each vulnerability found, provide:
- OWASP category classification
- CWE mapping where applicable
- Severity assessment (Critical/High/Medium/Low)
- Specific code location and context
- Exploitation scenario
- Remediation recommendations
- Compliance impact

Focus on practical, actionable findings that developers can immediately address."""
    
    def _get_owasp_user_prompt(self) -> str:
        """Get OWASP Top 10 user prompt."""
        return """Analyze the following {language} code for OWASP Top 10 2021 vulnerabilities:

File: {file_path}
Language: {language}

Code to analyze:
```{language}
{code_content}
```

Please provide a detailed security analysis covering:

1. **Access Control Issues**: Look for broken authorization, privilege escalation, CORS misconfigurations
2. **Cryptographic Failures**: Check for weak encryption, hardcoded secrets, insecure random number generation
3. **Injection Vulnerabilities**: Identify SQL injection, NoSQL injection, command injection, LDAP injection
4. **Insecure Design**: Assess architectural security flaws and missing security controls
5. **Security Misconfigurations**: Find default configurations, unnecessary features, verbose error messages
6. **Vulnerable Components**: Identify outdated libraries and dependencies with known vulnerabilities
7. **Authentication Failures**: Check for weak authentication, session management issues, credential stuffing vulnerabilities
8. **Integrity Failures**: Look for insecure deserialization, software supply chain attacks
9. **Logging Failures**: Assess logging coverage, sensitive data in logs, monitoring gaps
10. **SSRF Vulnerabilities**: Check for server-side request forgery and related issues

For each finding, provide the OWASP category, severity, and specific remediation steps."""
    
    def _get_cwe_system_prompt(self) -> str:
        """Get CWE Top 25 system prompt."""
        return """You are a security researcher specializing in the CWE Top 25 Most Dangerous Software Weaknesses.
Your analysis should focus on identifying and classifying vulnerabilities according to the CWE framework.

Key CWE categories to analyze:
- CWE-79: Cross-site Scripting
- CWE-89: SQL Injection  
- CWE-20: Improper Input Validation
- CWE-125: Out-of-bounds Read
- CWE-78: OS Command Injection
- CWE-22: Path Traversal
- CWE-352: Cross-Site Request Forgery
- CWE-434: Unrestricted Upload of File with Dangerous Type
- CWE-862: Missing Authorization
- CWE-476: NULL Pointer Dereference

Provide detailed CWE classifications, CVSS scoring guidance, and technical remediation approaches."""
    
    def _get_cwe_user_prompt(self) -> str:
        """Get CWE Top 25 user prompt."""
        return """Perform a CWE-focused security analysis of this {language} code:

File: {file_path}
```{language}
{code_content}
```

Identify vulnerabilities from the CWE Top 25 list and provide:
- Specific CWE identifier and description
- CVSS score estimation
- Technical exploitation details
- Code-level remediation steps
- Prevention strategies"""
    
    def _get_pci_system_prompt(self) -> str:
        """Get PCI DSS system prompt."""
        return """You are a PCI DSS compliance specialist analyzing code for payment card industry security requirements.
Focus on the 12 PCI DSS requirements and how the code implements or violates these controls.

Key areas of analysis:
- Cardholder data protection and storage
- Encryption requirements
- Access control implementation
- Network security controls
- Vulnerability management
- Security testing procedures"""
    
    def _get_pci_user_prompt(self) -> str:
        """Get PCI DSS user prompt."""
        return """Analyze this {language} code for PCI DSS compliance:

File: {file_path}
```{language}
{code_content}
```

Evaluate compliance with PCI DSS requirements:
1. Cardholder data protection
2. Encryption implementation
3. Access controls
4. Security configurations
5. Vulnerability management
6. Logging and monitoring

Provide specific PCI DSS requirement mappings and remediation guidance."""
    
    def _get_gdpr_system_prompt(self) -> str:
        """Get GDPR system prompt."""
        return """You are a privacy engineer specializing in GDPR compliance analysis.
Focus on data protection principles, data subject rights, and privacy by design implementation.

Key analysis areas:
- Personal data identification and classification
- Lawful basis for processing
- Data minimization implementation
- Data subject rights support
- Privacy by design principles
- Data breach prevention"""
    
    def _get_gdpr_user_prompt(self) -> str:
        """Get GDPR user prompt."""
        return """Analyze this {language} code for GDPR compliance and privacy protection:

File: {file_path}
```{language}
{code_content}
```

Evaluate:
1. Personal data handling
2. Consent management
3. Data subject rights implementation
4. Data minimization practices
5. Privacy by design principles
6. Data breach prevention measures

Provide GDPR article references and privacy-enhancing recommendations."""
    
    def _get_owasp_cwe_mappings(self) -> Dict[str, List[str]]:
        """Get OWASP to CWE mappings."""
        return {
            "A01_Broken_Access_Control": ["CWE-22", "CWE-284", "CWE-862"],
            "A02_Cryptographic_Failures": ["CWE-327", "CWE-328", "CWE-329"],
            "A03_Injection": ["CWE-79", "CWE-89", "CWE-78"],
            "A04_Insecure_Design": ["CWE-209", "CWE-256", "CWE-501"],
            "A05_Security_Misconfiguration": ["CWE-16", "CWE-2", "CWE-11"],
            "A06_Vulnerable_Components": ["CWE-1104", "CWE-937"],
            "A07_Auth_Failures": ["CWE-287", "CWE-384", "CWE-613"],
            "A08_Integrity_Failures": ["CWE-502", "CWE-829"],
            "A09_Logging_Failures": ["CWE-778", "CWE-117"],
            "A10_SSRF": ["CWE-918"]
        }
    
    def _get_cwe_top_25_mappings(self) -> Dict[str, List[str]]:
        """Get CWE Top 25 mappings."""
        return {
            "Input_Validation": ["CWE-20", "CWE-79", "CWE-89"],
            "Memory_Safety": ["CWE-125", "CWE-787", "CWE-476"],
            "Access_Control": ["CWE-862", "CWE-863", "CWE-269"],
            "Path_Traversal": ["CWE-22", "CWE-434"],
            "Command_Injection": ["CWE-78", "CWE-77"],
            "Cryptographic": ["CWE-327", "CWE-330"]
        }
    
    def _get_pci_cwe_mappings(self) -> Dict[str, List[str]]:
        """Get PCI DSS to CWE mappings."""
        return {
            "Data_Protection": ["CWE-311", "CWE-312", "CWE-319"],
            "Access_Control": ["CWE-284", "CWE-862", "CWE-863"],
            "Encryption": ["CWE-327", "CWE-328", "CWE-329"],
            "Logging": ["CWE-778", "CWE-117", "CWE-532"]
        }
    
    def _get_gdpr_cwe_mappings(self) -> Dict[str, List[str]]:
        """Get GDPR to CWE mappings."""
        return {
            "Data_Exposure": ["CWE-200", "CWE-209", "CWE-532"],
            "Access_Control": ["CWE-284", "CWE-862"],
            "Data_Integrity": ["CWE-345", "CWE-353"],
            "Privacy_Controls": ["CWE-359", "CWE-201"]
        }
