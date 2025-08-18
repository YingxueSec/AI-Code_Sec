"""
Enhanced AI Security Analyzer with Multi-Stage Analysis
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ..core.models import FileInfo, AnalysisResult, VulnerabilityInfo
from ..llm.client import LLMClient
from ..llm.prompts import PromptManager

logger = logging.getLogger(__name__)


class AnalysisStage(Enum):
    """Multi-stage analysis phases"""
    INITIAL_SCAN = "initial_scan"
    DEEP_ANALYSIS = "deep_analysis"
    CROSS_FILE_CORRELATION = "cross_file_correlation"
    ATTACK_CHAIN_CONSTRUCTION = "attack_chain_construction"
    BUSINESS_LOGIC_REVIEW = "business_logic_review"


@dataclass
class VulnerabilityChain:
    """Represents a chain of vulnerabilities across files"""
    chain_id: str
    severity: str
    attack_path: List[str]
    files_involved: List[str]
    description: str
    exploitation_scenario: str
    business_impact: str


class EnhancedSecurityAnalyzer:
    """Enhanced AI security analyzer with multi-stage analysis capabilities"""
    
    def __init__(self, llm_client: LLMClient, prompt_manager: PromptManager):
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.attack_chains: List[VulnerabilityChain] = []
        
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Load enhanced vulnerability detection patterns"""
        return {
            "sql_injection": [
                r"execute\s*\(\s*[\"'].*\{.*\}.*[\"']\s*\)",
                r"cursor\.execute\s*\(\s*f[\"'].*\{.*\}.*[\"']\s*\)",
                r"query\s*=\s*[\"'].*\{.*\}.*[\"']",
                r"SELECT.*\+.*",
                r"INSERT.*\+.*",
                r"UPDATE.*\+.*",
                r"DELETE.*\+.*"
            ],
            "command_injection": [
                r"subprocess\.(run|call|Popen).*shell\s*=\s*True",
                r"os\.system\s*\(",
                r"os\.popen\s*\(",
                r"eval\s*\(",
                r"exec\s*\(",
                r"__import__\s*\("
            ],
            "path_traversal": [
                r"open\s*\(\s*.*\+.*\)",
                r"file_path\s*=.*\+",
                r"\.\.\/",
                r"os\.path\.join\s*\(.*user.*\)",
                r"pathlib\.Path\s*\(.*user.*\)"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*[\"'][^\"']+[\"']",
                r"api_key\s*=\s*[\"'][^\"']+[\"']",
                r"secret\s*=\s*[\"'][^\"']+[\"']",
                r"token\s*=\s*[\"'][^\"']+[\"']",
                r"key\s*=\s*[\"'][^\"']+[\"']"
            ],
            "weak_crypto": [
                r"hashlib\.md5\s*\(",
                r"hashlib\.sha1\s*\(",
                r"random\.random\s*\(",
                r"time\.time\s*\(\)",
                r"DES\s*\(",
                r"RC4\s*\("
            ],
            "authentication_bypass": [
                r"if.*user_id.*in.*:",
                r"if.*len\s*\(.*user.*\)\s*>\s*0",
                r"if.*user.*is not None",
                r"return.*True",
                r"admin.*=.*\[.*\]"
            ]
        }
    
    async def analyze_with_enhanced_detection(
        self, 
        files: List[FileInfo], 
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform enhanced multi-stage security analysis
        """
        logger.info(f"Starting enhanced analysis of {len(files)} files")
        
        results = {
            "stage_results": {},
            "vulnerability_chains": [],
            "critical_findings": [],
            "recommendations": [],
            "analysis_metadata": {
                "total_files": len(files),
                "analysis_stages": len(AnalysisStage),
                "patterns_checked": sum(len(patterns) for patterns in self.vulnerability_patterns.values())
            }
        }
        
        # Stage 1: Initial vulnerability scan with enhanced patterns
        stage1_results = await self._stage1_initial_scan(files)
        results["stage_results"]["initial_scan"] = stage1_results
        
        # Stage 2: Deep analysis with enhanced prompts
        stage2_results = await self._stage2_deep_analysis(files, stage1_results)
        results["stage_results"]["deep_analysis"] = stage2_results
        
        # Stage 3: Cross-file correlation analysis
        stage3_results = await self._stage3_cross_file_analysis(files, stage2_results)
        results["stage_results"]["cross_file_correlation"] = stage3_results
        
        # Stage 4: Attack chain construction
        stage4_results = await self._stage4_attack_chain_construction(stage3_results)
        results["stage_results"]["attack_chain_construction"] = stage4_results
        
        # Stage 5: Business logic review
        stage5_results = await self._stage5_business_logic_review(files, project_context)
        results["stage_results"]["business_logic_review"] = stage5_results
        
        # Consolidate findings
        results["vulnerability_chains"] = self.attack_chains
        results["critical_findings"] = self._extract_critical_findings(results["stage_results"])
        results["recommendations"] = self._generate_enhanced_recommendations(results)
        
        logger.info(f"Enhanced analysis completed. Found {len(results['critical_findings'])} critical issues")
        return results
    
    async def _stage1_initial_scan(self, files: List[FileInfo]) -> Dict[str, Any]:
        """Stage 1: Pattern-based vulnerability detection"""
        logger.info("Stage 1: Initial vulnerability pattern scan")
        
        findings = {}
        for file_info in files:
            file_findings = []
            
            # Read file content
            try:
                with open(file_info.absolute_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Apply vulnerability patterns
                for vuln_type, patterns in self.vulnerability_patterns.items():
                    for pattern in patterns:
                        import re
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            file_findings.append({
                                "type": vuln_type,
                                "pattern": pattern,
                                "line": line_num,
                                "match": match.group(),
                                "severity": self._assess_pattern_severity(vuln_type)
                            })
                
                findings[file_info.path] = file_findings
                
            except Exception as e:
                logger.error(f"Error scanning {file_info.path}: {e}")
                findings[file_info.path] = []
        
        return findings
    
    async def _stage2_deep_analysis(self, files: List[FileInfo], stage1_results: Dict) -> Dict[str, Any]:
        """Stage 2: AI-powered deep analysis with enhanced prompts"""
        logger.info("Stage 2: Deep AI analysis with enhanced prompts")
        
        deep_findings = {}
        
        for file_info in files:
            try:
                # Use enhanced security audit template
                template = self.prompt_manager.get_template("security_audit_enhanced")
                if not template:
                    template = self.prompt_manager.get_template("security_audit")
                
                # Read file content
                with open(file_info.absolute_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Prepare context with stage 1 findings
                stage1_context = stage1_results.get(file_info.path, [])
                additional_context = f"Previous scan found {len(stage1_context)} potential issues: {[f['type'] for f in stage1_context]}"
                
                # Generate analysis prompt
                prompt = template.format_prompt(
                    language=file_info.language or 'python',
                    file_path=file_info.path,
                    project_type='web_application',
                    dependencies='flask, sqlite3, subprocess',
                    code_content=content,
                    additional_context=additional_context
                )
                
                # Get AI analysis
                response = await self.llm_client.generate_response(
                    prompt.system_prompt,
                    prompt.user_prompt,
                    temperature=0.05,  # Lower temperature for more focused analysis
                    max_tokens=4096
                )
                
                deep_findings[file_info.path] = {
                    "ai_analysis": response,
                    "stage1_findings": stage1_context,
                    "analysis_quality": self._assess_analysis_quality(response)
                }
                
            except Exception as e:
                logger.error(f"Error in deep analysis of {file_info.path}: {e}")
                deep_findings[file_info.path] = {"error": str(e)}
        
        return deep_findings
    
    async def _stage3_cross_file_analysis(self, files: List[FileInfo], stage2_results: Dict) -> Dict[str, Any]:
        """Stage 3: Cross-file vulnerability correlation"""
        logger.info("Stage 3: Cross-file vulnerability correlation")
        
        # This is where we'd implement sophisticated cross-file analysis
        # For now, we'll create a simplified version
        
        correlations = []
        file_paths = [f.path for f in files]
        
        # Look for function calls between files
        for file_info in files:
            try:
                with open(file_info.absolute_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find imports and function calls
                import re
                imports = re.findall(r'from\s+(\w+)\s+import\s+(\w+)', content)
                calls = re.findall(r'(\w+)\s*\(', content)
                
                for imp_module, imp_func in imports:
                    for other_file in files:
                        if imp_module in other_file.path and other_file.path != file_info.path:
                            correlations.append({
                                "source_file": file_info.path,
                                "target_file": other_file.path,
                                "connection_type": "import",
                                "function": imp_func,
                                "risk_level": "medium"
                            })
                
            except Exception as e:
                logger.error(f"Error in cross-file analysis of {file_info.path}: {e}")
        
        return {"correlations": correlations}
    
    async def _stage4_attack_chain_construction(self, stage3_results: Dict) -> Dict[str, Any]:
        """Stage 4: Construct attack chains from correlated vulnerabilities"""
        logger.info("Stage 4: Attack chain construction")
        
        # Simplified attack chain construction
        chains = []
        correlations = stage3_results.get("correlations", [])
        
        for correlation in correlations:
            if correlation["risk_level"] == "high":
                chain = VulnerabilityChain(
                    chain_id=f"chain_{len(chains) + 1}",
                    severity="high",
                    attack_path=[correlation["source_file"], correlation["target_file"]],
                    files_involved=[correlation["source_file"], correlation["target_file"]],
                    description=f"Cross-file vulnerability chain via {correlation['function']}",
                    exploitation_scenario="Attacker could chain vulnerabilities across files",
                    business_impact="Potential for privilege escalation or data breach"
                )
                chains.append(chain)
                self.attack_chains.append(chain)
        
        return {"attack_chains": [chain.__dict__ for chain in chains]}
    
    async def _stage5_business_logic_review(self, files: List[FileInfo], project_context: Dict) -> Dict[str, Any]:
        """Stage 5: Business logic security review"""
        logger.info("Stage 5: Business logic security review")
        
        # This would involve sophisticated business logic analysis
        # For now, we'll provide a framework
        
        business_issues = []
        
        for file_info in files:
            if "auth" in file_info.path.lower():
                business_issues.append({
                    "file": file_info.path,
                    "issue": "Authentication logic requires manual review",
                    "severity": "high",
                    "recommendation": "Verify authentication logic against business requirements"
                })
        
        return {"business_logic_issues": business_issues}
    
    def _assess_pattern_severity(self, vuln_type: str) -> str:
        """Assess severity based on vulnerability type"""
        severity_map = {
            "sql_injection": "critical",
            "command_injection": "critical",
            "path_traversal": "high",
            "hardcoded_secrets": "critical",
            "weak_crypto": "medium",
            "authentication_bypass": "critical"
        }
        return severity_map.get(vuln_type, "medium")
    
    def _assess_analysis_quality(self, analysis: str) -> str:
        """Assess the quality of AI analysis"""
        if len(analysis) > 2000 and "vulnerability" in analysis.lower():
            return "high"
        elif len(analysis) > 1000:
            return "medium"
        else:
            return "low"
    
    def _extract_critical_findings(self, stage_results: Dict) -> List[Dict]:
        """Extract critical findings from all stages"""
        critical_findings = []
        
        # Extract from stage 1
        for file_path, findings in stage_results.get("initial_scan", {}).items():
            for finding in findings:
                if finding["severity"] == "critical":
                    critical_findings.append({
                        "source": "pattern_scan",
                        "file": file_path,
                        "type": finding["type"],
                        "line": finding["line"],
                        "severity": "critical"
                    })
        
        # Extract from attack chains
        for chain in stage_results.get("attack_chain_construction", {}).get("attack_chains", []):
            if chain["severity"] == "high":
                critical_findings.append({
                    "source": "attack_chain",
                    "description": chain["description"],
                    "files": chain["files_involved"],
                    "severity": "critical"
                })
        
        return critical_findings
    
    def _generate_enhanced_recommendations(self, results: Dict) -> List[str]:
        """Generate enhanced security recommendations"""
        recommendations = [
            "Implement parameterized queries for all database operations",
            "Use subprocess with shell=False and validate all inputs",
            "Implement proper path validation for file operations",
            "Remove all hardcoded credentials and use secure configuration",
            "Upgrade to strong cryptographic algorithms (SHA-256+, AES)",
            "Implement proper authentication and session management",
            "Add comprehensive input validation and sanitization",
            "Implement proper error handling without information disclosure",
            "Add security logging and monitoring",
            "Conduct regular security code reviews and penetration testing"
        ]
        
        return recommendations
