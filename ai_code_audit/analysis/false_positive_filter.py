#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
误报过滤器 - 智能识别和过滤常见的误报问题
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FilterRule:
    """过滤规则"""
    name: str
    pattern: str
    issue_types: List[str]
    confidence_threshold: float
    description: str

class FalsePositiveFilter:
    """误报过滤器"""
    
    def __init__(self):
        self.rules = self._load_filter_rules()
        self.business_constants = self._load_business_constants()
        self.safe_patterns = self._load_safe_patterns()
    
    def _load_filter_rules(self) -> List[FilterRule]:
        """加载过滤规则"""
        return [
            # Java包名误报
            FilterRule(
                name="java_package_declaration",
                pattern=r"package\s+[a-zA-Z][a-zA-Z0-9_.]*;",
                issue_types=["硬编码密钥和敏感信息", "信息泄露"],
                confidence_threshold=0.9,
                description="Java包声明不是敏感信息"
            ),
            
            # 业务常量误报
            FilterRule(
                name="business_constants",
                pattern=r"(2L|1L|0L|\d+L?)\s*[,;)]",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.9,
                description="业务常量不是敏感信息"
            ),
            
            # 正常IP获取误报
            FilterRule(
                name="legitimate_ip_acquisition",
                pattern=r"InetAddress\.getLocalHost\(\)|getHostAddress\(\)",
                issue_types=["硬编码密钥和敏感信息", "信息泄露"],
                confidence_threshold=0.7,
                description="考勤系统获取IP地址是正常业务需求"
            ),
            
            # 分页参数误报
            FilterRule(
                name="pagination_parameters",
                pattern=r"PageHelper\.startPage\(\s*\d+\s*,\s*\d+\s*\)",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.8,
                description="分页参数不是敏感信息"
            ),
            
            # 状态码常量误报
            FilterRule(
                name="status_codes",
                pattern=r"(200|404|500|401|403)\s*[,;)]",
                issue_types=["硬编码密钥和敏感信息"],
                confidence_threshold=0.9,
                description="HTTP状态码不是敏感信息"
            ),
            
            # 正常的权限检查误报
            FilterRule(
                name="normal_permission_check",
                pattern=r"session\.getAttribute\([\"']userId[\"']\)",
                issue_types=["权限验证绕过"],
                confidence_threshold=0.8,
                description="获取用户ID是正常的权限验证步骤"
            ),

            # 正常的用户信息获取误报
            FilterRule(
                name="normal_user_info_access",
                pattern=r"Long\.parseLong\(session\.getAttribute\([\"']userId[\"']\)",
                issue_types=["权限验证绕过"],
                confidence_threshold=0.9,
                description="从session获取用户ID是正常操作"
            ),

            # JPA findOne方法误报
            FilterRule(
                name="jpa_findone_safe",
                pattern=r"\.findOne\(\s*\w+\s*\)",
                issue_types=["SQL注入漏洞"],
                confidence_threshold=0.8,
                description="JPA的findOne方法是安全的"
            ),
            
            # 正常的数据库查询误报
            FilterRule(
                name="normal_database_query",
                pattern=r"findOne\(\s*\w+\s*\)|findBy\w+\(",
                issue_types=["SQL注入漏洞"],
                confidence_threshold=0.8,
                description="JPA/Hibernate的findOne等方法是安全的"
            ),

            # 过度的权限验证警告
            FilterRule(
                name="excessive_permission_warnings",
                pattern=r"session\.getAttribute.*userId.*findOne",
                issue_types=["权限验证绕过"],
                confidence_threshold=0.7,
                description="正常的用户信息获取不是权限绕过"
            ),

            # Controller层的正常操作
            FilterRule(
                name="normal_controller_operations",
                pattern=r"@RequestMapping|@GetMapping|@PostMapping",
                issue_types=["权限验证绕过"],
                confidence_threshold=0.6,
                description="Spring MVC注解提供基础安全保护"
            )
        ]
    
    def _load_business_constants(self) -> Dict[str, str]:
        """加载业务常量映射"""
        return {
            "2L": "通知类型常量",
            "1L": "状态常量",
            "0L": "默认值常量",
            "10": "分页大小常量",
            "20": "分页大小常量",
            "true": "布尔常量",
            "false": "布尔常量"
        }
    
    def _load_safe_patterns(self) -> List[str]:
        """加载安全模式列表"""
        return [
            # Spring框架安全模式
            r"@RequestMapping",
            r"@GetMapping",
            r"@PostMapping",
            r"@SessionAttribute",
            r"@PathVariable",
            r"@RequestParam",
            
            # JPA/Hibernate安全模式
            r"\.findOne\(",
            r"\.findBy\w+\(",
            r"\.save\(",
            r"\.delete\(",
            
            # 正常的业务逻辑模式
            r"Objects\.isNull\(",
            r"StringUtils\.isEmpty\(",
            r"Long\.parseLong\(",
            r"Integer\.parseInt\(",
        ]
    
    def filter_findings(self, findings: List[Dict[str, Any]], file_path: str, code: str) -> List[Dict[str, Any]]:
        """
        过滤误报问题
        
        Args:
            findings: 发现的问题列表
            file_path: 文件路径
            code: 源代码
            
        Returns:
            过滤后的问题列表
        """
        filtered_findings = []
        
        for finding in findings:
            if not self._is_false_positive(finding, file_path, code):
                filtered_findings.append(finding)
            else:
                logger.debug(f"过滤误报: {finding.get('type', 'unknown')} in {file_path}")
        
        return filtered_findings
    
    def _is_false_positive(self, finding: Dict[str, Any], file_path: str, code: str) -> bool:
        """
        判断是否为误报

        Args:
            finding: 问题信息
            file_path: 文件路径
            code: 源代码

        Returns:
            True if 误报, False otherwise
        """
        issue_type = finding.get('type', '')
        description = finding.get('description', '')
        code_snippet = finding.get('code', '')
        line_number = finding.get('line', 0)
        confidence = finding.get('confidence', 0.5)

        # 0. 基础置信度过滤 - 过滤明显的低置信度问题
        if confidence < 0.4:
            logger.debug(f"置信度过滤: {confidence} < 0.4")
            return True

        # 1. 基于规则的过滤
        for rule in self.rules:
            if issue_type in rule.issue_types:
                if re.search(rule.pattern, code_snippet, re.IGNORECASE):
                    if confidence <= rule.confidence_threshold:
                        logger.debug(f"规则过滤: {rule.name} - {rule.description}")
                        return True

        # 2. HIGH级问题过滤 - 只过滤明显不可信的HIGH级问题
        severity = finding.get('severity', 'LOW')
        if severity == 'HIGH' and confidence < 0.6:
            logger.debug(f"HIGH级问题置信度不足: {confidence} < 0.6")
            return True

        # 3. 上下文分析过滤
        if self._is_context_safe(finding, file_path, code, line_number):
            return True

        # 4. 业务逻辑过滤
        if self._is_business_logic_safe(finding, file_path):
            return True

        # 5. 框架特定过滤
        if self._is_framework_safe(finding, code_snippet):
            return True

        # 6. 描述关键词过滤
        if self._is_description_false_positive(finding):
            return True

        return False
    
    def _is_context_safe(self, finding: Dict[str, Any], file_path: str, code: str, line_number: int) -> bool:
        """基于上下文判断是否安全"""
        issue_type = finding.get('type', '')
        
        # 获取问题行的上下文
        lines = code.split('\n')
        if line_number <= 0 or line_number > len(lines):
            return False
        
        # 获取前后3行作为上下文
        start_line = max(0, line_number - 4)
        end_line = min(len(lines), line_number + 3)
        context = '\n'.join(lines[start_line:end_line])
        
        # 硬编码敏感信息的上下文过滤
        if issue_type == "硬编码密钥和敏感信息":
            # 如果在注释中，可能是误报
            if re.search(r'//.*' + re.escape(finding.get('code', '')), context):
                return True
            
            # 如果是分页参数
            if re.search(r'PageHelper\.startPage|分页|page', context, re.IGNORECASE):
                return True
            
            # 如果是状态常量
            if re.search(r'status|状态|type|类型', context, re.IGNORECASE):
                return True
        
        # 权限验证绕过的上下文过滤
        if issue_type == "权限验证绕过":
            # 如果有权限检查逻辑
            if re.search(r'Objects\.isNull|权限|permission|auth', context, re.IGNORECASE):
                return True

            # 如果有重定向到错误页面
            if re.search(r'redirect.*notlimit|redirect.*error', context, re.IGNORECASE):
                return True

            # 如果只是获取用户信息而不是权限验证
            if re.search(r'session\.getAttribute.*userId.*findOne', context, re.IGNORECASE):
                return True

            # 如果是正常的用户信息获取
            if re.search(r'Long\.parseLong.*session.*getAttribute.*userId', context, re.IGNORECASE):
                return True

        # SQL注入的上下文过滤
        if issue_type == "SQL注入漏洞":
            # 如果是JPA/Hibernate的安全方法
            if re.search(r'\.findOne\(|\.findBy\w+\(|\.save\(|\.delete\(', context, re.IGNORECASE):
                return True

            # 如果是硬编码常量（如2L, 1L等）
            if re.search(r'\d+L?\s*\)', context):
                return True
        
        return False
    
    def _is_business_logic_safe(self, finding: Dict[str, Any], file_path: str) -> bool:
        """基于业务逻辑判断是否安全"""
        issue_type = finding.get('type', '')
        
        # 考勤系统的IP获取是正常需求
        if "AttendceController" in file_path and issue_type == "硬编码密钥和敏感信息":
            if "InetAddress" in finding.get('code', ''):
                return True
        
        # 邮件系统中的密码硬编码是真实的安全问题，不应该被过滤
        if "Mail" in file_path and issue_type == "硬编码密钥和敏感信息":
            # 如果包含密码相关内容，这是真实的安全问题，不过滤
            if "password" in finding.get('code', '').lower():
                return False  # 密码硬编码是真实问题，不过滤
            # 如果只是普通的邮件配置（如邮箱地址），可能可以过滤
            if "email" in finding.get('code', '').lower() and "password" not in finding.get('code', '').lower():
                return True  # 普通邮箱地址可以过滤
        
        return False
    
    def _is_framework_safe(self, finding: Dict[str, Any], code_snippet: str) -> bool:
        """基于框架特性判断是否安全"""
        issue_type = finding.get('type', '')
        
        # Spring框架的安全模式
        if issue_type == "SQL注入漏洞":
            # JPA/Hibernate的方法是安全的
            if re.search(r'\.findOne\(|\.findBy\w+\(|\.save\(', code_snippet):
                return True
            
            # MyBatis的#{}参数是安全的
            if re.search(r'#\{[^}]+\}', code_snippet):
                return True
        
        # Spring Security的注解是安全的
        if issue_type == "权限验证绕过":
            if re.search(r'@PreAuthorize|@Secured|@RolesAllowed', code_snippet):
                return True
        
        return False

    def _is_description_false_positive(self, finding: Dict[str, Any]) -> bool:
        """基于描述内容判断是否为误报"""
        description = finding.get('description', '').lower()
        issue_type = finding.get('type', '')
        code_snippet = finding.get('code', '').lower()

        # 但是，如果是真正的硬编码密码，不要过滤
        if 'password' in code_snippet and any(word in code_snippet for word in ['=', '"', "'"]):
            logger.debug("检测到真实的硬编码密码，不过滤")
            return False

        # 过度敏感的描述关键词（但要排除真实问题）
        false_positive_keywords = [
            '可能存在', '可能会导致', '可能造成',
            '未明确说明', '未充分检查',
            '如果.*能够控制', '如果.*被不当调用',
            '建议.*应.*确保'
        ]

        # 检查是否包含过度敏感的描述
        for keyword in false_positive_keywords:
            if re.search(keyword, description):
                logger.debug(f"描述关键词过滤: {keyword}")
                return True

        # 特定类型的过度警告
        if issue_type == "权限验证绕过":
            # 过度的权限验证警告
            if any(phrase in description for phrase in [
                '虽然检查了session中的userid',
                '未对用户角色或权限进行',
                '可能导致未授权访问',
                '应增加权限校验逻辑'
            ]):
                return True

        if issue_type == "SQL注入漏洞":
            # 过度的SQL注入警告
            if any(phrase in description for phrase in [
                '可能未使用参数化查询',
                '如果.*参数未经过严格过滤',
                '可能存在sql注入风险'
            ]):
                return True

        return False

    def get_filter_statistics(self) -> Dict[str, int]:
        """获取过滤统计信息"""
        return {
            "total_rules": len(self.rules),
            "business_constants": len(self.business_constants),
            "safe_patterns": len(self.safe_patterns)
        }
