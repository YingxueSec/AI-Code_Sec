"""
Advanced Vulnerability Detection Patterns
针对遗漏漏洞的专项检测模式库
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VulnerabilityCategory(Enum):
    """漏洞分类"""
    BUSINESS_LOGIC = "business_logic"
    ADVANCED_INJECTION = "advanced_injection"
    CONFIGURATION_SECURITY = "configuration_security"
    RACE_CONDITIONS = "race_conditions"
    CRYPTOGRAPHIC_FLAWS = "cryptographic_flaws"
    SESSION_MANAGEMENT = "session_management"
    INPUT_VALIDATION = "input_validation"
    ERROR_HANDLING = "error_handling"


@dataclass
class VulnerabilityPattern:
    """漏洞检测模式"""
    name: str
    category: VulnerabilityCategory
    patterns: List[str]
    severity: str
    description: str
    attack_scenarios: List[str]
    remediation: str


class AdvancedPatternDetector:
    """高级漏洞模式检测器"""
    
    def __init__(self):
        self.patterns = self._load_advanced_patterns()
        self.business_logic_indicators = self._load_business_logic_patterns()
        self.context_patterns = self._load_context_patterns()
    
    def _load_advanced_patterns(self) -> Dict[str, VulnerabilityPattern]:
        """加载高级漏洞检测模式"""
        patterns = {}
        
        # 1. 业务逻辑漏洞模式
        patterns["workflow_bypass"] = VulnerabilityPattern(
            name="工作流绕过漏洞",
            category=VulnerabilityCategory.BUSINESS_LOGIC,
            patterns=[
                r"if\s+step\s*==\s*\d+\s*:",  # 步骤检查
                r"state\s*=\s*['\"].*['\"]",  # 状态设置
                r"workflow\[.*\]\s*=",  # 工作流操作
                r"process_step\s*\(",  # 步骤处理
                r"validate_step\s*\(",  # 步骤验证
                r"skip_step\s*\(",  # 步骤跳过
            ],
            severity="high",
            description="多步骤工作流中的步骤验证不足，可能允许攻击者跳过关键步骤",
            attack_scenarios=[
                "直接访问后续步骤的URL",
                "修改步骤参数绕过验证",
                "并发请求导致状态混乱"
            ],
            remediation="实施严格的步骤验证和状态检查机制"
        )
        
        patterns["state_manipulation"] = VulnerabilityPattern(
            name="状态操纵漏洞",
            category=VulnerabilityCategory.BUSINESS_LOGIC,
            patterns=[
                r"session\[.*\]\s*=.*user",  # 会话状态设置
                r"state\s*=\s*request\.",  # 直接从请求设置状态
                r"status\s*=\s*.*input",  # 状态来自用户输入
                r"role\s*=\s*.*get\(",  # 角色获取
                r"permission\s*=\s*.*user",  # 权限设置
            ],
            severity="critical",
            description="用户可以直接操纵应用程序状态，绕过业务逻辑",
            attack_scenarios=[
                "修改会话中的用户角色",
                "直接设置管理员权限",
                "操纵订单状态和价格"
            ],
            remediation="状态变更必须通过服务端验证，不能依赖客户端输入"
        )
        
        # 2. 高级注入漏洞模式
        patterns["template_injection"] = VulnerabilityPattern(
            name="模板注入漏洞",
            category=VulnerabilityCategory.ADVANCED_INJECTION,
            patterns=[
                r"render_template_string\s*\(",  # Flask模板字符串渲染
                r"Template\s*\(.*\{.*\}",  # Jinja2模板
                r"format\s*\(.*user.*\)",  # 字符串格式化
                r"\.format\s*\(.*request\.",  # 请求数据格式化
                r"%\s*\(.*user.*\)",  # 百分号格式化
                r"f['\"].*\{.*user.*\}",  # f-string with user input
            ],
            severity="critical",
            description="用户输入被直接用于模板渲染，可能导致服务器端模板注入",
            attack_scenarios=[
                "{{7*7}} 测试模板注入",
                "{{config}} 获取应用配置",
                "{{''.__class__.__mro__[2].__subclasses__()}} 获取类信息"
            ],
            remediation="使用安全的模板渲染方法，对用户输入进行严格过滤"
        )
        
        patterns["deserialization"] = VulnerabilityPattern(
            name="反序列化漏洞",
            category=VulnerabilityCategory.ADVANCED_INJECTION,
            patterns=[
                r"pickle\.loads?\s*\(",  # Python pickle
                r"yaml\.load\s*\(",  # YAML加载
                r"json\.loads?\s*\(.*user",  # JSON with user input
                r"marshal\.loads?\s*\(",  # Marshal
                r"eval\s*\(.*user",  # Eval with user input
                r"exec\s*\(.*user",  # Exec with user input
                r"__import__\s*\(.*user",  # Dynamic import
            ],
            severity="critical",
            description="不安全的反序列化可能导致远程代码执行",
            attack_scenarios=[
                "构造恶意pickle对象执行任意代码",
                "YAML炸弹导致拒绝服务",
                "通过反序列化获取系统权限"
            ],
            remediation="避免反序列化不可信数据，使用安全的数据格式如JSON"
        )
        
        # 3. 竞态条件漏洞模式
        patterns["race_conditions"] = VulnerabilityPattern(
            name="竞态条件漏洞",
            category=VulnerabilityCategory.RACE_CONDITIONS,
            patterns=[
                r"threading\.",  # 多线程
                r"multiprocessing\.",  # 多进程
                r"async\s+def",  # 异步函数
                r"await\s+",  # 异步等待
                r"lock\s*=",  # 锁机制
                r"with\s+.*lock",  # 锁使用
                r"time\.sleep\s*\(",  # 时间延迟
                r"check.*then.*use",  # 检查后使用模式
            ],
            severity="high",
            description="并发访问共享资源时缺乏适当的同步机制",
            attack_scenarios=[
                "TOCTOU (Time-of-Check-Time-of-Use) 攻击",
                "并发修改导致数据不一致",
                "竞态条件绕过权限检查"
            ],
            remediation="使用适当的锁机制和原子操作"
        )
        
        # 4. 加密实现缺陷模式
        patterns["crypto_flaws"] = VulnerabilityPattern(
            name="加密实现缺陷",
            category=VulnerabilityCategory.CRYPTOGRAPHIC_FLAWS,
            patterns=[
                r"hashlib\.md5\s*\(",  # MD5哈希
                r"hashlib\.sha1\s*\(",  # SHA1哈希
                r"random\.random\s*\(",  # 弱随机数
                r"time\.time\s*\(\)",  # 时间作为种子
                r"DES\s*\(",  # DES加密
                r"RC4\s*\(",  # RC4加密
                r"ECB\s*mode",  # ECB模式
                r"key\s*=\s*['\"].*['\"]",  # 硬编码密钥
                r"iv\s*=\s*['\"].*['\"]",  # 硬编码IV
                r"salt\s*=\s*['\"].*['\"]",  # 硬编码盐值
            ],
            severity="high",
            description="使用了不安全的加密算法或实现方式",
            attack_scenarios=[
                "MD5/SHA1碰撞攻击",
                "弱随机数预测",
                "ECB模式的模式分析攻击"
            ],
            remediation="使用强加密算法和安全的实现方式"
        )
        
        # 5. 会话管理缺陷模式
        patterns["session_flaws"] = VulnerabilityPattern(
            name="会话管理缺陷",
            category=VulnerabilityCategory.SESSION_MANAGEMENT,
            patterns=[
                r"session_id\s*=\s*.*user",  # 用户控制的会话ID
                r"cookie\[.*\]\s*=.*user",  # 用户控制的Cookie
                r"session\.permanent\s*=\s*True",  # 永久会话
                r"remember_me\s*=\s*True",  # 记住我功能
                r"session_timeout\s*=\s*None",  # 无会话超时
                r"secure\s*=\s*False",  # 不安全的Cookie
                r"httponly\s*=\s*False",  # 非HttpOnly Cookie
            ],
            severity="medium",
            description="会话管理实现存在安全缺陷",
            attack_scenarios=[
                "会话固定攻击",
                "会话劫持",
                "跨站脚本获取会话Cookie"
            ],
            remediation="实施安全的会话管理机制"
        )
        
        return patterns
    
    def _load_business_logic_patterns(self) -> Dict[str, List[str]]:
        """加载业务逻辑漏洞指示器"""
        return {
            "price_manipulation": [
                r"price\s*=\s*.*request\.",
                r"amount\s*=\s*.*user",
                r"total\s*=\s*.*input",
                r"discount\s*=\s*.*get\(",
                r"quantity\s*\*\s*price",
            ],
            "privilege_escalation": [
                r"admin\s*=\s*.*user",
                r"role\s*=\s*.*request\.",
                r"permission\s*=\s*.*input",
                r"is_admin\s*=\s*.*get\(",
                r"user_type\s*=\s*.*user",
            ],
            "workflow_manipulation": [
                r"step\s*=\s*.*request\.",
                r"stage\s*=\s*.*user",
                r"phase\s*=\s*.*input",
                r"status\s*=\s*.*get\(",
                r"state\s*=\s*.*user",
            ]
        }
    
    def _load_context_patterns(self) -> Dict[str, List[str]]:
        """加载上下文相关的漏洞模式"""
        return {
            "financial_context": [
                r"balance\s*[+\-*/]=",
                r"transfer\s*\(",
                r"withdraw\s*\(",
                r"deposit\s*\(",
                r"payment\s*\(",
            ],
            "authentication_context": [
                r"login\s*\(",
                r"authenticate\s*\(",
                r"verify\s*\(",
                r"check_password\s*\(",
                r"validate_user\s*\(",
            ],
            "file_operation_context": [
                r"upload\s*\(",
                r"download\s*\(",
                r"delete\s*\(",
                r"read_file\s*\(",
                r"write_file\s*\(",
            ]
        }
    
    def detect_advanced_vulnerabilities(self, code: str, file_path: str) -> List[Dict]:
        """检测高级漏洞"""
        findings = []
        
        for pattern_name, pattern in self.patterns.items():
            matches = self._find_pattern_matches(code, pattern.patterns)
            if matches:
                for match in matches:
                    finding = {
                        "type": pattern_name,
                        "category": pattern.category.value,
                        "severity": pattern.severity,
                        "description": pattern.description,
                        "location": {
                            "file": file_path,
                            "line": self._get_line_number(code, match['start']),
                            "code": match['text']
                        },
                        "attack_scenarios": pattern.attack_scenarios,
                        "remediation": pattern.remediation,
                        "confidence": self._calculate_confidence(match, pattern)
                    }
                    findings.append(finding)
        
        return findings
    
    def _find_pattern_matches(self, code: str, patterns: List[str]) -> List[Dict]:
        """查找模式匹配"""
        matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE):
                matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(),
                    'pattern': pattern
                })
        return matches
    
    def _get_line_number(self, code: str, position: int) -> int:
        """获取代码位置的行号"""
        return code[:position].count('\n') + 1
    
    def _calculate_confidence(self, match: Dict, pattern: VulnerabilityPattern) -> float:
        """计算检测置信度"""
        # 基础置信度
        confidence = 0.7
        
        # 根据模式复杂度调整
        if len(pattern.patterns) > 3:
            confidence += 0.1
        
        # 根据匹配的代码长度调整
        if len(match['text']) > 20:
            confidence += 0.1
        
        # 根据严重程度调整
        if pattern.severity == "critical":
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def analyze_business_logic_context(self, code: str, file_path: str) -> List[Dict]:
        """分析业务逻辑上下文"""
        findings = []
        
        # 检测价格操纵漏洞
        if any(re.search(pattern, code, re.IGNORECASE) for pattern in self.business_logic_indicators["price_manipulation"]):
            findings.append({
                "type": "price_manipulation_risk",
                "severity": "high",
                "description": "检测到价格相关的用户输入处理，可能存在价格操纵风险",
                "file": file_path,
                "recommendation": "确保所有价格计算在服务端进行，并进行严格验证"
            })
        
        # 检测权限提升风险
        if any(re.search(pattern, code, re.IGNORECASE) for pattern in self.business_logic_indicators["privilege_escalation"]):
            findings.append({
                "type": "privilege_escalation_risk",
                "severity": "critical",
                "description": "检测到权限相关的用户输入处理，可能存在权限提升风险",
                "file": file_path,
                "recommendation": "权限分配必须在服务端严格控制，不能依赖客户端输入"
            })
        
        return findings
