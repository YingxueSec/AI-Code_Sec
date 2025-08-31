#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨文件关联分析器
当发现不确定漏洞时，自动分析相关文件进行辅助判定
"""

import re
import ast
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RelatedFile:
    """相关文件信息"""
    path: str
    relationship: str  # 'caller', 'callee', 'config', 'template', 'parent'
    confidence: float
    reason: str

@dataclass
class CrossFileAnalysisResult:
    """跨文件分析结果"""
    original_confidence: float
    adjusted_confidence: float
    related_files: List[RelatedFile]
    evidence: List[str]
    recommendation: str

class CrossFileAnalyzer:
    """跨文件关联分析器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.file_cache = {}  # 文件内容缓存
        self.analysis_cache = {}  # 新增：分析结果缓存
        self.search_cache = {}    # 新增：搜索结果缓存
        self.semaphore = asyncio.Semaphore(2)  # 限制跨文件分析并发数
        
    async def analyze_uncertain_finding(
        self,
        finding: Dict[str, Any],
        file_path: str,
        code: str,
        llm_manager,
        analysis_stack: Optional[Set[str]] = None,
        max_depth: int = 3
    ) -> CrossFileAnalysisResult:
        """
        分析不确定的漏洞发现，通过关联文件进行辅助判定

        Args:
            finding: 漏洞发现信息
            file_path: 当前文件路径
            code: 当前文件代码
            llm_manager: LLM管理器，用于分析关联文件

        Returns:
            CrossFileAnalysisResult: 跨文件分析结果
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(finding, file_path)

        # 检查缓存
        if cache_key in self.analysis_cache:
            logger.info(f"Using cached cross-file analysis result for {file_path}")
            return self.analysis_cache[cache_key]

        # 使用信号量控制并发
        async with self.semaphore:
            # 执行分析
            result = await self._perform_analysis(finding, file_path, code, llm_manager, analysis_stack, max_depth)

            # 缓存结果
            self.analysis_cache[cache_key] = result

            return result

    async def _perform_analysis(
        self,
        finding: Dict[str, Any],
        file_path: str,
        code: str,
        llm_manager,
        analysis_stack: Optional[Set[str]] = None,
        max_depth: int = 3
    ) -> CrossFileAnalysisResult:
        """执行实际的跨文件分析"""
        from ..utils.recursion_monitor import RecursionGuard, AnalysisType

        # 使用递归保护
        async with RecursionGuard(file_path, AnalysisType.CROSS_FILE):
            # 初始化分析堆栈，用于防止无限递归
            if analysis_stack is None:
                analysis_stack = set()

            # 将当前文件加入堆栈
            analysis_stack.add(file_path)

            # 检查是否超过最大递归深度
            if len(analysis_stack) > max_depth:
                return CrossFileAnalysisResult(
                    original_confidence=finding.get('confidence', 0.5),
                    adjusted_confidence=finding.get('confidence', 0.5),
                    related_files=[],
                    evidence=["Cross-file analysis stopped: maximum recursion depth reached."],
                    recommendation="递归分析深度超限，可能存在循环依赖，请手动审查。"
                )

            original_confidence = finding.get('confidence', 0.5)

            # 对需要跨文件分析的问题进行处理
            # 调整阈值，允许更多问题进行跨文件分析
            if original_confidence > 0.99:
                return CrossFileAnalysisResult(
                    original_confidence=original_confidence,
                    adjusted_confidence=original_confidence,
                    related_files=[],
                    evidence=[],
                    recommendation="极高置信度问题，无需跨文件分析"
                )

            # 1. 识别相关文件
            related_files = await self._find_related_files(finding, file_path, code)

            # 2. 分析相关文件
            evidence = []
            confidence_adjustments = []

            for related_file in related_files:
                try:
                    # 如果关联文件已在分析堆栈中，则跳过，避免循环
                    if related_file.path in analysis_stack:
                        continue

                    analysis = await self._analyze_related_file(
                        related_file, finding, llm_manager, analysis_stack, max_depth
                    )
                    evidence.extend(analysis['evidence'])
                    confidence_adjustments.append(analysis['confidence_adjustment'])

                except Exception as e:
                    print(f"Warning: Failed to analyze related file {related_file.path}: {e}")

            # 3. 计算调整后的置信度
            adjusted_confidence = self._calculate_adjusted_confidence(
                original_confidence, confidence_adjustments
            )

            # 4. 生成建议
            recommendation = self._generate_recommendation(
                finding, evidence, original_confidence, adjusted_confidence
            )

            return CrossFileAnalysisResult(
                original_confidence=original_confidence,
                adjusted_confidence=adjusted_confidence,
                related_files=related_files,
                evidence=evidence,
                recommendation=recommendation
            )
    
    async def _find_related_files(
        self, 
        finding: Dict[str, Any], 
        file_path: str, 
        code: str
    ) -> List[RelatedFile]:
        """查找相关文件"""
        related_files = []
        finding_type = finding.get('type', '')
        
        # 1. 查找调用者文件
        callers = self._find_caller_files(file_path, code)
        related_files.extend(callers)
        
        # 2. 查找被调用文件
        callees = self._find_callee_files(file_path, code)
        related_files.extend(callees)
        
        # 3. 查找配置文件
        if '路径遍历' in finding_type or '文件上传' in finding_type:
            config_files = self._find_config_files(file_path)
            related_files.extend(config_files)
        
        # 4. 查找模板文件
        if 'XSS' in finding_type:
            template_files = self._find_template_files(file_path, code)
            related_files.extend(template_files)
        
        # 5. 查找父级控制器
        if 'upload' in file_path.lower() or 'file' in file_path.lower():
            parent_files = self._find_parent_controller_files(file_path)
            related_files.extend(parent_files)
        
        return related_files[:5]  # 限制最多5个相关文件
    
    def _find_caller_files(self, file_path: str, code: str) -> List[RelatedFile]:
        """查找调用当前文件的文件"""
        related_files = []
        current_file = Path(file_path)
        
        # 搜索可能的调用者
        search_patterns = [
            current_file.stem,  # 文件名
            current_file.name,  # 完整文件名
        ]
        
        # 在项目中搜索引用
        for pattern in search_patterns:
            for found_file in self._search_files_containing(pattern):
                if found_file != file_path:
                    related_files.append(RelatedFile(
                        path=found_file,
                        relationship='caller',
                        confidence=0.7,
                        reason=f"文件中包含对{pattern}的引用"
                    ))
        
        return related_files[:3]
    
    def _find_callee_files(self, file_path: str, code: str) -> List[RelatedFile]:
        """查找当前文件调用的文件"""
        related_files = []
        
        # 分析代码中的包含/引用
        include_patterns = [
            r'include\s*[\'"]([^\'"]+)[\'"]',
            r'require\s*[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'from\s+[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in include_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            for match in matches:
                # 构建可能的文件路径
                possible_paths = self._resolve_file_path(file_path, match)
                for path in possible_paths:
                    if path.exists():
                        related_files.append(RelatedFile(
                            path=str(path),
                            relationship='callee',
                            confidence=0.8,
                            reason=f"通过{pattern}引用"
                        ))
        
        return related_files[:3]
    
    def _find_config_files(self, file_path: str) -> List[RelatedFile]:
        """查找配置文件"""
        related_files = []
        
        # 常见配置文件
        config_patterns = [
            '**/config.php',
            '**/config.ini',
            '**/settings.py',
            '**/application.properties',
            '**/web.xml',
            '**/.htaccess'
        ]
        
        for pattern in config_patterns:
            for config_file in self.project_path.rglob(pattern):
                related_files.append(RelatedFile(
                    path=str(config_file),
                    relationship='config',
                    confidence=0.6,
                    reason="项目配置文件，可能包含安全设置"
                ))
        
        return related_files[:2]
    
    def _find_template_files(self, file_path: str, code: str) -> List[RelatedFile]:
        """查找模板文件"""
        related_files = []
        
        # 查找模板引用
        template_patterns = [
            r'template\s*[\'"]([^\'"]+)[\'"]',
            r'render\s*[\'"]([^\'"]+)[\'"]',
            r'include\s*[\'"]([^\'"]+\.html?)[\'"]',
        ]
        
        for pattern in template_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            for match in matches:
                possible_paths = self._resolve_file_path(file_path, match)
                for path in possible_paths:
                    if path.exists():
                        related_files.append(RelatedFile(
                            path=str(path),
                            relationship='template',
                            confidence=0.7,
                            reason=f"模板文件引用: {match}"
                        ))
        
        return related_files[:2]
    
    def _find_parent_controller_files(self, file_path: str) -> List[RelatedFile]:
        """查找父级控制器文件"""
        related_files = []
        current_path = Path(file_path)
        
        # 向上查找控制器文件
        for parent in current_path.parents:
            for controller_file in parent.glob('*Controller*'):
                if controller_file.is_file():
                    related_files.append(RelatedFile(
                        path=str(controller_file),
                        relationship='parent',
                        confidence=0.6,
                        reason="父级控制器，可能包含权限验证"
                    ))
        
        return related_files[:2]
    
    async def _analyze_related_file(
        self,
        related_file: RelatedFile,
        finding: Dict[str, Any],
        llm_manager,
        analysis_stack: Set[str],
        max_depth: int
    ) -> Dict[str, Any]:
        """分析相关文件"""
        try:
            # 读取文件内容
            if related_file.path not in self.file_cache:
                with open(related_file.path, 'r', encoding='utf-8', errors='ignore') as f:
                    self.file_cache[related_file.path] = f.read()
            
            related_code = self.file_cache[related_file.path]
            
            # 构建针对性的分析提示
            analysis_prompt = self._build_related_file_analysis_prompt(
                finding, related_file, related_code
            )
            
            # 使用LLM分析相关文件
            # 🔥 关键修改：使用 analysis_context 参数防止递归
            result = await llm_manager.analyze_code(
                code=related_code,
                file_path=related_file.path,
                language=self._detect_language(related_file.path),
                template="related_file_analysis",
                prompt_override=analysis_prompt,
                analysis_context="related_file"  # 🔥 新增：标记为关联文件分析
            )
            
            if result.get('success'):
                findings = result.get('findings', [])
                return self._extract_evidence_from_findings(findings, finding)
            else:
                return {'evidence': [], 'confidence_adjustment': 0}
                
        except Exception as e:
            print(f"Error analyzing related file {related_file.path}: {e}")
            return {'evidence': [], 'confidence_adjustment': 0}
    
    def _build_related_file_analysis_prompt(
        self, 
        original_finding: Dict[str, Any], 
        related_file: RelatedFile, 
        related_code: str
    ) -> str:
        """构建相关文件分析提示"""
        finding_type = original_finding.get('type', '')
        
        if '路径遍历' in finding_type:
            return f"""
