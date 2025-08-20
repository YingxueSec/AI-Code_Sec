"""
大文件处理器 - 用于处理超过大小限制的重要文件
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeChunk:
    """代码块"""
    
    def __init__(self, content: str, start_line: int, end_line: int, chunk_type: str = "general"):
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.chunk_type = chunk_type  # function, class, general
        self.size = len(content)
    
    def __repr__(self):
        return f"CodeChunk(lines={self.start_line}-{self.end_line}, type={self.chunk_type}, size={self.size})"


class LargeFileHandler:
    """大文件处理器"""
    
    def __init__(self, max_chunk_size: int = 50000):
        """
        初始化大文件处理器
        
        Args:
            max_chunk_size: 每个块的最大字符数
        """
        self.max_chunk_size = max_chunk_size
        
        # PHP函数和类的正则模式
        self.php_patterns = {
            'function': re.compile(r'^\s*(public|private|protected)?\s*function\s+(\w+)\s*\(', re.MULTILINE | re.IGNORECASE),
            'class': re.compile(r'^\s*class\s+(\w+)', re.MULTILINE | re.IGNORECASE),
            'method': re.compile(r'^\s*(public|private|protected)\s+function\s+(\w+)\s*\(', re.MULTILINE | re.IGNORECASE)
        }
    
    def should_chunk_file(self, file_path: Path, max_file_size: int) -> bool:
        """检查文件是否需要分块处理"""
        try:
            file_size = file_path.stat().st_size
            return file_size > max_file_size
        except OSError:
            return False
    
    def chunk_php_file(self, file_path: Path) -> List[CodeChunk]:
        """
        智能分块PHP文件
        
        Args:
            file_path: PHP文件路径
            
        Returns:
            代码块列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            chunks = []
            
            # 首先尝试按函数/类分块
            function_chunks = self._chunk_by_functions(content, lines)
            
            if function_chunks:
                # 检查每个函数块是否还需要进一步分块
                for chunk in function_chunks:
                    if chunk.size > self.max_chunk_size:
                        # 大函数需要进一步分块
                        sub_chunks = self._chunk_by_size(chunk.content, chunk.start_line)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(chunk)
            else:
                # 如果无法按函数分块，则按大小分块
                chunks = self._chunk_by_size(content, 1)
            
            logger.info(f"Chunked {file_path.name} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking file {file_path}: {e}")
            return []
    
    def _chunk_by_functions(self, content: str, lines: List[str]) -> List[CodeChunk]:
        """按函数/类分块"""
        chunks = []
        current_chunk_start = 0
        current_chunk_lines = []
        current_function = None
        brace_count = 0
        in_function = False
        
        for i, line in enumerate(lines):
            current_chunk_lines.append(line)
            
            # 检查是否是函数或类定义
            if not in_function:
                for pattern_type, pattern in self.php_patterns.items():
                    match = pattern.search(line)
                    if match:
                        if current_chunk_lines and len(current_chunk_lines) > 1:
                            # 保存之前的代码块
                            chunk_content = '\n'.join(current_chunk_lines[:-1])
                            if chunk_content.strip():
                                chunks.append(CodeChunk(
                                    content=chunk_content,
                                    start_line=current_chunk_start + 1,
                                    end_line=i,
                                    chunk_type="general"
                                ))
                        
                        # 开始新的函数块
                        current_chunk_start = i
                        current_chunk_lines = [line]
                        current_function = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                        in_function = True
                        brace_count = 0
                        break
            
            if in_function:
                # 计算大括号
                brace_count += line.count('{') - line.count('}')
                
                # 如果大括号平衡且不为0，说明函数结束
                if brace_count == 0 and '{' in '\n'.join(current_chunk_lines):
                    chunk_content = '\n'.join(current_chunk_lines)
                    chunks.append(CodeChunk(
                        content=chunk_content,
                        start_line=current_chunk_start + 1,
                        end_line=i + 1,
                        chunk_type="function"
                    ))
                    
                    # 重置状态
                    in_function = False
                    current_function = None
                    current_chunk_start = i + 1
                    current_chunk_lines = []
        
        # 处理剩余内容
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    content=chunk_content,
                    start_line=current_chunk_start + 1,
                    end_line=len(lines),
                    chunk_type="function" if in_function else "general"
                ))
        
        return chunks
    
    def _chunk_by_size(self, content: str, start_line: int) -> List[CodeChunk]:
        """按大小分块"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        chunk_start_line = start_line
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > self.max_chunk_size and current_chunk:
                # 创建当前块
                chunk_content = '\n'.join(current_chunk)
                chunks.append(CodeChunk(
                    content=chunk_content,
                    start_line=chunk_start_line,
                    end_line=chunk_start_line + len(current_chunk) - 1,
                    chunk_type="size_based"
                ))
                
                # 开始新块
                current_chunk = [line]
                current_size = line_size
                chunk_start_line = start_line + i
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # 处理最后一块
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(CodeChunk(
                content=chunk_content,
                start_line=chunk_start_line,
                end_line=chunk_start_line + len(current_chunk) - 1,
                chunk_type="size_based"
            ))
        
        return chunks
    
    def merge_chunk_results(self, chunk_results: List[Dict[str, Any]], file_path: str) -> Dict[str, Any]:
        """
        合并多个代码块的审计结果
        
        Args:
            chunk_results: 各个代码块的审计结果
            file_path: 原始文件路径
            
        Returns:
            合并后的审计结果
        """
        if not chunk_results:
            return {
                "file_path": file_path,
                "vulnerabilities": [],
                "summary": "No results from chunks",
                "chunk_count": 0
            }
        
        # 合并所有漏洞
        all_vulnerabilities = []
        all_summaries = []
        
        for i, result in enumerate(chunk_results):
            if result and isinstance(result, dict):
                # 提取漏洞信息
                vulnerabilities = result.get('vulnerabilities', [])
                if isinstance(vulnerabilities, list):
                    # 为每个漏洞添加块信息
                    for vuln in vulnerabilities:
                        if isinstance(vuln, dict):
                            vuln['chunk_index'] = i
                            vuln['source_file'] = file_path
                    all_vulnerabilities.extend(vulnerabilities)
                
                # 提取摘要
                summary = result.get('summary', '')
                if summary and isinstance(summary, str):
                    all_summaries.append(f"Chunk {i+1}: {summary}")
        
        # 去重漏洞（基于类型和描述）
        unique_vulnerabilities = []
        seen_vulns = set()
        
        for vuln in all_vulnerabilities:
            if isinstance(vuln, dict):
                vuln_key = (vuln.get('type', ''), vuln.get('description', ''))
                if vuln_key not in seen_vulns:
                    seen_vulns.add(vuln_key)
                    unique_vulnerabilities.append(vuln)
        
        # 生成综合摘要
        total_chunks = len(chunk_results)
        total_vulnerabilities = len(unique_vulnerabilities)
        
        combined_summary = f"Large file analysis completed: {total_chunks} chunks processed, {total_vulnerabilities} unique vulnerabilities found."
        
        if all_summaries:
            combined_summary += "\n\nChunk summaries:\n" + "\n".join(all_summaries)
        
        return {
            "file_path": file_path,
            "vulnerabilities": unique_vulnerabilities,
            "summary": combined_summary,
            "chunk_count": total_chunks,
            "total_vulnerabilities": total_vulnerabilities,
            "processing_method": "chunked_analysis"
        }
    
    def get_important_chunks(self, chunks: List[CodeChunk], max_chunks: int = 10) -> List[CodeChunk]:
        """
        获取最重要的代码块进行优先分析
        
        Args:
            chunks: 所有代码块
            max_chunks: 最大返回块数
            
        Returns:
            按重要性排序的代码块
        """
        # 重要性评分
        scored_chunks = []
        
        for chunk in chunks:
            score = 0
            content_lower = chunk.content.lower()
            
            # 函数类型加分
            if chunk.chunk_type == "function":
                score += 10
            elif chunk.chunk_type == "class":
                score += 8
            
            # 安全相关关键词加分
            security_keywords = [
                'password', 'login', 'auth', 'session', 'cookie', 'token',
                'sql', 'query', 'select', 'insert', 'update', 'delete',
                'upload', 'file', 'input', 'post', 'get', 'request',
                'admin', 'user', 'permission', 'role', 'access'
            ]
            
            for keyword in security_keywords:
                score += content_lower.count(keyword) * 2
            
            # 大小适中的块加分（不太小也不太大）
            if 1000 < chunk.size < 20000:
                score += 5
            
            scored_chunks.append((score, chunk))
        
        # 按分数排序并返回前N个
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:max_chunks]]
