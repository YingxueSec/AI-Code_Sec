#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能代码预处理器 - 提取关键代码段，减少LLM分析负担
"""

import re
import ast
from typing import List, Dict, Any, Tuple
from pathlib import Path


class CodePreprocessor:
    """代码预处理器"""
    
    def __init__(self):
        self.security_keywords = {
            'python': [
                'execute', 'eval', 'exec', 'subprocess', 'os.system', 'input', 'raw_input',
                'pickle', 'yaml.load', 'sql', 'query', 'cursor', 'request', 'session',
                'open', 'file', 'read', 'write', 'import', 'from', '__import__'
            ],
            'java': [
                'execute', 'Runtime', 'ProcessBuilder', 'Statement', 'PreparedStatement',
                'request', 'response', 'session', 'cookie', 'parameter', 'header',
                'file', 'path', 'stream', 'reader', 'writer', 'reflection'
            ],
            'javascript': [
                'eval', 'Function', 'setTimeout', 'setInterval', 'innerHTML', 'outerHTML',
                'document.write', 'location', 'window', 'require', 'import', 'fetch',
                'XMLHttpRequest', 'localStorage', 'sessionStorage', 'cookie'
            ],
            'php': [
                'eval', 'exec', 'system', 'shell_exec', 'passthru', 'include', 'require',
                'file_get_contents', 'fopen', 'mysql_query', 'mysqli_query', '$_GET',
                '$_POST', '$_REQUEST', '$_SESSION', '$_COOKIE', 'unserialize'
            ]
        }
    
    def extract_security_relevant_code(self, code: str, language: str, max_lines: int = 100) -> str:
        """提取安全相关的代码段"""
        lines = code.split('\n')
        relevant_lines = []
        keywords = self.security_keywords.get(language.lower(), [])
        
        # 提取包含安全关键词的行及其上下文
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in keywords):
                # 添加上下文（前后2行）
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                for j in range(start, end):
                    if j not in [idx for idx, _ in relevant_lines]:
                        relevant_lines.append((j, lines[j]))
        
        # 如果相关代码太少，添加函数定义和类定义
        if len(relevant_lines) < max_lines // 2:
            relevant_lines.extend(self._extract_definitions(lines, language))
        
        # 排序并去重
        relevant_lines = sorted(list(set(relevant_lines)), key=lambda x: x[0])
        
        # 限制行数
        if len(relevant_lines) > max_lines:
            relevant_lines = relevant_lines[:max_lines]
        
        # 重构代码
        if relevant_lines:
            result_lines = []
            last_line_num = -1
            
            for line_num, line_content in relevant_lines:
                if line_num > last_line_num + 1:
                    result_lines.append(f"# ... (省略第{last_line_num + 1}-{line_num - 1}行)")
                result_lines.append(f"{line_num + 1:4d}: {line_content}")
                last_line_num = line_num
            
            return '\n'.join(result_lines)
        
        # 如果没有找到相关代码，返回前面部分
        return '\n'.join(f"{i+1:4d}: {line}" for i, line in enumerate(lines[:max_lines]))
    
    def _extract_definitions(self, lines: List[str], language: str) -> List[Tuple[int, str]]:
        """提取函数和类定义"""
        definitions = []
        
        if language.lower() == 'python':
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(('def ', 'class ', 'async def ')):
                    definitions.append((i, line))
        elif language.lower() == 'java':
            for i, line in enumerate(lines):
                stripped = line.strip()
                if any(keyword in stripped for keyword in ['public ', 'private ', 'protected ']):
                    if any(keyword in stripped for keyword in ['class ', 'interface ', 'method']):
                        definitions.append((i, line))
        elif language.lower() == 'javascript':
            for i, line in enumerate(lines):
                stripped = line.strip()
                if any(keyword in stripped for keyword in ['function ', 'class ', 'const ', 'let ', 'var ']):
                    definitions.append((i, line))
        
        return definitions
    
    def should_skip_file(self, file_path: str, file_size: int) -> Tuple[bool, str]:
        """判断是否应该跳过文件"""
        path = Path(file_path)
        
        # 跳过过大的文件
        if file_size > 1024 * 1024:  # 1MB
            return True, "文件过大"
        
        # 跳过测试文件（通常安全风险较低）
        if any(keyword in path.name.lower() for keyword in ['test', 'spec', 'mock']):
            return True, "测试文件"
        
        # 跳过配置文件
        if path.suffix.lower() in ['.json', '.xml', '.yaml', '.yml', '.ini', '.cfg']:
            return True, "配置文件"
        
        # 跳过文档文件
        if path.suffix.lower() in ['.md', '.txt', '.rst', '.doc']:
            return True, "文档文件"
        
        return False, ""
    
    def get_file_priority(self, file_path: str, language: str) -> int:
        """获取文件优先级（数字越大优先级越高）"""
        path = Path(file_path)
        priority = 0
        
        # 基于文件名的优先级
        high_priority_names = ['auth', 'login', 'admin', 'user', 'security', 'api', 'controller']
        if any(name in path.name.lower() for name in high_priority_names):
            priority += 10
        
        # 基于路径的优先级
        if any(keyword in str(path).lower() for keyword in ['api', 'controller', 'service', 'handler']):
            priority += 5
        
        # 基于语言的优先级
        if language.lower() in ['python', 'java', 'php', 'javascript']:
            priority += 3
        
        # 降低测试文件优先级
        if any(keyword in path.name.lower() for keyword in ['test', 'spec']):
            priority -= 5
        
        return priority
    
    def optimize_code_for_analysis(self, code: str, language: str, quick_mode: bool = False) -> str:
        """优化代码以提高分析效率"""
        if quick_mode:
            # 快速模式：只保留前50行和安全相关代码
            lines = code.split('\n')
            if len(lines) > 50:
                header = '\n'.join(lines[:20])
                security_code = self.extract_security_relevant_code(code, language, 30)
                return f"{header}\n\n# ... (省略中间部分)\n\n{security_code}"
        
        # 标准模式：提取安全相关代码
        if len(code.split('\n')) > 200:
            return self.extract_security_relevant_code(code, language, 150)
        
        return code
    
    def get_analysis_hints(self, code: str, language: str) -> List[str]:
        """获取分析提示，帮助LLM聚焦"""
        hints = []
        code_lower = code.lower()
        
        # 检测可能的安全问题模式
        if language.lower() == 'python':
            if 'subprocess' in code_lower or 'os.system' in code_lower:
                hints.append("检查命令注入漏洞")
            if 'execute' in code_lower and ('sql' in code_lower or 'query' in code_lower):
                hints.append("检查SQL注入漏洞")
            if 'pickle' in code_lower:
                hints.append("检查反序列化漏洞")
            if 'eval' in code_lower or 'exec' in code_lower:
                hints.append("检查代码注入漏洞")
        
        elif language.lower() == 'java':
            if 'runtime' in code_lower or 'processbuilder' in code_lower:
                hints.append("检查命令注入漏洞")
            if 'statement' in code_lower and 'execute' in code_lower:
                hints.append("检查SQL注入漏洞")
            if 'request.getparameter' in code_lower:
                hints.append("检查输入验证")
        
        elif language.lower() == 'javascript':
            if 'eval' in code_lower:
                hints.append("检查代码注入漏洞")
            if 'innerhtml' in code_lower:
                hints.append("检查XSS漏洞")
            if 'document.write' in code_lower:
                hints.append("检查XSS漏洞")
        
        return hints


# 全局预处理器实例
_global_preprocessor = None

def get_preprocessor() -> CodePreprocessor:
    """获取全局预处理器实例"""
    global _global_preprocessor
    if _global_preprocessor is None:
        _global_preprocessor = CodePreprocessor()
    return _global_preprocessor
