#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端代码分析优化器
智能过滤前端代码，提取关键输入点，避免分析冗长的静态内容
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class InputPoint:
    """前端输入点"""
    type: str  # 'form', 'ajax', 'url_param', 'user_input'
    element: str  # HTML元素或JS代码片段
    name: str  # 输入名称
    method: Optional[str] = None  # GET/POST等
    action: Optional[str] = None  # 提交地址
    validation: Optional[str] = None  # 前端验证
    line_number: Optional[int] = None

@dataclass
class SecurityHotspot:
    """安全热点"""
    type: str  # 'XSS_RISK', 'SENSITIVE_INFO', 'UNSAFE_EVAL'
    pattern: str  # 匹配的模式
    code_snippet: str  # 代码片段
    severity: str  # 'high', 'medium', 'low'
    line_number: int
    description: str

@dataclass
class FrontendAnalysisResult:
    """前端分析结果"""
    should_skip: bool
    skip_reason: Optional[str] = None
    analysis_type: Optional[str] = None  # 'full', 'hotspot', 'input_extraction', 'light'
    input_points: List[InputPoint] = None
    security_hotspots: List[SecurityHotspot] = None
    backend_mapping_needed: bool = False
    estimated_time_saved: float = 0.0  # 节省的分析时间（秒）

