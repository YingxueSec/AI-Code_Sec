#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用误报过滤器 - 适用于多语言项目的误报过滤
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UniversalFilterRule:
    """通用过滤规则"""
    name: str
    pattern: str
    issue_types: List[str]
    confidence_threshold: float
    description: str
    languages: List[str]  # 适用的语言列表，空列表表示适用于所有语言

class UniversalFalsePositiveFilter:
    """通用误报过滤器 - 适用于多语言项目"""
    
    def __init__(self):
        self.universal_rules = self._load_universal_rules()
        self.language_specific_rules = self._load_language_specific_rules()
    
    def _load_universal_rules(self) -> List[UniversalFilterRule]:
        """加载语言无关的通用过滤规则"""
        return [
            # 通用的业务常量误报
            UniversalFilterRule(
                name="numeric_constants",
                pattern=r"\b\d+[LlFfDd]?\b\s*[,;)\]}]",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.8,
                description="数字常量通常不是敏感信息",
                languages=[]  # 适用于所有语言
            ),
            
            # HTTP状态码常量
            UniversalFilterRule(
                name="http_status_codes",
                pattern=r"\b(200|201|400|401|403|404|500|502|503)\b",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.9,
                description="HTTP状态码不是敏感信息",
                languages=[]
            ),
            
            # 通用的日志输出误报
            UniversalFilterRule(
                name="logging_statements",
                pattern=r"(console\.log|print|println|printf|log\.|logger\.|logging\.)",
                issue_types=["命令注入漏洞", "代码注入漏洞"],
                confidence_threshold=0.7,
                description="日志输出语句通常不是注入点",
                languages=[]
            ),
            
            # 通用的配置常量
            UniversalFilterRule(
                name="configuration_constants",
                pattern=r"(true|false|null|undefined|None|nil)\b",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.9,
                description="布尔值和空值常量不是敏感信息",
                languages=[]
            ),
            
            # 通用的版本号
            UniversalFilterRule(
                name="version_numbers",
                pattern=r"\b\d+\.\d+(\.\d+)?\b",
                issue_types=["硬编码密钥和敏感信息", "信息泄露"],
                confidence_threshold=0.8,
                description="版本号通常不是敏感信息",
                languages=[]
            ),
            
            # 通用的URL路径
            UniversalFilterRule(
                name="url_paths",
                pattern=r"['\"]/([\w/\-]+)['\"]",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.7,
                description="URL路径通常不是敏感信息",
                languages=[]
            )
        ]
    
    def _load_language_specific_rules(self) -> Dict[str, List[UniversalFilterRule]]:
        """加载特定语言的过滤规则"""
        return {
            "java": [
                # Java包名
                UniversalFilterRule(
                    name="java_package_declaration",
                    pattern=r"package\s+[a-zA-Z][a-zA-Z0-9_.]*;",
                    issue_types=["硬编码密钥和敏感信息", "信息泄露"],
                    confidence_threshold=0.9,
                    description="Java包声明不是敏感信息",
                    languages=["java"]
                ),
                
                # Java注解
                UniversalFilterRule(
                    name="java_annotations",
                    pattern=r"@\w+(\([^)]*\))?",
                    issue_types=["硬编码密钥和敏感信息"],
                    confidence_threshold=0.8,
                    description="Java注解通常不是敏感信息",
                    languages=["java"]
                ),
                
                # Spring框架安全模式
                UniversalFilterRule(
                    name="spring_mvc_annotations",
                    pattern=r"@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)",
                    issue_types=["权限验证绕过"],
                    confidence_threshold=0.6,
                    description="Spring MVC注解提供基础路由保护",
                    languages=["java"]
                ),
                
                # JPA安全方法
                UniversalFilterRule(
                    name="jpa_safe_methods",
                    pattern=r"\.(findOne|findBy\w+|save|delete)\s*\(",
                    issue_types=["SQL注入漏洞"],
                    confidence_threshold=0.7,
                    description="JPA方法使用参数化查询，通常是安全的",
                    languages=["java"]
                )
            ],
            
            "python": [
                # Python导入语句
                UniversalFilterRule(
                    name="python_imports",
                    pattern=r"(import\s+\w+|from\s+\w+\s+import)",
                    issue_types=["硬编码密钥和敏感信息", "信息泄露"],
                    confidence_threshold=0.9,
                    description="Python导入语句不是敏感信息",
                    languages=["python"]
                ),
                
                # Django安全模式
                UniversalFilterRule(
                    name="django_safe_patterns",
                    pattern=r"@(login_required|permission_required|csrf_exempt)",
                    issue_types=["权限验证绕过"],
                    confidence_threshold=0.6,
                    description="Django装饰器提供安全保护",
                    languages=["python"]
                )
            ],
            
            "javascript": [
                # JavaScript模块导入
                UniversalFilterRule(
                    name="js_imports",
                    pattern=r"(import\s+.*from|require\s*\()",
                    issue_types=["硬编码密钥和敏感信息"],
                    confidence_threshold=0.8,
                    description="JavaScript导入语句通常不是敏感信息",
                    languages=["javascript", "typescript"]
                ),
                
                # Express.js安全模式
                UniversalFilterRule(
                    name="express_middleware",
                    pattern=r"app\.(use|get|post|put|delete)\s*\(",
                    issue_types=["权限验证绕过"],
                    confidence_threshold=0.5,
                    description="Express.js路由定义通常包含中间件保护",
                    languages=["javascript", "typescript"]
                )
            ],
            
            "csharp": [
                # C# using语句
                UniversalFilterRule(
                    name="csharp_using",
                    pattern=r"using\s+[\w.]+;",
                    issue_types=["硬编码密钥和敏感信息"],
                    confidence_threshold=0.9,
                    description="C# using语句不是敏感信息",
                    languages=["csharp"]
                ),
                
                # ASP.NET安全属性
                UniversalFilterRule(
                    name="aspnet_attributes",
                    pattern=r"\[(Authorize|AllowAnonymous|ValidateAntiForgeryToken)\]",
                    issue_types=["权限验证绕过"],
                    confidence_threshold=0.6,
                    description="ASP.NET安全属性提供保护",
                    languages=["csharp"]
                )
            ]
        }
    
    def filter_findings(self, findings: List[Dict[str, Any]], file_path: str, code: str, language: str = None) -> List[Dict[str, Any]]:
        """
        过滤误报问题
        
        Args:
            findings: 发现的问题列表
            file_path: 文件路径
            code: 源代码
            language: 编程语言
            
        Returns:
            过滤后的问题列表
        """
        if not language:
            language = self._detect_language(file_path)
        
        filtered_findings = []
        
        for finding in findings:
            if not self._is_universal_false_positive(finding, file_path, code, language):
                filtered_findings.append(finding)
            else:
                logger.debug(f"通用过滤器过滤误报: {finding.get('type', 'unknown')} in {file_path}")
        
        return filtered_findings
    
    def _detect_language(self, file_path: str) -> str:
        """根据文件路径检测编程语言"""
        extension = file_path.lower().split('.')[-1]
        
        language_map = {
            'java': 'java',
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'cs': 'csharp',
            'cpp': 'cpp',
            'c': 'c',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust'
        }
        
        return language_map.get(extension, 'unknown')
    
    def _is_universal_false_positive(self, finding: Dict[str, Any], file_path: str, code: str, language: str) -> bool:
        """判断是否为通用误报"""
        issue_type = finding.get('type', '')
        code_snippet = finding.get('code', '')
        confidence = finding.get('confidence', 0.5)
        
        # 1. 应用通用规则
        for rule in self.universal_rules:
            if issue_type in rule.issue_types:
                if re.search(rule.pattern, code_snippet, re.IGNORECASE):
                    if confidence <= rule.confidence_threshold:
                        logger.debug(f"通用规则过滤: {rule.name}")
                        return True
        
        # 2. 应用语言特定规则
        if language in self.language_specific_rules:
            for rule in self.language_specific_rules[language]:
                if issue_type in rule.issue_types:
                    if re.search(rule.pattern, code_snippet, re.IGNORECASE):
                        if confidence <= rule.confidence_threshold:
                            logger.debug(f"语言特定规则过滤: {rule.name}")
                            return True
        
        # 3. 基于置信度的通用过滤
        if confidence < 0.4:
            logger.debug(f"低置信度过滤: {confidence}")
            return True
        
        # 4. 描述关键词过滤
        if self._is_description_false_positive(finding):
            return True
        
        return False
    
    def _is_description_false_positive(self, finding: Dict[str, Any]) -> bool:
        """基于描述判断是否为误报"""
        description = finding.get('description', '').lower()
        
        # 过度敏感的描述关键词
        false_positive_keywords = [
            '可能存在', '可能会导致', '可能造成',
            '虽然.*但', '如果.*能够控制',
            '建议.*应.*确保'
        ]
        
        for keyword in false_positive_keywords:
            if re.search(keyword, description):
                return True
        
        return False
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的编程语言列表"""
        return list(self.language_specific_rules.keys())
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """获取过滤器统计信息"""
        return {
            "universal_rules": len(self.universal_rules),
            "language_specific_rules": {
                lang: len(rules) for lang, rules in self.language_specific_rules.items()
            },
            "supported_languages": self.get_supported_languages()
        }