请分析此文件是否包含以下安全控制：
1. 路径验证和过滤机制
2. 白名单目录限制
3. 文件上传安全配置
4. 权限验证机制

重点关注是否有代码可以缓解路径遍历风险。
"""
        elif 'XSS' in finding_type:
            return f"""
请分析此文件是否包含以下安全控制：
1. 输出转义和过滤
2. CSP (Content Security Policy) 配置
3. XSS防护机制
4. 输入验证

重点关注是否有代码可以防止XSS攻击。
"""
        else:
            return f"""
请分析此文件是否包含与{finding_type}相关的安全控制机制。
"""
    
    def _extract_evidence_from_findings(
        self, 
        findings: List[Dict], 
        original_finding: Dict
    ) -> Dict[str, Any]:
        """从相关文件的发现中提取证据"""
        evidence = []
        confidence_adjustment = 0
        
        original_type = original_finding.get('type', '')
        
        for finding in findings:
            finding_type = finding.get('type', '')
            
            # 如果相关文件中发现了相同类型的问题，增加置信度
            if finding_type == original_type:
                confidence_adjustment += 0.2
                evidence.append(f"相关文件中发现相同类型问题: {finding.get('description', '')[:100]}")
            
            # 如果相关文件中发现了安全控制，降低置信度
            elif '安全' in finding.get('description', '') or '验证' in finding.get('description', ''):
                confidence_adjustment -= 0.1
                evidence.append(f"相关文件中发现安全控制: {finding.get('description', '')[:100]}")
        
        return {
            'evidence': evidence,
            'confidence_adjustment': confidence_adjustment
        }
    
    def _calculate_adjusted_confidence(
        self, 
        original_confidence: float, 
        adjustments: List[float]
    ) -> float:
        """计算调整后的置信度"""
        total_adjustment = sum(adjustments)
        adjusted = original_confidence + total_adjustment
        return max(0.1, min(1.0, adjusted))
    
    def _generate_recommendation(
        self, 
        finding: Dict[str, Any], 
        evidence: List[str], 
        original_confidence: float, 
        adjusted_confidence: float
    ) -> str:
        """生成建议"""
        if adjusted_confidence > original_confidence + 0.1:
            return f"跨文件分析增加了问题的置信度 ({original_confidence:.2f} → {adjusted_confidence:.2f})，建议优先修复"
        elif adjusted_confidence < original_confidence - 0.1:
            return f"跨文件分析降低了问题的置信度 ({original_confidence:.2f} → {adjusted_confidence:.2f})，可能存在安全控制"
        else:
            return "跨文件分析未显著改变置信度，建议进一步人工审查"
    
    def _search_files_containing(self, pattern: str) -> List[str]:
        """优化的文件搜索，避免全项目扫描"""
        found_files = []

        # 检查搜索缓存
        if hasattr(self, 'search_cache') and pattern in self.search_cache:
            logger.info(f"Using cached search result for pattern '{pattern}'")
            return self.search_cache[pattern]

        # 1. 限制搜索范围和文件类型
        search_extensions = {'.php', '.java', '.py', '.js', '.html', '.jsp', '.xml'}
        max_search_files = 100  # 限制搜索文件数量
        max_results = 5  # 限制结果数量

        searched_count = 0

        try:
            for file_path in self.project_path.rglob('*'):
                if searched_count >= max_search_files:
                    break

                if not file_path.is_file() or file_path.suffix not in search_extensions:
                    continue

                # 跳过大文件
                try:
                    if file_path.stat().st_size > 500 * 1024:  # 500KB限制
                        continue
                except:
                    continue

                searched_count += 1

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # 只读取前10KB内容进行搜索
                        content = f.read(10240)
                        if pattern in content:
                            found_files.append(str(file_path))
                            if len(found_files) >= max_results:
                                break
                except:
                    continue

        except Exception as e:
            logger.warning(f"File search failed: {e}")

        # 缓存搜索结果
        if not hasattr(self, 'search_cache'):
            self.search_cache = {}
        self.search_cache[pattern] = found_files

        logger.info(f"Searched {searched_count} files, found {len(found_files)} matches for pattern '{pattern}'")
        return found_files

    def _generate_cache_key(self, finding: Dict[str, Any], file_path: str) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{file_path}:{finding.get('type', '')}:{finding.get('line', 0)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _resolve_file_path(self, current_file: str, relative_path: str) -> List[Path]:
        """解析相对文件路径"""
        current_path = Path(current_file)
        possible_paths = []
        
        # 相对于当前文件
        possible_paths.append(current_path.parent / relative_path)
        
        # 相对于项目根目录
        possible_paths.append(self.project_path / relative_path)
        
        # 添加常见扩展名
        for path in possible_paths.copy():
            if not path.suffix:
                for ext in ['.php', '.html', '.js', '.py']:
                    possible_paths.append(path.with_suffix(ext))
        
        return [p for p in possible_paths if p.exists()]
    
    def _detect_language(self, file_path: str) -> str:
        """检测文件语言"""
        extension = Path(file_path).suffix.lower()
        language_map = {
            '.php': 'php',
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.xml': 'xml'
        }
        return language_map.get(extension, 'unknown')