class FrontendOptimizer:
    """前端代码分析优化器"""
    
    def __init__(self):
        # 静态内容指示符
        self.static_indicators = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<title>',
            '<meta',
            '<link',
            '<style>',
            'text-align:',
            'font-size:',
            'color:',
            'background:'
        ]
        
        # 动态内容指示符
        self.dynamic_indicators = [
            '<script',
            'javascript:',
            'onclick=',
            'onload=',
            'onsubmit=',
            '<form',
            '<input',
            '<textarea',
            '<select',
            'ajax',
            'fetch(',
            'XMLHttpRequest',
            '$.post',
            '$.get',
            'axios.',
            'document.cookie',
            'localStorage',
            'sessionStorage'
        ]
        
        # 安全敏感模式
        self.security_patterns = {
            'XSS_RISK': [
                r'innerHTML\s*=\s*[^;]+[\'"][^\'";]*\+',  # innerHTML with concatenation
                r'outerHTML\s*=\s*[^;]+[\'"][^\'";]*\+',  # outerHTML with concatenation
                r'document\.write\s*\([^)]*\+',           # document.write with concatenation
                r'eval\s*\([^)]*[\'"][^\'";]*\+',         # eval with concatenation
                r'setTimeout\s*\(\s*[\'"][^\'";]*\+',     # setTimeout with string concatenation
                r'setInterval\s*\(\s*[\'"][^\'";]*\+'     # setInterval with string concatenation
            ],
            'SENSITIVE_INFO': [
                r'password\s*[:=]\s*[\'"][^\'"]{6,}[\'"]',     # hardcoded passwords
                r'api[_-]?key\s*[:=]\s*[\'"][^\'"]{10,}[\'"]', # API keys
                r'token\s*[:=]\s*[\'"][^\'"]{20,}[\'"]',       # tokens
                r'secret\s*[:=]\s*[\'"][^\'"]{8,}[\'"]',       # secrets
                r'jdbc:[^\'";]+password[=:][^\'";]+',          # database passwords
            ],
            'UNSAFE_EVAL': [
                r'eval\s*\(',
                r'Function\s*\(',
                r'setTimeout\s*\(\s*[\'"][^\'";]*[\'"]',
                r'setInterval\s*\(\s*[\'"][^\'";]*[\'"]'
            ],
            'DOM_XSS': [
                r'location\.hash',
                r'location\.search',
                r'document\.referrer',
                r'window\.name',
                r'document\.URL'
            ]
        }
    
    def analyze_frontend_file(self, file_path: str, content: str) -> FrontendAnalysisResult:
        """分析前端文件，决定处理策略"""
        
        # 1. 快速预检 - 判断是否为纯静态内容
        if self._is_pure_static_content(content):
            return FrontendAnalysisResult(
                should_skip=True,
                skip_reason="纯静态内容，无安全风险",
                estimated_time_saved=self._estimate_analysis_time(content)
            )
        
        # 2. 检测安全热点
        security_hotspots = self._detect_security_hotspots(content)
        
        # 3. 提取输入点
        input_points = self._extract_input_points(content)
        
        # 4. 决定分析策略
        if security_hotspots:
            # 有安全热点，需要重点分析
            return FrontendAnalysisResult(
                should_skip=False,
                analysis_type='hotspot',
                security_hotspots=security_hotspots,
                input_points=input_points,
                backend_mapping_needed=bool(input_points)
            )
        elif input_points:
            # 有输入点，提取后与后端关联
            return FrontendAnalysisResult(
                should_skip=False,
                analysis_type='input_extraction',
                input_points=input_points,
                backend_mapping_needed=True,
                estimated_time_saved=self._estimate_analysis_time(content) * 0.7  # 节省70%时间
            )
        elif self._has_minimal_security_risk(content):
            # 轻量安全检查
            return FrontendAnalysisResult(
                should_skip=False,
                analysis_type='light',
                estimated_time_saved=self._estimate_analysis_time(content) * 0.5  # 节省50%时间
            )
        else:
            # 跳过分析
            return FrontendAnalysisResult(
                should_skip=True,
                skip_reason="无明显安全风险的静态页面",
                estimated_time_saved=self._estimate_analysis_time(content)
            )
    
    def _is_pure_static_content(self, content: str) -> bool:
        """判断是否为纯静态内容"""
        content_lower = content.lower()
        
        # 计算静态内容比例
        static_count = sum(1 for indicator in self.static_indicators if indicator in content_lower)
        dynamic_count = sum(1 for indicator in self.dynamic_indicators if indicator in content_lower)
        
        # 如果没有动态内容，或静态内容占绝对优势
        if dynamic_count == 0:
            return True
        
        # 静态内容比例超过80%且动态内容很少
        if static_count > 0 and static_count / (static_count + dynamic_count) > 0.8 and dynamic_count < 3:
            return True
        
        # 检查文件大小和动态内容密度
        if len(content) > 5000 and dynamic_count < 5:  # 大文件但动态内容很少
            return True
        
        return False
    
    def _detect_security_hotspots(self, content: str) -> List[SecurityHotspot]:
        """检测安全热点"""
        hotspots = []
        lines = content.split('\n')
        
        for hotspot_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        hotspots.append(SecurityHotspot(
                            type=hotspot_type,
                            pattern=pattern,
                            code_snippet=line.strip(),
                            severity=self._get_severity(hotspot_type),
                            line_number=line_num,
                            description=self._get_hotspot_description(hotspot_type)
                        ))
        
        return hotspots
    
    def _extract_input_points(self, content: str) -> List[InputPoint]:
        """提取前端输入点"""
        input_points = []
        lines = content.split('\n')
        
        # 1. 提取表单
        form_inputs = self._extract_form_inputs(content, lines)
        input_points.extend(form_inputs)
        
        # 2. 提取AJAX请求
        ajax_inputs = self._extract_ajax_inputs(content, lines)
        input_points.extend(ajax_inputs)
        
        # 3. 提取URL参数
        url_params = self._extract_url_parameters(content, lines)
        input_points.extend(url_params)
        
        return input_points
    
    def _extract_form_inputs(self, content: str, lines: List[str]) -> List[InputPoint]:
        """提取表单输入"""
        inputs = []
        
        # 查找表单
        form_pattern = r'<form[^>]*action\s*=\s*[\'"]([^\'"]*)[\'"][^>]*method\s*=\s*[\'"]([^\'"]*)[\'"][^>]*>'
        forms = re.finditer(form_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for form in forms:
            action = form.group(1)
            method = form.group(2)
            
            # 在表单内查找输入字段
            form_start = form.end()
            form_end = content.find('</form>', form_start)
            if form_end == -1:
                form_end = len(content)
            
            form_content = content[form_start:form_end]
            
            # 查找输入字段
            input_pattern = r'<input[^>]*name\s*=\s*[\'"]([^\'"]*)[\'"][^>]*>'
            input_fields = re.finditer(input_pattern, form_content, re.IGNORECASE)
            
            for field in input_fields:
                inputs.append(InputPoint(
                    type='form',
                    element=field.group(0),
                    name=field.group(1),
                    method=method,
                    action=action,
                    line_number=self._find_line_number(content, form.start(), lines)
                ))
        
        return inputs
    
    def _extract_ajax_inputs(self, content: str, lines: List[str]) -> List[InputPoint]:
        """提取AJAX请求"""
        inputs = []
        
        # AJAX模式
        ajax_patterns = [
            r'\$\.post\s*\(\s*[\'"]([^\'"]*)[\'"]',
            r'\$\.get\s*\(\s*[\'"]([^\'"]*)[\'"]',
            r'fetch\s*\(\s*[\'"]([^\'"]*)[\'"]',
            r'axios\.post\s*\(\s*[\'"]([^\'"]*)[\'"]',
            r'XMLHttpRequest.*open\s*\(\s*[\'"]([^\'"]*)[\'"]\s*,\s*[\'"]([^\'"]*)[\'"]'
        ]
        
        for pattern in ajax_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                inputs.append(InputPoint(
                    type='ajax',
                    element=match.group(0),
                    name='ajax_request',
                    action=match.group(1) if match.groups() else None,
                    line_number=self._find_line_number(content, match.start(), lines)
                ))
        
        return inputs
    
    def _extract_url_parameters(self, content: str, lines: List[str]) -> List[InputPoint]:
        """提取URL参数"""
        inputs = []
        
        # URL参数模式
        url_param_patterns = [
            r'location\.search',
            r'location\.hash',
            r'window\.location\.href',
            r'getParameter\s*\(\s*[\'"]([^\'"]*)[\'"]',
            r'URLSearchParams'
        ]
        
        for pattern in url_param_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                inputs.append(InputPoint(
                    type='url_param',
                    element=match.group(0),
                    name=match.group(1) if match.groups() else 'url_parameter',
                    line_number=self._find_line_number(content, match.start(), lines)
                ))
        
        return inputs
    
    def _has_minimal_security_risk(self, content: str) -> bool:
        """检查是否有最小安全风险"""
        # 检查是否包含基本的用户交互
        minimal_risk_indicators = [
            'onclick=',
            'onchange=',
            'onsubmit=',
            'addEventListener',
            'document.getElementById',
            'document.querySelector'
        ]
        
        return any(indicator in content for indicator in minimal_risk_indicators)
    
    def _get_severity(self, hotspot_type: str) -> str:
        """获取安全热点严重程度"""
        severity_map = {
            'XSS_RISK': 'high',
            'SENSITIVE_INFO': 'high',
            'UNSAFE_EVAL': 'high',
            'DOM_XSS': 'medium'
        }
        return severity_map.get(hotspot_type, 'low')
    
    def _get_hotspot_description(self, hotspot_type: str) -> str:
        """获取安全热点描述"""
        descriptions = {
            'XSS_RISK': '潜在的XSS跨站脚本攻击风险',
            'SENSITIVE_INFO': '硬编码敏感信息泄露',
            'UNSAFE_EVAL': '不安全的代码执行',
            'DOM_XSS': '基于DOM的XSS攻击风险'
        }
        return descriptions.get(hotspot_type, '未知安全风险')
    
    def _find_line_number(self, content: str, position: int, lines: List[str]) -> int:
        """根据字符位置查找行号"""
        current_pos = 0
        for line_num, line in enumerate(lines, 1):
            if current_pos + len(line) >= position:
                return line_num
            current_pos += len(line) + 1  # +1 for newline
        return len(lines)
    
    def _estimate_analysis_time(self, content: str) -> float:
        """估算分析时间（秒）"""
        # 基于内容长度估算，平均每1000字符需要1秒
        base_time = len(content) / 1000
        return max(1.0, base_time)
    
    def generate_optimized_prompt(self, analysis_result: FrontendAnalysisResult, content: str) -> str:
        """生成优化的分析提示词"""
        if analysis_result.analysis_type == 'hotspot':
            return self._generate_hotspot_prompt(analysis_result.security_hotspots, content)
        elif analysis_result.analysis_type == 'input_extraction':
            return self._generate_input_extraction_prompt(analysis_result.input_points)
        elif analysis_result.analysis_type == 'light':
            return self._generate_light_analysis_prompt()
        else:
            return ""
    
    def _generate_hotspot_prompt(self, hotspots: List[SecurityHotspot], content: str) -> str:
        """生成安全热点分析提示词"""
        hotspot_info = []
        for hotspot in hotspots:
            hotspot_info.append(f"- 第{hotspot.line_number}行: {hotspot.description}")
        
        return f"""
请重点分析以下检测到的安全热点：

{chr(10).join(hotspot_info)}

请仔细检查这些代码片段是否存在真实的安全风险，并提供具体的修复建议。
忽略纯静态内容，专注于动态代码的安全性。
"""
    
    def _generate_input_extraction_prompt(self, input_points: List[InputPoint]) -> str:
        """生成输入点提取提示词"""
        input_info = []
        for input_point in input_points:
            input_info.append(f"- {input_point.type}: {input_point.name} (第{input_point.line_number}行)")
        
        return f"""
检测到以下前端输入点：

{chr(10).join(input_info)}

请分析这些输入点的安全风险，特别关注：
1. 输入验证是否充分
2. 是否存在客户端绕过风险
3. 与后端接口的安全对接
4. XSS和注入攻击的防护

重点分析输入处理逻辑，忽略页面布局和样式代码。
"""
    
    def _generate_light_analysis_prompt(self) -> str:
        """生成轻量分析提示词"""
        return """
请进行轻量级安全检查，重点关注：
1. 明显的安全漏洞（XSS、敏感信息泄露等）
2. 不安全的JavaScript代码执行
3. 客户端存储的敏感数据

忽略纯展示性内容和样式代码，只报告确实存在的安全问题。
"""
