#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前后端关联分析器
将前端输入点与后端处理逻辑关联，进行端到端的安全分析
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from .frontend_optimizer import InputPoint

@dataclass
class BackendEndpoint:
    """后端接口端点"""
    path: str  # 接口路径
    method: str  # HTTP方法
    file_path: str  # 文件路径
    handler_method: str  # 处理方法名
    parameters: List[str]  # 参数列表
    validation: List[str]  # 验证逻辑
    line_number: int

@dataclass
class SecurityMapping:
    """安全映射"""
    frontend_input: InputPoint
    backend_endpoint: Optional[BackendEndpoint]
    risk_level: str  # 'high', 'medium', 'low'
    security_gaps: List[str]  # 安全缺口
    recommendations: List[str]  # 修复建议

class FrontendBackendMapper:
    """前后端关联分析器"""
    
    def __init__(self):
        # 后端框架模式
        self.backend_patterns = {
            'spring_mvc': {
                'controller': r'@(RestController|Controller)',
                'mapping': r'@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)\s*\([^)]*[\'"]([^\'"]*)[\'"]',
                'param': r'@RequestParam\s*\([^)]*[\'"]([^\'"]*)[\'"]',
                'validation': r'@(Valid|Validated)',
                'security': r'@(PreAuthorize|Secured|RolesAllowed)'
            },
            'django': {
                'view': r'def\s+(\w+)\s*\([^)]*request',
                'url': r'path\s*\([^)]*[\'"]([^\'"]*)[\'"]',
                'param': r'request\.(GET|POST)\s*\.\s*get\s*\([\'"]([^\'"]*)[\'"]',
                'validation': r'(clean_|is_valid\(\))',
                'security': r'@(login_required|permission_required)'
            },
            'express': {
                'route': r'app\.(get|post|put|delete)\s*\([\'"]([^\'"]*)[\'"]',
                'param': r'req\.(query|body|params)\s*\.\s*(\w+)',
                'validation': r'(validator\.|express-validator)',
                'security': r'(authenticate|authorize)'
            },
            'php': {
                'endpoint': r'\$_(GET|POST)\s*\[\s*[\'"]([^\'"]*)[\'"]',
                'validation': r'(filter_var|preg_match|strlen)',
                'security': r'(session_start|isset\(\$_SESSION)'
            }
        }
    
    def map_frontend_to_backend(
        self, 
        input_points: List[InputPoint], 
        backend_files: List[Dict[str, Any]]
    ) -> List[SecurityMapping]:
        """将前端输入点映射到后端处理逻辑"""
        mappings = []
        
        # 1. 分析后端接口
        backend_endpoints = self._analyze_backend_endpoints(backend_files)
        
        # 2. 为每个前端输入点找到对应的后端处理
        for input_point in input_points:
            backend_endpoint = self._find_matching_backend(input_point, backend_endpoints)
            
            # 3. 分析安全风险
            security_mapping = self._analyze_security_mapping(input_point, backend_endpoint)
            mappings.append(security_mapping)
        
        return mappings
    
    def _analyze_backend_endpoints(self, backend_files: List[Dict[str, Any]]) -> List[BackendEndpoint]:
        """分析后端接口端点"""
        endpoints = []
        
        for file_info in backend_files:
            file_path = file_info.get('path', '')
            language = file_info.get('language', '')
            
            try:
                if Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if language == 'java':
                        endpoints.extend(self._extract_spring_endpoints(file_path, content))
                    elif language == 'python':
                        endpoints.extend(self._extract_django_endpoints(file_path, content))
                    elif language == 'javascript':
                        endpoints.extend(self._extract_express_endpoints(file_path, content))
                    elif language == 'php':
                        endpoints.extend(self._extract_php_endpoints(file_path, content))
                        
            except Exception as e:
                print(f"Warning: Failed to analyze backend file {file_path}: {e}")
        
        return endpoints
    
    def _extract_spring_endpoints(self, file_path: str, content: str) -> List[BackendEndpoint]:
        """提取Spring MVC接口端点"""
        endpoints = []
        lines = content.split('\n')
        
        # 查找控制器类
        if not re.search(self.backend_patterns['spring_mvc']['controller'], content):
            return endpoints
        
        # 查找映射注解
        mapping_pattern = self.backend_patterns['spring_mvc']['mapping']
        param_pattern = self.backend_patterns['spring_mvc']['param']
        validation_pattern = self.backend_patterns['spring_mvc']['validation']
        security_pattern = self.backend_patterns['spring_mvc']['security']
        
        for line_num, line in enumerate(lines, 1):
            mapping_match = re.search(mapping_pattern, line)
            if mapping_match:
                path = mapping_match.group(2)
                method = self._extract_http_method(mapping_match.group(1))
                
                # 查找方法定义
                method_line = line_num
                while method_line < len(lines):
                    method_match = re.search(r'public\s+\w+\s+(\w+)\s*\(', lines[method_line])
                    if method_match:
                        handler_method = method_match.group(1)
                        
                        # 提取参数
                        parameters = self._extract_method_parameters(
                            lines[method_line:method_line+5], param_pattern
                        )
                        
                        # 检查验证逻辑
                        validation = self._check_validation(
                            lines[method_line:method_line+10], validation_pattern
                        )
                        
                        endpoints.append(BackendEndpoint(
                            path=path,
                            method=method,
                            file_path=file_path,
                            handler_method=handler_method,
                            parameters=parameters,
                            validation=validation,
                            line_number=line_num
                        ))
                        break
                    method_line += 1
        
        return endpoints
    
    def _extract_django_endpoints(self, file_path: str, content: str) -> List[BackendEndpoint]:
        """提取Django视图端点"""
        endpoints = []
        lines = content.split('\n')
        
        view_pattern = self.backend_patterns['django']['view']
        param_pattern = self.backend_patterns['django']['param']
        validation_pattern = self.backend_patterns['django']['validation']
        
        for line_num, line in enumerate(lines, 1):
            view_match = re.search(view_pattern, line)
            if view_match:
                handler_method = view_match.group(1)
                
                # 提取参数
                view_content = '\n'.join(lines[line_num:line_num+20])
                parameters = self._extract_django_parameters(view_content, param_pattern)
                
                # 检查验证逻辑
                validation = self._check_validation(
                    lines[line_num:line_num+20], validation_pattern
                )
                
                endpoints.append(BackendEndpoint(
                    path=f"/{handler_method}/",  # 简化处理
                    method="GET/POST",
                    file_path=file_path,
                    handler_method=handler_method,
                    parameters=parameters,
                    validation=validation,
                    line_number=line_num
                ))
        
        return endpoints
    
    def _extract_express_endpoints(self, file_path: str, content: str) -> List[BackendEndpoint]:
        """提取Express.js接口端点"""
        endpoints = []
        lines = content.split('\n')
        
        route_pattern = self.backend_patterns['express']['route']
        param_pattern = self.backend_patterns['express']['param']
        validation_pattern = self.backend_patterns['express']['validation']
        
        for line_num, line in enumerate(lines, 1):
            route_match = re.search(route_pattern, line)
            if route_match:
                method = route_match.group(1).upper()
                path = route_match.group(2)
                
                # 提取参数
                route_content = '\n'.join(lines[line_num:line_num+15])
                parameters = self._extract_express_parameters(route_content, param_pattern)
                
                # 检查验证逻辑
                validation = self._check_validation(
                    lines[line_num:line_num+15], validation_pattern
                )
                
                endpoints.append(BackendEndpoint(
                    path=path,
                    method=method,
                    file_path=file_path,
                    handler_method=f"{method.lower()}_handler",
                    parameters=parameters,
                    validation=validation,
                    line_number=line_num
                ))
        
        return endpoints
    
    def _extract_php_endpoints(self, file_path: str, content: str) -> List[BackendEndpoint]:
        """提取PHP接口端点"""
        endpoints = []
        lines = content.split('\n')
        
        endpoint_pattern = self.backend_patterns['php']['endpoint']
        validation_pattern = self.backend_patterns['php']['validation']
        
        for line_num, line in enumerate(lines, 1):
            endpoint_match = re.search(endpoint_pattern, line)
            if endpoint_match:
                method = endpoint_match.group(1)
                param_name = endpoint_match.group(2)
                
                # 检查验证逻辑
                validation = self._check_validation(
                    lines[line_num:line_num+10], validation_pattern
                )
                
                endpoints.append(BackendEndpoint(
                    path=Path(file_path).name,
                    method=method,
                    file_path=file_path,
                    handler_method="php_handler",
                    parameters=[param_name],
                    validation=validation,
                    line_number=line_num
                ))
        
        return endpoints
    
    def _find_matching_backend(
        self, 
        input_point: InputPoint, 
        backend_endpoints: List[BackendEndpoint]
    ) -> Optional[BackendEndpoint]:
        """为前端输入点找到匹配的后端端点"""
        
        # 1. 精确路径匹配
        if input_point.action:
            for endpoint in backend_endpoints:
                if self._paths_match(input_point.action, endpoint.path):
                    return endpoint
        
        # 2. 参数名匹配
        for endpoint in backend_endpoints:
            if input_point.name in endpoint.parameters:
                return endpoint
        
        # 3. 模糊匹配
        for endpoint in backend_endpoints:
            if self._fuzzy_match(input_point, endpoint):
                return endpoint
        
        return None
    
    def _analyze_security_mapping(
        self, 
        input_point: InputPoint, 
        backend_endpoint: Optional[BackendEndpoint]
    ) -> SecurityMapping:
        """分析安全映射"""
        security_gaps = []
        recommendations = []
        risk_level = 'low'
        
        if not backend_endpoint:
            security_gaps.append("未找到对应的后端处理逻辑")
            recommendations.append("确认前端输入是否有对应的后端验证")
            risk_level = 'high'
        else:
            # 检查后端验证
            if not backend_endpoint.validation:
                security_gaps.append("后端缺少输入验证")
                recommendations.append("在后端添加输入验证逻辑")
                risk_level = 'medium'
            
            # 检查参数匹配
            if input_point.name not in backend_endpoint.parameters:
                security_gaps.append("前后端参数名不匹配")
                recommendations.append("确保前后端参数名一致")
                risk_level = 'medium'
            
            # 检查HTTP方法匹配
            if (input_point.method and backend_endpoint.method and 
                input_point.method.upper() not in backend_endpoint.method.upper()):
                security_gaps.append("HTTP方法不匹配")
                recommendations.append("确保前后端HTTP方法一致")
                risk_level = 'medium'
        
        return SecurityMapping(
            frontend_input=input_point,
            backend_endpoint=backend_endpoint,
            risk_level=risk_level,
            security_gaps=security_gaps,
            recommendations=recommendations
        )
    
    def _extract_http_method(self, mapping_annotation: str) -> str:
        """从Spring映射注解提取HTTP方法"""
        method_map = {
            'GetMapping': 'GET',
            'PostMapping': 'POST',
            'PutMapping': 'PUT',
            'DeleteMapping': 'DELETE',
            'RequestMapping': 'GET/POST'
        }
        return method_map.get(mapping_annotation, 'GET/POST')
    
    def _extract_method_parameters(self, lines: List[str], param_pattern: str) -> List[str]:
        """提取方法参数"""
        parameters = []
        content = '\n'.join(lines)
        
        matches = re.finditer(param_pattern, content)
        for match in matches:
            if match.groups():
                parameters.append(match.group(1))
        
        return parameters
    
    def _extract_django_parameters(self, content: str, param_pattern: str) -> List[str]:
        """提取Django参数"""
        parameters = []
        matches = re.finditer(param_pattern, content)
        for match in matches:
            if len(match.groups()) >= 2:
                parameters.append(match.group(2))
        return parameters
    
    def _extract_express_parameters(self, content: str, param_pattern: str) -> List[str]:
        """提取Express参数"""
        parameters = []
        matches = re.finditer(param_pattern, content)
        for match in matches:
            if len(match.groups()) >= 2:
                parameters.append(match.group(2))
        return parameters
    
    def _check_validation(self, lines: List[str], validation_pattern: str) -> List[str]:
        """检查验证逻辑"""
        validation = []
        content = '\n'.join(lines)
        
        if re.search(validation_pattern, content):
            validation.append("存在验证逻辑")
        
        return validation
    
    def _paths_match(self, frontend_path: str, backend_path: str) -> bool:
        """检查路径是否匹配"""
        # 简化的路径匹配逻辑
        frontend_path = frontend_path.strip('/')
        backend_path = backend_path.strip('/')
        
        return frontend_path == backend_path or frontend_path in backend_path
    
    def _fuzzy_match(self, input_point: InputPoint, endpoint: BackendEndpoint) -> bool:
        """模糊匹配"""
        # 基于文件名或方法名的模糊匹配
        if input_point.action:
            action_name = Path(input_point.action).stem
            if action_name in endpoint.handler_method or action_name in endpoint.file_path:
                return True
        
        return False
    
    def generate_security_report(self, mappings: List[SecurityMapping]) -> Dict[str, Any]:
        """生成安全报告"""
        report = {
            'total_inputs': len(mappings),
            'mapped_inputs': len([m for m in mappings if m.backend_endpoint]),
            'unmapped_inputs': len([m for m in mappings if not m.backend_endpoint]),
            'high_risk': len([m for m in mappings if m.risk_level == 'high']),
            'medium_risk': len([m for m in mappings if m.risk_level == 'medium']),
            'low_risk': len([m for m in mappings if m.risk_level == 'low']),
            'security_gaps': [],
            'recommendations': []
        }
        
        # 收集所有安全缺口和建议
        for mapping in mappings:
            report['security_gaps'].extend(mapping.security_gaps)
            report['recommendations'].extend(mapping.recommendations)
        
        # 去重
        report['security_gaps'] = list(set(report['security_gaps']))
        report['recommendations'] = list(set(report['recommendations']))
        
        return report
