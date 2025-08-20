#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上下文关联分析器
用于分析跨文件的调用关系、数据流和安全边界
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class MethodCall:
    """方法调用信息"""
    caller_file: str
    caller_method: str
    called_method: str
    called_class: Optional[str]
    line_number: int
    parameters: List[str]
    context: str

@dataclass
class DataFlow:
    """数据流信息"""
    variable_name: str
    source_file: str
    source_method: str
    data_type: str
    flow_path: List[str]
    security_sensitive: bool

@dataclass
class SecurityBoundary:
    """安全边界信息"""
    layer: str  # controller, service, dao
    file_path: str
    methods: List[str]
    security_controls: List[str]
    responsibilities: List[str]

class ContextAnalyzer:
    """上下文关联分析器"""
    
    def __init__(self):
        self.method_calls: List[MethodCall] = []
        self.data_flows: List[DataFlow] = []
        self.security_boundaries: Dict[str, SecurityBoundary] = {}
        self.project_structure: Dict[str, Any] = {}
        
    def analyze_project_context(self, project_files: List[Dict]) -> Dict[str, Any]:
        """分析整个项目的上下文"""
        # 1. 构建项目结构
        self._build_project_structure(project_files)
        
        # 2. 分析方法调用链
        self._analyze_method_calls(project_files)
        
        # 3. 追踪数据流
        self._analyze_data_flows(project_files)
        
        # 4. 识别安全边界
        self._identify_security_boundaries(project_files)
        
        return {
            'method_calls': self.method_calls,
            'data_flows': self.data_flows,
            'security_boundaries': self.security_boundaries,
            'project_structure': self.project_structure
        }
    
    def _build_project_structure(self, project_files: List[Dict]):
        """构建项目结构"""
        for file_info in project_files:
            file_path = str(file_info.get('path', ''))
            language = file_info.get('language', '')
            
            # 分析文件层次
            layer = self._detect_layer(file_path)
            package = self._extract_package(file_path, language)
            
            self.project_structure[file_path] = {
                'layer': layer,
                'package': package,
                'language': language,
                'classes': self._extract_classes(file_info),
                'methods': self._extract_methods(file_info)
            }
    
    def _analyze_method_calls(self, project_files: List[Dict]):
        """分析方法调用链"""
        for file_info in project_files:
            file_path = str(file_info.get('path', ''))
            
            try:
                # 读取文件内容
                if Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 根据语言分析调用
                    language = file_info.get('language', '')
                    if language == 'java':
                        self._analyze_java_calls(file_path, content)
                    elif language == 'python':
                        self._analyze_python_calls(file_path, content)
                    elif language == 'javascript':
                        self._analyze_js_calls(file_path, content)
                        
            except Exception as e:
                print(f"Warning: Failed to analyze calls in {file_path}: {e}")
    
    def _analyze_java_calls(self, file_path: str, content: str):
        """分析Java方法调用"""
        lines = content.split('\n')
        current_class = None
        current_method = None
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 识别类定义
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
            
            # 识别方法定义
            method_match = re.search(r'(public|private|protected).*?\s+(\w+)\s*\(', line)
            if method_match:
                current_method = method_match.group(2)
            
            # 识别方法调用
            call_patterns = [
                r'(\w+)\.(\w+)\s*\(',  # object.method()
                r'(\w+)\s*\(',         # method()
                r'new\s+(\w+)\s*\(',   # new Constructor()
            ]
            
            for pattern in call_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    if len(match.groups()) == 2:
                        called_class, called_method = match.groups()
                    else:
                        called_class, called_method = None, match.group(1)
                    
                    # 提取参数
                    params = self._extract_parameters(line, match.end())
                    
                    call = MethodCall(
                        caller_file=file_path,
                        caller_method=current_method or 'unknown',
                        called_method=called_method,
                        called_class=called_class,
                        line_number=i,
                        parameters=params,
                        context=line
                    )
                    self.method_calls.append(call)
    
    def _analyze_python_calls(self, file_path: str, content: str):
        """分析Python方法调用"""
        try:
            tree = ast.parse(content)
            
            class CallVisitor(ast.NodeVisitor):
                def __init__(self, file_path):
                    self.file_path = file_path
                    self.current_method = None
                    self.calls = []
                
                def visit_FunctionDef(self, node):
                    old_method = self.current_method
                    self.current_method = node.name
                    self.generic_visit(node)
                    self.current_method = old_method
                
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Attribute):
                        # object.method() 调用
                        called_method = node.func.attr
                        called_class = ast.unparse(node.func.value) if hasattr(ast, 'unparse') else 'unknown'
                    elif isinstance(node.func, ast.Name):
                        # method() 调用
                        called_method = node.func.id
                        called_class = None
                    else:
                        called_method = 'unknown'
                        called_class = None
                    
                    call = MethodCall(
                        caller_file=self.file_path,
                        caller_method=self.current_method or 'module_level',
                        called_method=called_method,
                        called_class=called_class,
                        line_number=node.lineno,
                        parameters=[],  # 简化处理
                        context=f"Line {node.lineno}"
                    )
                    self.calls.append(call)
                    self.generic_visit(node)
            
            visitor = CallVisitor(file_path)
            visitor.visit(tree)
            self.method_calls.extend(visitor.calls)
            
        except Exception as e:
            print(f"Warning: Failed to parse Python file {file_path}: {e}")
    
    def _analyze_js_calls(self, file_path: str, content: str):
        """分析JavaScript方法调用"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 简单的正则匹配JavaScript调用
            call_patterns = [
                r'(\w+)\.(\w+)\s*\(',  # object.method()
                r'(\w+)\s*\(',         # function()
            ]
            
            for pattern in call_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    if len(match.groups()) == 2:
                        called_class, called_method = match.groups()
                    else:
                        called_class, called_method = None, match.group(1)
                    
                    call = MethodCall(
                        caller_file=file_path,
                        caller_method='unknown',
                        called_method=called_method,
                        called_class=called_class,
                        line_number=i,
                        parameters=[],
                        context=line.strip()
                    )
                    self.method_calls.append(call)
    
    def _analyze_data_flows(self, project_files: List[Dict]):
        """分析数据流"""
        # 识别敏感数据源
        sensitive_sources = [
            'request.getParameter', 'request.getHeader', 'request.getInputStream',
            'HttpServletRequest', '@RequestParam', '@PathVariable',
            'input()', 'raw_input()', 'sys.argv', 'os.environ',
            'req.body', 'req.params', 'req.query', 'req.headers'
        ]
        
        for call in self.method_calls:
            # 检查是否为敏感数据源
            is_sensitive = any(source in call.context for source in sensitive_sources)
            
            if is_sensitive:
                data_flow = DataFlow(
                    variable_name='user_input',
                    source_file=call.caller_file,
                    source_method=call.caller_method,
                    data_type='user_input',
                    flow_path=[call.caller_file],
                    security_sensitive=True
                )
                self.data_flows.append(data_flow)
    
    def _identify_security_boundaries(self, project_files: List[Dict]):
        """识别安全边界"""
        for file_path, structure in self.project_structure.items():
            layer = structure['layer']
            
            if layer in ['controller', 'service', 'dao']:
                # 分析安全控制
                security_controls = self._detect_security_controls(file_path, structure)
                
                boundary = SecurityBoundary(
                    layer=layer,
                    file_path=file_path,
                    methods=structure.get('methods', []),
                    security_controls=security_controls,
                    responsibilities=self._get_layer_responsibilities(layer)
                )
                
                self.security_boundaries[file_path] = boundary
    
    def _detect_layer(self, file_path: str) -> str:
        """检测文件所在的架构层次"""
        path_lower = file_path.lower()
        
        if any(indicator in path_lower for indicator in ['controller', 'rest', 'api', 'endpoint']):
            return 'controller'
        elif any(indicator in path_lower for indicator in ['service', 'business', 'logic']):
            return 'service'
        elif any(indicator in path_lower for indicator in ['dao', 'repository', 'mapper']):
            return 'dao'
        elif any(indicator in path_lower for indicator in ['entity', 'domain', 'pojo', 'model']):
            return 'entity'
        else:
            return 'unknown'
    
    def _extract_package(self, file_path: str, language: str) -> str:
        """提取包名"""
        if language == 'java':
            # Java包路径
            parts = Path(file_path).parts
            if 'java' in parts:
                java_index = parts.index('java')
                if java_index + 1 < len(parts):
                    return '.'.join(parts[java_index + 1:-1])
        return 'unknown'
    
    def _extract_classes(self, file_info: Dict) -> List[str]:
        """提取类名"""
        # 简化实现，从文件名推断
        file_path = str(file_info.get('path', ''))
        file_name = Path(file_path).stem
        return [file_name] if file_name else []
    
    def _extract_methods(self, file_info: Dict) -> List[str]:
        """提取方法名"""
        # 简化实现，返回空列表
        return []
    
    def _extract_parameters(self, line: str, start_pos: int) -> List[str]:
        """提取方法参数"""
        # 简化实现
        return []
    
    def _detect_security_controls(self, file_path: str, structure: Dict) -> List[str]:
        """检测安全控制"""
        controls = []
        
        try:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检测常见安全注解和控制
                security_patterns = [
                    '@PreAuthorize', '@Secured', '@RolesAllowed',
                    '@Valid', '@Validated', 'SecurityContext',
                    'authentication', 'authorization', 'csrf'
                ]
                
                for pattern in security_patterns:
                    if pattern in content:
                        controls.append(pattern)
                        
        except Exception:
            pass
        
        return controls
    
    def _get_layer_responsibilities(self, layer: str) -> List[str]:
        """获取层次职责"""
        responsibilities = {
            'controller': ['权限验证', '输入校验', '会话管理', '请求路由'],
            'service': ['业务逻辑', '事务管理', '数据验证'],
            'dao': ['数据查询', '数据持久化'],
            'entity': ['数据模型', '数据验证']
        }
        return responsibilities.get(layer, [])
    
    def get_call_chain(self, target_method: str, max_depth: int = 5) -> List[List[MethodCall]]:
        """获取指定方法的调用链"""
        chains = []
        
        def find_chains(method_name: str, current_chain: List[MethodCall], depth: int):
            if depth >= max_depth:
                return
            
            for call in self.method_calls:
                if call.called_method == method_name:
                    new_chain = current_chain + [call]
                    chains.append(new_chain)
                    
                    # 继续向上查找调用者
                    find_chains(call.caller_method, new_chain, depth + 1)
        
        find_chains(target_method, [], 0)
        return chains
    
    def is_security_sensitive_flow(self, file_path: str, method_name: str) -> bool:
        """检查是否为安全敏感的数据流"""
        for flow in self.data_flows:
            if flow.source_file == file_path and flow.security_sensitive:
                return True
        return False
    
    def get_security_boundary_info(self, file_path: str) -> Optional[SecurityBoundary]:
        """获取文件的安全边界信息"""
        return self.security_boundaries.get(file_path)
