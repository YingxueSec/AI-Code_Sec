#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的审计模板 - 专注于性能和准确性
"""

from typing import Dict, Any
from .base_template import BaseTemplate


class OptimizedSecurityTemplate(BaseTemplate):
    """优化的安全审计模板 - 简洁高效"""
    
    def __init__(self):
        super().__init__()
        self.name = "optimized_security"
        self.description = "优化的安全审计模板，专注于性能和准确性"
        
    @property
    def system_prompt(self) -> str:
        return """你是一个专业的代码安全审计专家。请分析提供的代码，识别安全漏洞。

要求：
1. 只报告真实存在的安全问题
2. 提供准确的行号和代码片段
3. 给出具体的修复建议
4. 按严重程度分类：high/medium/low

重点关注：
- SQL注入、XSS、CSRF
- 命令注入、路径遍历
- 权限绕过、认证缺陷
- 敏感信息泄露
- 业务逻辑漏洞

输出格式（JSON）：
{
  "success": true,
  "findings": [
    {
      "type": "漏洞类型",
      "severity": "high|medium|low",
      "line": 行号,
      "code_snippet": "相关代码",
      "description": "问题描述",
      "recommendation": "修复建议",
      "impact": "安全影响"
    }
  ]
}

如果没有发现问题，返回：{"success": true, "findings": []}"""

    def format_request(self, code: str, file_path: str, language: str, **kwargs) -> str:
        """格式化分析请求"""
        return f"""文件: {file_path}
语言: {language}

代码:
```{language}
{code}
```

请分析上述代码的安全问题。"""


class FastScanTemplate(BaseTemplate):
    """快速扫描模板 - 最小化响应时间"""
    
    def __init__(self):
        super().__init__()
        self.name = "fast_scan"
        self.description = "快速扫描模板，最小化响应时间"
        
    @property
    def system_prompt(self) -> str:
        return """快速安全扫描。只报告高危漏洞：SQL注入、命令注入、XSS、路径遍历、权限绕过。

输出JSON格式：
{
  "success": true,
  "findings": [
    {
      "type": "漏洞类型",
      "severity": "high",
      "line": 行号,
      "code_snippet": "代码片段",
      "description": "简要描述"
    }
  ]
}"""

    def format_request(self, code: str, file_path: str, language: str, **kwargs) -> str:
        """格式化分析请求"""
        # 限制代码长度，提高响应速度
        max_code_length = 2000
        if len(code) > max_code_length:
            code = code[:max_code_length] + "\n... (代码已截断)"
            
        return f"""文件: {file_path}
代码:
```{language}
{code}
```"""


class TargetedScanTemplate(BaseTemplate):
    """针对性扫描模板 - 基于文件类型优化"""
    
    def __init__(self):
        super().__init__()
        self.name = "targeted_scan"
        self.description = "针对性扫描模板，基于文件类型优化"
        
    def get_language_specific_prompt(self, language: str) -> str:
        """获取语言特定的提示词"""
        prompts = {
            "python": "重点检查：SQL注入(sqlite3/mysql)、命令注入(subprocess/os)、路径遍历、pickle反序列化",
            "java": "重点检查：SQL注入(JDBC)、XSS、XXE、反序列化、Spring安全配置",
            "javascript": "重点检查：XSS、原型污染、eval注入、路径遍历、npm包安全",
            "php": "重点检查：SQL注入、文件包含、命令注入、反序列化、上传漏洞",
            "go": "重点检查：SQL注入、命令注入、路径遍历、goroutine竞态条件",
            "c": "重点检查：缓冲区溢出、格式化字符串、内存泄露、整数溢出",
            "cpp": "重点检查：缓冲区溢出、UAF、内存泄露、整数溢出"
        }
        return prompts.get(language.lower(), "通用安全检查")
        
    @property
    def system_prompt(self) -> str:
        return """你是代码安全专家。根据编程语言特点进行针对性安全分析。

输出JSON格式：
{
  "success": true,
  "findings": [
    {
      "type": "漏洞类型",
      "severity": "high|medium|low",
      "line": 行号,
      "code_snippet": "代码片段",
      "description": "问题描述",
      "recommendation": "修复建议"
    }
  ]
}"""

    def format_request(self, code: str, file_path: str, language: str, **kwargs) -> str:
        """格式化分析请求"""
        specific_prompt = self.get_language_specific_prompt(language)
        
        return f"""文件: {file_path}
语言: {language}
检查重点: {specific_prompt}

代码:
```{language}
{code}
```

请进行针对性安全分析。"""


# 模板注册
OPTIMIZED_TEMPLATES = {
    "optimized_security": OptimizedSecurityTemplate(),
    "fast_scan": FastScanTemplate(),
    "targeted_scan": TargetedScanTemplate()
}


def get_optimized_template(name: str) -> BaseTemplate:
    """获取优化模板"""
    return OPTIMIZED_TEMPLATES.get(name)


def list_optimized_templates() -> Dict[str, str]:
    """列出所有优化模板"""
    return {name: template.description for name, template in OPTIMIZED_TEMPLATES.items()}
