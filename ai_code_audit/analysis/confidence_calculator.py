#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能置信度评分系统
基于多个维度计算安全漏洞报告的置信度
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConfidenceFactors:
    """置信度影响因素"""
    framework_protection: float = 1.0
    architecture_appropriateness: float = 1.0
    code_complexity: float = 1.0
    pattern_reliability: float = 1.0
    context_completeness: float = 1.0
    historical_accuracy: float = 1.0

@dataclass
class ConfidenceResult:
    """置信度计算结果"""
    final_score: float
    factors: ConfidenceFactors
    reasoning: List[str]
    risk_level: str

class ConfidenceCalculator:
    """智能置信度计算器"""
    
    def __init__(self):
        # 历史误报率统计 (模拟数据，实际应从数据库获取)
        self.historical_false_positive_rates = {
            'SQL注入': 0.85,  # 85%的SQL注入报告是误报
            '权限验证绕过': 0.75,
            'XSS攻击': 0.60,
            '命令注入': 0.40,
            '路径遍历': 0.50,
            '硬编码密钥': 0.20,
            '弱加密算法': 0.30
        }
        
        # 框架安全保护模式
        self.framework_protections = {
            'spring_data_jpa': {
                'SQL注入': 0.95,  # Spring Data JPA对SQL注入有95%的保护
                '权限验证绕过': 0.0
            },
            'mybatis': {
                'SQL注入': 0.5,  # MyBatis部分保护
            },
            'spring_security': {
                '权限验证绕过': 0.90,
                'CSRF攻击': 0.85
            },
            'django': {
                'SQL注入': 0.90,
                'XSS攻击': 0.80,
                'CSRF攻击': 0.90
            }
        }
        
        # 架构层次职责
        self.layer_responsibilities = {
            'controller': ['权限验证绕过', 'XSS攻击', 'CSRF攻击', '输入验证'],
            'service': ['业务逻辑漏洞', '数据验证'],
            'dao': ['SQL注入'],
            'entity': ['数据验证', '敏感信息泄露']
        }
    
    def calculate_confidence(self, finding: Dict[str, Any], context: Dict[str, Any]) -> ConfidenceResult:
        """
        计算漏洞报告的置信度
        
        Args:
            finding: 漏洞发现信息
            context: 上下文信息 (框架、架构层次、项目信息等)
            
        Returns:
            ConfidenceResult: 置信度计算结果
        """
        factors = ConfidenceFactors()
        reasoning = []
        
        # 1. 框架保护检查
        framework_factor, framework_reasoning = self._check_framework_protection(finding, context)
        factors.framework_protection = framework_factor
        reasoning.extend(framework_reasoning)
        
        # 2. 架构适当性检查
        arch_factor, arch_reasoning = self._check_architecture_appropriateness(finding, context)
        factors.architecture_appropriateness = arch_factor
        reasoning.extend(arch_reasoning)
        
        # 3. 代码复杂度检查
        complexity_factor, complexity_reasoning = self._check_code_complexity(finding, context)
        factors.code_complexity = complexity_factor
        reasoning.extend(complexity_reasoning)
        
        # 4. 模式可靠性检查
        pattern_factor, pattern_reasoning = self._check_pattern_reliability(finding, context)
        factors.pattern_reliability = pattern_factor
        reasoning.extend(pattern_reasoning)
        
        # 5. 上下文完整性检查
        context_factor, context_reasoning = self._check_context_completeness(finding, context)
        factors.context_completeness = context_factor
        reasoning.extend(context_reasoning)
        
        # 6. 历史准确性检查
        historical_factor, historical_reasoning = self._check_historical_accuracy(finding, context)
        factors.historical_accuracy = historical_factor
        reasoning.extend(historical_reasoning)
        
        # 计算最终置信度
        final_score = self._calculate_final_score(factors)
        risk_level = self._determine_risk_level(final_score)
        
        return ConfidenceResult(
            final_score=final_score,
            factors=factors,
            reasoning=reasoning,
            risk_level=risk_level
        )
    
    def _check_framework_protection(self, finding: Dict, context: Dict) -> tuple[float, List[str]]:
        """检查框架保护因素"""
        factor = 1.0
        reasoning = []
        
        finding_type = finding.get('type', '')
        detected_frameworks = context.get('frameworks', {})
        
        for framework, detected in detected_frameworks.items():
            if detected and framework in self.framework_protections:
                protection_rate = self.framework_protections[framework].get(finding_type, 0)
                if protection_rate > 0:
                    factor *= (1 - protection_rate)
                    reasoning.append(f"框架{framework}对{finding_type}提供{protection_rate*100:.0f}%保护，降低置信度")
        
        return factor, reasoning
    
    def _check_architecture_appropriateness(self, finding: Dict, context: Dict) -> tuple[float, List[str]]:
        """检查架构适当性"""
        factor = 1.0
        reasoning = []
        
        finding_type = finding.get('type', '')
        file_path = context.get('file_path', '')
        architecture_layer = context.get('architecture_layer', 'unknown')
        
        # 检查问题类型是否适合当前架构层
        if architecture_layer in self.layer_responsibilities:
            appropriate_issues = self.layer_responsibilities[architecture_layer]
            
            if finding_type not in appropriate_issues:
                # 检查特殊情况
                if architecture_layer == 'dao' and '权限' in finding_type:
                    factor *= 0.2  # DAO层不应该负责权限验证
                    reasoning.append(f"DAO层不应该负责权限验证，这是Controller/Service层的职责")
                elif architecture_layer == 'entity' and 'SQL注入' in finding_type:
                    factor *= 0.3  # 实体层通常不直接处理SQL
                    reasoning.append(f"实体层通常不直接处理SQL查询")
        
        return factor, reasoning
    
    def _check_code_complexity(self, finding: Dict, context: Dict) -> tuple[float, List[str]]:
        """检查代码复杂度"""
        factor = 1.0
        reasoning = []
        
        code_snippet = finding.get('code_snippet', '')
        
        # 代码行数
        line_count = len(code_snippet.split('\n'))
        if line_count < 3:
            factor *= 0.8
            reasoning.append(f"代码片段过短({line_count}行)，可能缺乏足够上下文")
        
        # 代码复杂度指标
        complexity_indicators = [
            ('if', 0.1), ('for', 0.1), ('while', 0.1), 
            ('try', 0.1), ('catch', 0.1), ('switch', 0.1)
        ]
        
        complexity_score = 0
        for indicator, weight in complexity_indicators:
            complexity_score += code_snippet.count(indicator) * weight
        
        if complexity_score < 0.2:
            factor *= 0.9
            reasoning.append("代码复杂度较低，可能是简单的框架调用")
        
        return factor, reasoning
    
    def _check_pattern_reliability(self, finding: Dict, context: Dict) -> tuple[float, List[str]]:
        """检查模式可靠性"""
        factor = 1.0
        reasoning = []
        
        code_snippet = finding.get('code_snippet', '')
        finding_type = finding.get('type', '')
        
        # 检查已知的安全模式
        safe_patterns = {
            'SQL注入': [
                r'@Query.*\?\d+',  # JPA占位符
                r'@Query.*:\w+',   # JPA命名参数
                r'#\{[^}]+\}',     # MyBatis安全参数
                r'\.objects\.',    # Django ORM
                r'findBy\w+Like'   # JPA命名查询
            ],
            '权限验证绕过': [
                r'@PreAuthorize',
                r'@Secured',
                r'SecurityContext',
                r'@login_required'
            ]
        }
        
        if finding_type in safe_patterns:
            for pattern in safe_patterns[finding_type]:
                if re.search(pattern, code_snippet):
                    factor *= 0.2
                    reasoning.append(f"检测到安全模式: {pattern}")
                    break
        
        # 检查危险模式
        dangerous_patterns = {
            'SQL注入': [
                r'\$\{[^}]+\}',    # MyBatis危险参数
                r'String.*\+.*sql', # 字符串拼接SQL
                r'execute\s*\(\s*["\'].*\+' # 动态SQL执行
            ]
        }
        
        if finding_type in dangerous_patterns:
            for pattern in dangerous_patterns[finding_type]:
                if re.search(pattern, code_snippet):
                    factor *= 1.5  # 增加置信度
                    reasoning.append(f"检测到危险模式: {pattern}")
                    break
        
        return factor, reasoning
    
    def _check_context_completeness(self, finding: Dict, context: Dict) -> tuple[float, List[str]]:
        """检查上下文完整性"""
        factor = 1.0
        reasoning = []
        
        # 检查是否有调用链信息
        if not context.get('call_chain'):
            factor *= 0.9
            reasoning.append("缺少调用链信息，无法完整分析数据流")
        
        # 检查是否有项目技术栈信息
        if not context.get('tech_stack'):
            factor *= 0.9
            reasoning.append("缺少项目技术栈信息")
        
        # 检查是否有安全配置信息
        if not context.get('security_config'):
            factor *= 0.95
            reasoning.append("缺少安全配置信息")
        
        return factor, reasoning
    
    def _check_historical_accuracy(self, finding: Dict, context: Dict) -> tuple[float, List[str]]:
        """检查历史准确性"""
        factor = 1.0
        reasoning = []
        
        finding_type = finding.get('type', '')
        
        # 基于历史误报率调整
        if finding_type in self.historical_false_positive_rates:
            false_positive_rate = self.historical_false_positive_rates[finding_type]
            factor *= (1 - false_positive_rate * 0.5)  # 不完全依赖历史数据
            reasoning.append(f"{finding_type}历史误报率{false_positive_rate*100:.0f}%，调整置信度")
        
        return factor, reasoning
    
    def _calculate_final_score(self, factors: ConfidenceFactors) -> float:
        """计算最终置信度分数"""
        # 加权平均
        weights = {
            'framework_protection': 0.25,
            'architecture_appropriateness': 0.20,
            'code_complexity': 0.15,
            'pattern_reliability': 0.20,
            'context_completeness': 0.10,
            'historical_accuracy': 0.10
        }
        
        score = (
            factors.framework_protection * weights['framework_protection'] +
            factors.architecture_appropriateness * weights['architecture_appropriateness'] +
            factors.code_complexity * weights['code_complexity'] +
            factors.pattern_reliability * weights['pattern_reliability'] +
            factors.context_completeness * weights['context_completeness'] +
            factors.historical_accuracy * weights['historical_accuracy']
        )
        
        # 确保分数在0.1-1.0范围内
        return max(0.1, min(1.0, score))
    
    def _determine_risk_level(self, score: float) -> str:
        """确定风险等级"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'very_low'
    
    def update_historical_data(self, finding_type: str, was_false_positive: bool):
        """更新历史数据"""
        if finding_type not in self.historical_false_positive_rates:
            self.historical_false_positive_rates[finding_type] = 0.5
        
        # 简单的移动平均更新
        current_rate = self.historical_false_positive_rates[finding_type]
        if was_false_positive:
            new_rate = current_rate * 0.9 + 0.1  # 增加误报率
        else:
            new_rate = current_rate * 0.9  # 降低误报率
        
        self.historical_false_positive_rates[finding_type] = max(0.1, min(0.9, new_rate))
