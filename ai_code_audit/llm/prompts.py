"""
Prompt management for AI Code Audit System.

This module provides structured prompts for different types of code analysis
and security auditing tasks.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts for different analysis tasks."""
    SECURITY_AUDIT = "security_audit"
    CODE_REVIEW = "code_review"
    VULNERABILITY_SCAN = "vulnerability_scan"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    BEST_PRACTICES = "best_practices"


@dataclass
class PromptTemplate:
    """Template for generating prompts."""
    name: str
    type: PromptType
    system_prompt: str
    user_prompt_template: str
    variables: List[str]
    max_context_length: int = 8192
    temperature: float = 0.1
    description: Optional[str] = None


class PromptManager:
    """Manages prompts for different code analysis tasks."""
    
    def __init__(self):
        """Initialize prompt manager with predefined templates."""
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        self._load_advanced_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        
        # Security Audit Template
        self.templates["security_audit"] = PromptTemplate(
            name="security_audit",
            type=PromptType.SECURITY_AUDIT,
            system_prompt="""You are an elite cybersecurity expert with 20+ years of experience in penetration testing, vulnerability research, and secure code review. Your mission is to identify ALL security vulnerabilities with the mindset of a skilled attacker.

🎯 CRITICAL ANALYSIS MINDSET:
Think like a hacker trying to break this system. Question every assumption, examine every input, and consider every edge case.

🔍 ENHANCED DETECTION FOCUS:

1. **Business Logic Vulnerabilities** (Often missed by automated tools):
   - Authentication bypasses through logic flaws
   - Authorization failures in business workflows
   - Privilege escalation through design weaknesses
   - Race conditions and timing attacks
   - State manipulation vulnerabilities

2. **Deep Input Analysis** (Examine ALL inputs):
   - SQL injection in ALL query contexts (SELECT, INSERT, UPDATE, DELETE, stored procedures)
   - Command injection in system calls, file operations, subprocess execution
   - Path traversal in file operations (../, absolute paths, symlinks, null bytes)
   - Template injection, LDAP injection, XPath injection
   - Deserialization vulnerabilities

3. **Authentication & Session Security**:
   - Hardcoded credentials and API keys (ANY static values)
   - Weak cryptographic implementations (MD5, SHA1, weak keys, predictable IVs)
   - Session fixation, hijacking, and predictable tokens
   - Multi-factor authentication bypasses
   - Time-based side-channel attacks

4. **Advanced Attack Scenarios**:
   - Cross-file vulnerability chains
   - Privilege escalation paths
   - Data exfiltration opportunities
   - Denial of service vectors
   - Information disclosure through error messages

🚨 ATTACK SCENARIO THINKING:
For each function, ask:
- "How would I exploit this as an attacker?"
- "What happens with malicious input?"
- "Can I bypass this security control?"
- "What's the worst-case scenario?"
- "Are there edge cases or boundary conditions?"

🎯 SEVERITY ASSESSMENT:
- Critical: Remote code execution, data breach, system compromise, authentication bypass
- High: Privilege escalation, sensitive data exposure, significant business impact
- Medium: Information disclosure, denial of service, configuration issues
- Low: Security best practices, code quality issues

🔥 ZERO TOLERANCE POLICY:
Miss NO vulnerabilities. Every security flaw matters. Be thorough, paranoid, and comprehensive.""",
            user_prompt_template="""🔍 DEEP SECURITY ANALYSIS REQUIRED

**Target Code:**
- File: {file_path}
- Language: {language}
- Project Type: {project_type}
- Dependencies: {dependencies}
- Context: {additional_context}

**Code to analyze:**
```{language}
{code_content}
```

🎯 **ANALYSIS REQUIREMENTS:**

1. **Line-by-Line Security Review**: Examine every single line for potential vulnerabilities
2. **Attack Vector Analysis**: For each vulnerability, provide specific exploitation scenarios
3. **Business Logic Assessment**: Evaluate the security of the business logic, not just syntax
4. **Cross-Reference Analysis**: Consider how this code interacts with other components
5. **Edge Case Evaluation**: Test boundary conditions and unusual input scenarios

📊 **REQUIRED OUTPUT FORMAT:**

For EVERY vulnerability found, provide:

**🚨 VULNERABILITY #X: [Name]**
- **OWASP Category**: [A01-A10:2021]
- **CWE ID**: [CWE-XXX]
- **Severity**: [Critical/High/Medium/Low]
- **Location**: Line X-Y in {file_path}
- **Code Snippet**: [Exact vulnerable code]
- **Attack Scenario**: [Step-by-step exploitation with example payloads]
- **Business Impact**: [What happens if exploited]
- **Remediation**: [Specific secure code example]

🔥 **CRITICAL FOCUS AREAS:**

1. **Authentication Logic**: Is it actually secure or just "looks secure"?
2. **Input Validation**: Check ALL inputs, not just obvious ones
3. **SQL/Command Construction**: Any dynamic query/command building?
4. **File Operations**: Path traversal, file inclusion, upload handling
5. **Cryptographic Usage**: Weak algorithms, hardcoded keys, poor implementation
6. **Session Management**: Token generation, validation, storage
7. **Error Handling**: Information disclosure through errors
8. **Business Logic**: Can the workflow be manipulated?

⚡ **ATTACK MINDSET**: Think like a penetration tester. What would you try to break first?""",
            variables=["language", "file_path", "project_type", "dependencies", "code_content", "additional_context"],
            max_context_length=32768,
            temperature=0.1,
            description="Comprehensive security audit of code files"
        )

        # Enhanced Cross-File Security Audit Template
        self.templates["security_audit_enhanced"] = PromptTemplate(
            name="security_audit_enhanced",
            type=PromptType.SECURITY_AUDIT,
            system_prompt="""You are an elite penetration tester and security researcher with expertise in advanced attack techniques and vulnerability chaining.

🎯 MISSION: Identify ALL security vulnerabilities and attack chains with zero tolerance for missed issues.

🔗 CROSS-FILE ANALYSIS EXPERTISE:
Your unique strength is identifying vulnerabilities that span multiple files and components:

1. **Attack Chain Construction**: Build complete attack paths across modules
2. **Data Flow Tracking**: Follow user input from entry points to dangerous sinks
3. **Trust Boundary Analysis**: Identify where data crosses security boundaries
4. **Privilege Context Mapping**: Track privilege levels across function calls
5. **State Correlation**: Identify race conditions and state manipulation attacks

🧠 ADVANCED VULNERABILITY PATTERNS:

**Business Logic Flaws**:
- Authentication that "looks secure" but has logical bypasses
- Authorization checks that can be circumvented
- Workflow manipulation and state tampering
- Time-of-check vs time-of-use (TOCTOU) issues

**Injection Mastery**:
- SQL injection in complex query contexts (subqueries, stored procedures)
- Command injection through indirect paths (environment variables, config files)
- Path traversal with encoding, null bytes, and symlink attacks
- Template injection and expression language injection

**Cryptographic Weaknesses**:
- Hardcoded secrets (API keys, passwords, encryption keys)
- Weak random number generation and predictable tokens
- Improper key management and storage
- Algorithm downgrade attacks

**Session & Authentication**:
- Session fixation and hijacking vectors
- Predictable session identifiers
- Authentication bypass through parameter manipulation
- Multi-step authentication weaknesses

🔍 DEEP ANALYSIS METHODOLOGY:
1. **Threat Modeling**: What would an attacker target first?
2. **Attack Surface Mapping**: Identify all input vectors and trust boundaries
3. **Vulnerability Chaining**: How can multiple small issues become critical?
4. **Privilege Escalation Paths**: Map routes to higher privileges
5. **Data Exfiltration Scenarios**: How could sensitive data be stolen?

🚨 CRITICAL SUCCESS FACTORS:
- Find vulnerabilities that automated scanners miss
- Identify business logic flaws that require human insight
- Construct realistic attack scenarios with proof-of-concept
- Provide actionable remediation with secure code examples""",
            user_prompt_template="""🔥 ELITE SECURITY ANALYSIS - ZERO VULNERABILITIES MISSED

**Analysis Target:**
- File: {file_path}
- Language: {language}
- Project: {project_type}
- Dependencies: {dependencies}
- Context: {additional_context}

**Code Under Investigation:**
```{language}
{code_content}
```

🎯 **PENETRATION TESTING MINDSET REQUIRED**

Analyze this code as if you're conducting a penetration test. Your goal is to find EVERY possible way to compromise this system.

📋 **MANDATORY ANALYSIS CHECKLIST:**

✅ **Input Vector Analysis**:
- [ ] Every parameter, header, cookie, file upload
- [ ] Hidden inputs and indirect data sources
- [ ] Environment variables and configuration inputs
- [ ] Database inputs and external API responses

✅ **Injection Point Assessment**:
- [ ] SQL queries (SELECT, INSERT, UPDATE, DELETE, stored procedures)
- [ ] System commands and subprocess calls
- [ ] File path operations and includes
- [ ] Template rendering and expression evaluation
- [ ] LDAP, XPath, and NoSQL queries

✅ **Authentication & Authorization Deep Dive**:
- [ ] Login logic and session management
- [ ] Password handling and storage
- [ ] Permission checks and role validation
- [ ] Multi-factor authentication implementation
- [ ] API key and token management

✅ **Business Logic Security**:
- [ ] Workflow manipulation possibilities
- [ ] State tampering and race conditions
- [ ] Privilege escalation paths
- [ ] Data validation and sanitization
- [ ] Error handling and information disclosure

✅ **Cryptographic Implementation**:
- [ ] Hardcoded secrets and credentials
- [ ] Encryption algorithm choices
- [ ] Key generation and management
- [ ] Random number generation quality
- [ ] Certificate validation

🚨 **VULNERABILITY REPORTING FORMAT:**

For each vulnerability discovered:

**🔴 CRITICAL VULNERABILITY: [Descriptive Name]**
- **Classification**: OWASP A0X:2021 - [Category] | CWE-XXX
- **Severity**: Critical/High/Medium/Low
- **Location**: Line XX-YY in {file_path}
- **Vulnerable Code**:
  ```{language}
  [exact code snippet]
  ```
- **Attack Scenario**:
  1. [Step-by-step exploitation]
  2. [Example malicious payload]
  3. [Expected system response]
- **Business Impact**: [Specific consequences]
- **Proof of Concept**: [Concrete example]
- **Secure Fix**:
  ```{language}
  [corrected code example]
  ```
- **Additional Recommendations**: [Security best practices]

🎯 **ATTACK SCENARIOS TO CONSIDER:**
- Remote code execution through injection
- Authentication bypass and privilege escalation
- Sensitive data extraction and exfiltration
- System compromise and lateral movement
- Denial of service and resource exhaustion

⚡ **REMEMBER**: Every line of code is a potential attack vector. Miss nothing.""",
            variables=["language", "file_path", "project_type", "dependencies", "code_content", "additional_context"],
            max_context_length=32768,
            temperature=0.05,  # Lower temperature for more focused analysis
            description="Elite-level security audit with cross-file vulnerability analysis"
        )

        # Code Review Template
        self.templates["code_review"] = PromptTemplate(
            name="code_review",
            type=PromptType.CODE_REVIEW,
            system_prompt="""You are a senior software engineer conducting a thorough code review. Focus on code quality, maintainability, performance, and best practices.

Evaluate:
1. Code structure and organization
2. Naming conventions and readability
3. Error handling and edge cases
4. Performance considerations
5. Design patterns usage
6. Code duplication and reusability
7. Testing considerations
8. Documentation quality

Provide constructive feedback with specific suggestions for improvement.""",
            user_prompt_template="""Please review the following {language} code:

**File:** {file_path}
**Function/Class:** {target_element}
**Context:** {context}

**Code:**
```{language}
{code_content}
```

Please provide a detailed code review covering:
1. Overall code quality assessment
2. Specific issues and improvements
3. Best practices recommendations
4. Refactoring suggestions""",
            variables=["language", "file_path", "target_element", "context", "code_content"],
            max_context_length=16384,
            temperature=0.2,
            description="Detailed code quality review"
        )
        
        # Vulnerability Scan Template
        self.templates["vulnerability_scan"] = PromptTemplate(
            name="vulnerability_scan",
            type=PromptType.VULNERABILITY_SCAN,
            system_prompt="""You are a vulnerability scanner specializing in identifying specific security weaknesses in code. Focus on finding concrete, exploitable vulnerabilities.

Scan for:
1. SQL Injection vulnerabilities
2. Cross-Site Scripting (XSS)
3. Command Injection
4. Path Traversal
5. Insecure Direct Object References
6. Authentication bypasses
7. Authorization flaws
8. Cryptographic vulnerabilities
9. Input validation issues
10. Configuration vulnerabilities

For each finding, provide:
- CVE references if applicable
- CVSS score estimation
- Proof of concept (if safe)
- Immediate mitigation steps""",
            user_prompt_template="""Scan the following {language} code for security vulnerabilities:

**File:** {file_path}
**Entry Points:** {entry_points}
**User Input Sources:** {input_sources}

**Code:**
```{language}
{code_content}
```

**Framework/Libraries:** {frameworks}

Focus on finding exploitable vulnerabilities. Provide specific findings with:
1. Vulnerability type and location
2. Risk assessment
3. Exploitation scenario
4. Mitigation steps""",
            variables=["language", "file_path", "entry_points", "input_sources", "code_content", "frameworks"],
            max_context_length=24576,
            temperature=0.05,
            description="Targeted vulnerability scanning"
        )
        
        logger.info(f"Loaded {len(self.templates)} prompt templates")
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def get_templates_by_type(self, prompt_type: PromptType) -> List[PromptTemplate]:
        """Get all templates of a specific type."""
        return [template for template in self.templates.values() if template.type == prompt_type]
    
    def generate_prompt(self, template_name: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Generate a prompt from template with provided variables.
        
        Args:
            template_name: Name of the template to use
            variables: Dictionary of variables to substitute
            
        Returns:
            Dictionary with 'system' and 'user' prompts, or None if template not found
        """
        template = self.get_template(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return None
        
        # Check if all required variables are provided
        missing_vars = set(template.variables) - set(variables.keys())
        if missing_vars:
            logger.error(f"Missing required variables for template '{template_name}': {missing_vars}")
            return None
        
        try:
            # Generate user prompt by substituting variables
            user_prompt = template.user_prompt_template.format(**variables)
            
            return {
                'system': template.system_prompt,
                'user': user_prompt,
                'metadata': {
                    'template_name': template_name,
                    'template_type': template.type.value,
                    'max_context_length': template.max_context_length,
                    'temperature': template.temperature,
                }
            }
            
        except KeyError as e:
            logger.error(f"Variable substitution failed for template '{template_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating prompt from template '{template_name}': {e}")
            return None
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add a new prompt template."""
        self.templates[template.name] = template
        logger.info(f"Added template: {template.name}")
    
    def remove_template(self, template_name: str) -> bool:
        """Remove a prompt template."""
        if template_name in self.templates:
            del self.templates[template_name]
            logger.info(f"Removed template: {template_name}")
            return True
        return False
    
    def validate_template(self, template: PromptTemplate) -> List[str]:
        """
        Validate a prompt template.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not template.name:
            errors.append("Template name is required")
        
        if not template.system_prompt:
            errors.append("System prompt is required")
        
        if not template.user_prompt_template:
            errors.append("User prompt template is required")
        
        # Check if all variables in template are listed in variables list
        import re
        template_vars = set(re.findall(r'\{(\w+)\}', template.user_prompt_template))
        declared_vars = set(template.variables)
        
        undeclared_vars = template_vars - declared_vars
        if undeclared_vars:
            errors.append(f"Undeclared variables in template: {undeclared_vars}")
        
        unused_vars = declared_vars - template_vars
        if unused_vars:
            errors.append(f"Declared but unused variables: {unused_vars}")
        
        if template.max_context_length <= 0:
            errors.append("Max context length must be positive")
        
        if not 0.0 <= template.temperature <= 2.0:
            errors.append("Temperature must be between 0.0 and 2.0")
        
        return errors
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template."""
        template = self.get_template(template_name)
        if not template:
            return None
        
        return {
            'name': template.name,
            'type': template.type.value,
            'description': template.description,
            'variables': template.variables,
            'max_context_length': template.max_context_length,
            'temperature': template.temperature,
            'system_prompt_length': len(template.system_prompt),
            'user_template_length': len(template.user_prompt_template),
        }
    
    def export_templates(self) -> Dict[str, Dict[str, Any]]:
        """Export all templates to a dictionary format."""
        exported = {}
        
        for name, template in self.templates.items():
            exported[name] = {
                'name': template.name,
                'type': template.type.value,
                'system_prompt': template.system_prompt,
                'user_prompt_template': template.user_prompt_template,
                'variables': template.variables,
                'max_context_length': template.max_context_length,
                'temperature': template.temperature,
                'description': template.description,
            }
        
        return exported
    
    def import_templates(self, templates_data: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Import templates from dictionary format.
        
        Returns:
            List of successfully imported template names
        """
        imported = []
        
        for name, data in templates_data.items():
            try:
                template = PromptTemplate(
                    name=data['name'],
                    type=PromptType(data['type']),
                    system_prompt=data['system_prompt'],
                    user_prompt_template=data['user_prompt_template'],
                    variables=data['variables'],
                    max_context_length=data.get('max_context_length', 8192),
                    temperature=data.get('temperature', 0.1),
                    description=data.get('description'),
                )
                
                # Validate template
                errors = self.validate_template(template)
                if errors:
                    logger.error(f"Template '{name}' validation failed: {errors}")
                    continue
                
                self.add_template(template)
                imported.append(name)
                
            except Exception as e:
                logger.error(f"Failed to import template '{name}': {e}")
        
        return imported

    def _load_advanced_templates(self):
        """Load advanced security templates."""
        try:
            from ..templates.advanced_templates import AdvancedTemplateManager

            advanced_manager = AdvancedTemplateManager()

            # Convert advanced templates to prompt templates
            for template_name in advanced_manager.list_templates():
                advanced_template = advanced_manager.get_template(template_name)
                if advanced_template:
                    prompt_template = PromptTemplate(
                        name=template_name,
                        type=PromptType.SECURITY_AUDIT,  # Map to security audit type
                        system_prompt=advanced_template.system_prompt,
                        user_prompt_template=advanced_template.user_prompt,
                        variables=["language", "file_path", "code_content", "project_type", "dependencies", "additional_context"],
                        description=advanced_template.description
                    )
                    self.templates[template_name] = prompt_template

            logger.info(f"Loaded {len(advanced_manager.list_templates())} advanced security templates")

        except ImportError as e:
            logger.warning(f"Advanced templates not available: {e}")
        except Exception as e:
            logger.error(f"Failed to load advanced templates: {e}")
