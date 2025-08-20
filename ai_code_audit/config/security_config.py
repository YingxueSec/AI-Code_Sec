#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全规则配置加载器
用于加载和管理不同语言和框架的安全检查规则
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class FrameworkInfo:
    """框架信息"""
    name: str
    safe_patterns: List[str]
    dangerous_patterns: List[str]
    rules: str
    detection_patterns: List[str]

@dataclass
class LanguageInfo:
    """语言信息"""
    checks: List[str]

@dataclass
class ArchitectureLayerInfo:
    """架构层次信息"""
    name: str
    responsibilities: List[str]
    security_focus: List[str]
    notes: Optional[str] = None

class SecurityRulesConfig:
    """安全规则配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "security_rules.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to load security rules config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'frameworks': {},
            'languages': {
                'java': {'checks': ['SQL注入漏洞', '命令注入漏洞', '路径遍历漏洞']},
                'python': {'checks': ['SQL注入漏洞', '命令注入漏洞', '路径遍历漏洞']},
                'javascript': {'checks': ['XSS攻击', '原型污染', '代码注入']},
                'php': {'checks': ['SQL注入漏洞', '文件包含漏洞', '代码注入']}
            },
            'architecture_layers': {},
            'false_positive_filters': {'confidence_threshold': 0.3}
        }
    
    def get_framework_info(self, framework_name: str) -> Optional[FrameworkInfo]:
        """获取框架信息"""
        framework_config = self.config.get('frameworks', {}).get(framework_name)
        if not framework_config:
            return None
            
        return FrameworkInfo(
            name=framework_config.get('name', framework_name),
            safe_patterns=framework_config.get('safe_patterns', []),
            dangerous_patterns=framework_config.get('dangerous_patterns', []),
            rules=framework_config.get('rules', ''),
            detection_patterns=framework_config.get('detection_patterns', [])
        )
    
    def get_language_info(self, language: str) -> LanguageInfo:
        """获取语言信息"""
        language_config = self.config.get('languages', {}).get(language, {})
        return LanguageInfo(
            checks=language_config.get('checks', [])
        )
    
    def get_architecture_layer_info(self, layer: str) -> Optional[ArchitectureLayerInfo]:
        """获取架构层次信息"""
        layer_config = self.config.get('architecture_layers', {}).get(layer)
        if not layer_config:
            return None
            
        return ArchitectureLayerInfo(
            name=layer_config.get('name', layer),
            responsibilities=layer_config.get('responsibilities', []),
            security_focus=layer_config.get('security_focus', []),
            notes=layer_config.get('notes')
        )
    
    def detect_frameworks(self, code: str, file_path: str) -> Dict[str, bool]:
        """检测代码中使用的框架"""
        detected = {}
        
        for framework_name, framework_config in self.config.get('frameworks', {}).items():
            detected[framework_name] = False
            
            detection_patterns = framework_config.get('detection_patterns', [])
            for pattern in detection_patterns:
                if pattern in code or pattern.lower() in file_path.lower():
                    detected[framework_name] = True
                    break
        
        return detected
    
    def is_safe_pattern(self, code_snippet: str, framework_name: str) -> bool:
        """检查代码片段是否匹配安全模式"""
        framework_info = self.get_framework_info(framework_name)
        if not framework_info:
            return False
            
        for pattern in framework_info.safe_patterns:
            if re.search(pattern, code_snippet):
                return True
        return False
    
    def is_dangerous_pattern(self, code_snippet: str, framework_name: str) -> bool:
        """检查代码片段是否匹配危险模式"""
        framework_info = self.get_framework_info(framework_name)
        if not framework_info:
            return False
            
        for pattern in framework_info.dangerous_patterns:
            if re.search(pattern, code_snippet):
                return True
        return False
    
    def get_framework_rules_text(self, detected_frameworks: Dict[str, bool]) -> str:
        """获取检测到的框架的安全规则文本"""
        rules = []
        
        for framework_name, detected in detected_frameworks.items():
            if detected:
                framework_info = self.get_framework_info(framework_name)
                if framework_info and framework_info.rules:
                    rules.append(framework_info.rules)
        
        return "\n".join(rules)
    
    def get_confidence_threshold(self) -> float:
        """获取置信度阈值"""
        return self.config.get('false_positive_filters', {}).get('confidence_threshold', 0.3)
    
    def is_dao_layer_permission_issue(self, file_path: str, code_snippet: str) -> bool:
        """检查是否为DAO层权限问题误报"""
        filters = self.config.get('false_positive_filters', {})
        permission_filters = filters.get('permission_bypass', {})
        
        # 检查DAO层指示符
        dao_indicators = permission_filters.get('dao_layer_indicators', [])
        if not any(indicator in file_path.lower() for indicator in dao_indicators):
            return False
        
        # 检查DAO方法模式
        dao_methods = permission_filters.get('dao_method_patterns', [])
        return any(method in code_snippet.lower() for method in dao_methods)
    
    def is_safe_sql_pattern(self, code_snippet: str) -> bool:
        """检查是否为安全的SQL模式"""
        filters = self.config.get('false_positive_filters', {})
        sql_filters = filters.get('sql_injection', {})
        safe_patterns = sql_filters.get('safe_patterns', [])
        
        for pattern in safe_patterns:
            if re.search(pattern, code_snippet):
                return True
        return False

# 全局配置实例
_security_config = None

def get_security_config() -> SecurityRulesConfig:
    """获取全局安全配置实例"""
    global _security_config
    if _security_config is None:
        _security_config = SecurityRulesConfig()
    return _security_config

def reload_security_config(config_path: Optional[str] = None):
    """重新加载安全配置"""
    global _security_config
    _security_config = SecurityRulesConfig(config_path)

if __name__ == "__main__":
    # 测试配置加载
    config = get_security_config()
    
    # 测试框架检测
    java_code = """
    @Query("from User u where u.name = ?1")
    public User findByName(String name);
    """
    
    detected = config.detect_frameworks(java_code, "UserDao.java")
    print("检测到的框架:", [name for name, found in detected.items() if found])
    
    # 测试安全模式检查
    if detected.get('spring_data_jpa'):
        is_safe = config.is_safe_pattern("@Query(\"from User u where u.name = ?1\")", 'spring_data_jpa')
        print("是否为安全模式:", is_safe)
