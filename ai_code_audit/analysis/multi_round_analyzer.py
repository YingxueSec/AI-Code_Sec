"""
Multi-Round Analysis Engine
多轮分析引擎 - 渐进式深度安全分析
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ..core.models import FileInfo, AnalysisResult
from ..llm.client import LLMClient
from ..llm.prompts import PromptManager
from ..detection.advanced_patterns import AdvancedPatternDetector

logger = logging.getLogger(__name__)


class AnalysisRound(Enum):
    """分析轮次"""
    QUICK_SCAN = "quick_scan"           # 快速扫描
    DEEP_ANALYSIS = "deep_analysis"     # 深度分析
    EXPERT_REVIEW = "expert_review"     # 专家级审查
    CROSS_FILE = "cross_file"           # 跨文件分析
    BUSINESS_LOGIC = "business_logic"   # 业务逻辑分析


@dataclass
class RoundResult:
    """单轮分析结果"""
    round_type: AnalysisRound
    findings: List[Dict]
    confidence_score: float
    analysis_time: float
    tokens_used: int
    suspicious_areas: List[Dict]


class MultiRoundAnalyzer:
    """多轮分析引擎"""
    
    def __init__(self, llm_client: LLMClient, prompt_manager: PromptManager):
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.pattern_detector = AdvancedPatternDetector()
        self.analysis_history = []
        
        # 分析阈值配置
        self.thresholds = {
            "suspicious_score": 0.6,      # 可疑度阈值
            "critical_file_score": 0.8,   # 关键文件阈值
            "deep_analysis_trigger": 0.7, # 深度分析触发阈值
            "expert_review_trigger": 0.9  # 专家审查触发阈值
        }
    
    async def analyze_with_multiple_rounds(
        self, 
        files: List[FileInfo], 
        max_rounds: int = 4
    ) -> Dict[str, Any]:
        """执行多轮分析"""
        logger.info(f"开始多轮分析，文件数量: {len(files)}, 最大轮次: {max_rounds}")
        
        results = {
            "rounds": [],
            "consolidated_findings": [],
            "analysis_metadata": {
                "total_files": len(files),
                "rounds_executed": 0,
                "total_tokens": 0,
                "total_time": 0
            }
        }
        
        # 第一轮：快速模式扫描
        round1_result = await self._round1_quick_scan(files)
        results["rounds"].append(round1_result)
        results["analysis_metadata"]["rounds_executed"] += 1
        
        # 根据第一轮结果决定是否进行后续分析
        high_risk_files = self._identify_high_risk_files(files, round1_result)
        
        if high_risk_files and max_rounds > 1:
            # 第二轮：深度AI分析
            round2_result = await self._round2_deep_analysis(high_risk_files, round1_result)
            results["rounds"].append(round2_result)
            results["analysis_metadata"]["rounds_executed"] += 1
            
            if self._should_continue_analysis(round2_result) and max_rounds > 2:
                # 第三轮：跨文件关联分析
                round3_result = await self._round3_cross_file_analysis(files, round2_result)
                results["rounds"].append(round3_result)
                results["analysis_metadata"]["rounds_executed"] += 1
                
                if self._needs_expert_review(round3_result) and max_rounds > 3:
                    # 第四轮：专家级业务逻辑分析
                    round4_result = await self._round4_expert_business_logic(files, round3_result)
                    results["rounds"].append(round4_result)
                    results["analysis_metadata"]["rounds_executed"] += 1
        
        # 整合所有轮次的结果
        results["consolidated_findings"] = self._consolidate_findings(results["rounds"])
        results["analysis_metadata"]["total_tokens"] = sum(r.tokens_used for r in results["rounds"])
        results["analysis_metadata"]["total_time"] = sum(r.analysis_time for r in results["rounds"])
        
        logger.info(f"多轮分析完成，执行轮次: {results['analysis_metadata']['rounds_executed']}")
        return results
    
    async def _round1_quick_scan(self, files: List[FileInfo]) -> RoundResult:
        """第一轮：快速模式扫描"""
        logger.info("执行第一轮：快速模式扫描")
        import time
        start_time = time.time()
        
        findings = []
        suspicious_areas = []
        
        for file_info in files:
            try:
                # 读取文件内容
                with open(file_info.absolute_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用高级模式检测器
                pattern_findings = self.pattern_detector.detect_advanced_vulnerabilities(
                    content, file_info.path
                )
                findings.extend(pattern_findings)
                
                # 业务逻辑上下文分析
                business_findings = self.pattern_detector.analyze_business_logic_context(
                    content, file_info.path
                )
                findings.extend(business_findings)
                
                # 计算文件可疑度
                suspicious_score = self._calculate_file_suspicion_score(pattern_findings + business_findings)
                if suspicious_score > self.thresholds["suspicious_score"]:
                    suspicious_areas.append({
                        "file": file_info.path,
                        "score": suspicious_score,
                        "reasons": [f["type"] for f in pattern_findings + business_findings]
                    })
                
            except Exception as e:
                logger.error(f"第一轮分析文件 {file_info.path} 时出错: {e}")
        
        analysis_time = time.time() - start_time
        
        return RoundResult(
            round_type=AnalysisRound.QUICK_SCAN,
            findings=findings,
            confidence_score=0.8,  # 模式匹配的置信度较高
            analysis_time=analysis_time,
            tokens_used=0,  # 模式匹配不使用tokens
            suspicious_areas=suspicious_areas
        )
    
    async def _round2_deep_analysis(
        self, 
        high_risk_files: List[FileInfo], 
        round1_result: RoundResult
    ) -> RoundResult:
        """第二轮：深度AI分析"""
        logger.info(f"执行第二轮：深度AI分析，文件数量: {len(high_risk_files)}")
        import time
        start_time = time.time()
        
        findings = []
        total_tokens = 0
        
        # 获取增强的安全审计模板
        template = self.prompt_manager.get_template("security_audit_enhanced")
        if not template:
            template = self.prompt_manager.get_template("security_audit")
        
        for file_info in high_risk_files:
            try:
                # 读取文件内容
                with open(file_info.absolute_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 构建增强的上下文信息
                round1_findings = [f for f in round1_result.findings if f.get("location", {}).get("file") == file_info.path]
                context = self._build_enhanced_context(file_info, round1_findings)
                
                # 生成深度分析提示
                prompt = template.format_prompt(
                    language=file_info.language or 'python',
                    file_path=file_info.path,
                    project_type='web_application',
                    dependencies='flask, sqlite3, subprocess',
                    code_content=content,
                    additional_context=context
                )
                
                # 执行AI分析
                response = await self.llm_client.generate_response(
                    prompt.system_prompt,
                    prompt.user_prompt,
                    temperature=0.05,  # 更低的温度以提高准确性
                    max_tokens=4096
                )
                
                # 解析AI响应
                ai_findings = self._parse_ai_response(response, file_info.path)
                findings.extend(ai_findings)
                total_tokens += len(response.split())  # 简单的token估算
                
            except Exception as e:
                logger.error(f"第二轮分析文件 {file_info.path} 时出错: {e}")
        
        analysis_time = time.time() - start_time
        
        return RoundResult(
            round_type=AnalysisRound.DEEP_ANALYSIS,
            findings=findings,
            confidence_score=0.9,  # AI分析的置信度很高
            analysis_time=analysis_time,
            tokens_used=total_tokens,
            suspicious_areas=[]
        )
    
    async def _round3_cross_file_analysis(
        self, 
        files: List[FileInfo], 
        round2_result: RoundResult
    ) -> RoundResult:
        """第三轮：跨文件关联分析"""
        logger.info("执行第三轮：跨文件关联分析")
        import time
        start_time = time.time()
        
        findings = []
        
        # 构建文件依赖图
        dependency_graph = self._build_dependency_graph(files)
        
        # 分析跨文件漏洞链
        vulnerability_chains = self._analyze_vulnerability_chains(
            dependency_graph, 
            round2_result.findings
        )
        
        # 转换为标准格式
        for chain in vulnerability_chains:
            findings.append({
                "type": "cross_file_vulnerability_chain",
                "severity": chain["severity"],
                "description": chain["description"],
                "files_involved": chain["files"],
                "attack_path": chain["path"],
                "business_impact": chain["impact"],
                "remediation": "实施跨模块的安全验证和数据流控制"
            })
        
        analysis_time = time.time() - start_time
        
        return RoundResult(
            round_type=AnalysisRound.CROSS_FILE,
            findings=findings,
            confidence_score=0.85,
            analysis_time=analysis_time,
            tokens_used=0,
            suspicious_areas=[]
        )
    
    async def _round4_expert_business_logic(
        self, 
        files: List[FileInfo], 
        round3_result: RoundResult
    ) -> RoundResult:
        """第四轮：专家级业务逻辑分析"""
        logger.info("执行第四轮：专家级业务逻辑分析")
        import time
        start_time = time.time()
        
        findings = []
        total_tokens = 0
        
        # 专家级业务逻辑分析提示
        expert_prompt = self._create_expert_business_logic_prompt()
        
        # 分析关键业务逻辑文件
        business_critical_files = [f for f in files if self._is_business_critical(f)]
        
        for file_info in business_critical_files:
            try:
                with open(file_info.absolute_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 构建专家级分析上下文
                expert_context = self._build_expert_context(file_info, round3_result.findings)
                
                # 执行专家级AI分析
                response = await self.llm_client.generate_response(
                    expert_prompt,
                    f"""
                    文件: {file_info.path}
                    上下文: {expert_context}
                    
                    代码:
                    ```python
                    {content}
                    ```
                    
                    请进行专家级业务逻辑安全分析。
                    """,
                    temperature=0.02,  # 极低温度确保准确性
                    max_tokens=3072
                )
                
                expert_findings = self._parse_expert_response(response, file_info.path)
                findings.extend(expert_findings)
                total_tokens += len(response.split())
                
            except Exception as e:
                logger.error(f"第四轮分析文件 {file_info.path} 时出错: {e}")
        
        analysis_time = time.time() - start_time
        
        return RoundResult(
            round_type=AnalysisRound.BUSINESS_LOGIC,
            findings=findings,
            confidence_score=0.95,  # 专家级分析置信度最高
            analysis_time=analysis_time,
            tokens_used=total_tokens,
            suspicious_areas=[]
        )
    
    def _identify_high_risk_files(self, files: List[FileInfo], round1_result: RoundResult) -> List[FileInfo]:
        """识别高风险文件"""
        high_risk_files = []
        
        # 基于第一轮结果识别高风险文件
        suspicious_file_paths = {area["file"] for area in round1_result.suspicious_areas}
        
        for file_info in files:
            if (file_info.path in suspicious_file_paths or 
                self._is_critical_file(file_info) or
                self._has_high_severity_findings(file_info.path, round1_result.findings)):
                high_risk_files.append(file_info)
        
        return high_risk_files
    
    def _calculate_file_suspicion_score(self, findings: List[Dict]) -> float:
        """计算文件可疑度分数"""
        if not findings:
            return 0.0
        
        score = 0.0
        for finding in findings:
            severity = finding.get("severity", "low")
            if severity == "critical":
                score += 0.4
            elif severity == "high":
                score += 0.3
            elif severity == "medium":
                score += 0.2
            else:
                score += 0.1
        
        return min(score, 1.0)
    
    def _build_enhanced_context(self, file_info: FileInfo, round1_findings: List[Dict]) -> str:
        """构建增强的分析上下文"""
        context_parts = [
            f"文件 {file_info.path} 的深度安全分析",
            f"第一轮扫描发现 {len(round1_findings)} 个潜在问题："
        ]
        
        for finding in round1_findings[:5]:  # 只显示前5个
            context_parts.append(f"- {finding.get('type', 'unknown')}: {finding.get('description', '')}")
        
        context_parts.append("请进行更深入的分析，特别关注业务逻辑漏洞和复杂攻击场景。")
        
        return "\n".join(context_parts)
    
    def _should_continue_analysis(self, round_result: RoundResult) -> bool:
        """判断是否应该继续分析"""
        # 如果发现了高严重性漏洞，继续分析
        critical_findings = [f for f in round_result.findings if f.get("severity") == "critical"]
        return len(critical_findings) > 0 or round_result.confidence_score > self.thresholds["deep_analysis_trigger"]
    
    def _needs_expert_review(self, round_result: RoundResult) -> bool:
        """判断是否需要专家级审查"""
        return round_result.confidence_score > self.thresholds["expert_review_trigger"]
    
    def _is_critical_file(self, file_info: FileInfo) -> bool:
        """判断是否为关键文件"""
        critical_patterns = ['auth', 'login', 'admin', 'payment', 'security', 'database']
        return any(pattern in file_info.path.lower() for pattern in critical_patterns)
    
    def _is_business_critical(self, file_info: FileInfo) -> bool:
        """判断是否为业务关键文件"""
        business_patterns = ['auth', 'payment', 'order', 'user', 'admin', 'workflow']
        return any(pattern in file_info.path.lower() for pattern in business_patterns)
    
    def _has_high_severity_findings(self, file_path: str, findings: List[Dict]) -> bool:
        """检查文件是否有高严重性发现"""
        file_findings = [f for f in findings if f.get("location", {}).get("file") == file_path]
        return any(f.get("severity") in ["critical", "high"] for f in file_findings)
    
    def _build_dependency_graph(self, files: List[FileInfo]) -> Dict:
        """构建文件依赖图"""
        # 简化的依赖图构建
        graph = {"nodes": [], "edges": []}
        
        for file_info in files:
            graph["nodes"].append(file_info.path)
            
            # 这里可以实现更复杂的依赖分析
            # 例如分析import语句、函数调用等
        
        return graph
    
    def _analyze_vulnerability_chains(self, dependency_graph: Dict, findings: List[Dict]) -> List[Dict]:
        """分析漏洞链"""
        chains = []
        
        # 简化的漏洞链分析
        # 在实际实现中，这里会有更复杂的逻辑
        
        return chains
    
    def _create_expert_business_logic_prompt(self) -> str:
        """创建专家级业务逻辑分析提示"""
        return """你是一位拥有20年经验的高级安全架构师和业务逻辑安全专家。

🎯 专家级业务逻辑安全分析任务：

重点关注以下高级安全问题：

1. **工作流安全缺陷**：
   - 步骤跳过和绕过
   - 状态机的非法转换
   - 并发访问的竞态条件

2. **权限和访问控制**：
   - 垂直权限提升
   - 水平权限绕过
   - 上下文相关的访问控制缺陷

3. **业务逻辑操纵**：
   - 价格和数量操纵
   - 时间和顺序操纵
   - 业务规则绕过

4. **数据完整性**：
   - 关键业务数据的篡改
   - 审计日志的绕过
   - 数据一致性问题

请提供专家级的分析，包括具体的攻击场景和业务影响评估。"""
    
    def _build_expert_context(self, file_info: FileInfo, findings: List[Dict]) -> str:
        """构建专家级分析上下文"""
        return f"基于前期分析，文件 {file_info.path} 需要专家级业务逻辑审查。"
    
    def _parse_ai_response(self, response: str, file_path: str) -> List[Dict]:
        """解析AI响应"""
        # 简化的响应解析
        # 实际实现中需要更复杂的解析逻辑
        return [{
            "type": "ai_detected_vulnerability",
            "severity": "medium",
            "description": "AI检测到的潜在安全问题",
            "file": file_path,
            "raw_response": response[:200] + "..." if len(response) > 200 else response
        }]
    
    def _parse_expert_response(self, response: str, file_path: str) -> List[Dict]:
        """解析专家级响应"""
        return [{
            "type": "expert_business_logic_finding",
            "severity": "high",
            "description": "专家级业务逻辑分析发现",
            "file": file_path,
            "expert_analysis": response[:300] + "..." if len(response) > 300 else response
        }]
    
    def _consolidate_findings(self, rounds: List[RoundResult]) -> List[Dict]:
        """整合所有轮次的发现"""
        all_findings = []
        
        for round_result in rounds:
            for finding in round_result.findings:
                finding["analysis_round"] = round_result.round_type.value
                finding["confidence"] = round_result.confidence_score
                all_findings.append(finding)
        
        # 去重和优先级排序
        return self._deduplicate_and_prioritize(all_findings)
    
    def _deduplicate_and_prioritize(self, findings: List[Dict]) -> List[Dict]:
        """去重和优先级排序"""
        # 简化的去重逻辑
        seen = set()
        unique_findings = []
        
        # 按严重性排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        for finding in findings:
            key = f"{finding.get('type', '')}_{finding.get('file', '')}"
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)
        
        return unique_findings
