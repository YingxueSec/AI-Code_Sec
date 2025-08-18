# 增强审计策略 - 核心处理机制

## 1. 会话隔离机制

### 设计原理
每个功能点使用独立的上下文线程，避免信息污染和上下文混乱。

### 实现方案

#### 会话隔离架构
```python
class IsolatedAuditSession:
    def __init__(self, module_name: str, project_summary: ProjectSummary):
        self.session_id = f"{module_name}_{uuid.uuid4()}"
        self.module_name = module_name
        self.project_summary = project_summary  # 共享项目摘要
        self.context_history = []
        self.evidence_chain = []
        self.isolation_boundary = set()  # 隔离边界
    
    def create_isolated_context(self) -> AuditContext:
        """创建隔离的审计上下文"""
        return AuditContext(
            session_id=self.session_id,
            module_focus=self.module_name,
            shared_resources={
                'project_summary': self.project_summary,
                'code_index': self.project_summary.code_index,
                'security_rules': self.project_summary.security_rules
            },
            isolation_scope=self.isolation_boundary
        )
```

#### 共享资源管理
```python
class SharedProjectResources:
    def __init__(self):
        self.project_summary = None
        self.code_index = None
        self.security_rules = None
        self.dependency_graph = None
    
    def get_minimal_shared_context(self, module_name: str) -> dict:
        """获取最小共享上下文"""
        return {
            'project_overview': self.project_summary.overview,
            'module_boundaries': self.project_summary.get_module_boundaries(module_name),
            'relevant_rules': self.security_rules.get_rules_for_module(module_name),
            'dependency_subset': self.dependency_graph.get_module_dependencies(module_name)
        }
```

## 2. 最小充分集取证机制

### 智能文件检索流程
```python
class MinimalEvidenceRetriever:
    def __init__(self, semantic_analyzer, call_graph, code_slicer):
        self.semantic_analyzer = semantic_analyzer
        self.call_graph = call_graph
        self.code_slicer = code_slicer
        self.evidence_cache = {}
    
    async def retrieve_evidence(self, llm_request: CodeRequest) -> EvidenceSet:
        """最小充分集取证流程"""
        
        # 1. LLM请求解析
        request_intent = await self.parse_request_intent(llm_request)
        
        # 2. 语义/调用图检索
        candidate_files = await self.semantic_call_graph_search(request_intent)
        
        # 3. 代码切片返回（带行号）
        code_slices = await self.slice_relevant_code(candidate_files, request_intent)
        
        # 4. 污点与异常路径验证
        validated_evidence = await self.validate_taint_paths(code_slices, request_intent)
        
        # 5. 充分性检查
        if not self.is_evidence_sufficient(validated_evidence, request_intent):
            additional_evidence = await self.pull_additional_evidence(validated_evidence, request_intent)
            validated_evidence.extend(additional_evidence)
        
        return EvidenceSet(
            primary_evidence=validated_evidence,
            confidence_score=self.calculate_confidence(validated_evidence),
            completeness_score=self.calculate_completeness(validated_evidence, request_intent)
        )
    
    async def semantic_call_graph_search(self, intent: RequestIntent) -> List[FileCandidate]:
        """语义和调用图联合检索"""
        
        # 语义相似度搜索
        semantic_matches = await self.semantic_analyzer.find_similar_code(
            intent.target_function,
            intent.context_keywords,
            threshold=0.7
        )
        
        # 调用图路径搜索
        call_paths = self.call_graph.find_paths_to_target(
            intent.target_function,
            max_depth=intent.context_depth
        )
        
        # 合并和排序候选文件
        candidates = self.merge_and_rank_candidates(semantic_matches, call_paths)
        
        return candidates[:intent.max_files]  # 限制文件数量
    
    async def slice_relevant_code(self, candidates: List[FileCandidate], intent: RequestIntent) -> List[CodeSlice]:
        """精确代码切片提取"""
        slices = []
        
        for candidate in candidates:
            # 基于意图的智能切片
            relevant_slices = await self.code_slicer.extract_slices(
                file_path=candidate.file_path,
                target_symbols=intent.target_symbols,
                context_lines=intent.context_lines,
                include_dependencies=True
            )
            
            # 添加行号和文件信息
            for slice_obj in relevant_slices:
                slice_obj.add_metadata({
                    'file_path': candidate.file_path,
                    'start_line': slice_obj.start_line,
                    'end_line': slice_obj.end_line,
                    'relevance_score': candidate.relevance_score
                })
            
            slices.extend(relevant_slices)
        
        return sorted(slices, key=lambda x: x.relevance_score, reverse=True)
    
    async def validate_taint_paths(self, slices: List[CodeSlice], intent: RequestIntent) -> List[ValidatedEvidence]:
        """污点分析和异常路径验证"""
        validated = []
        
        for slice_obj in slices:
            # 污点分析
            taint_analysis = await self.perform_taint_analysis(slice_obj, intent.security_focus)
            
            # 异常路径检查
            exception_paths = await self.check_exception_paths(slice_obj)
            
            # 数据流验证
            data_flow_valid = await self.validate_data_flow(slice_obj, intent.data_flow_requirements)
            
            if taint_analysis.has_issues or exception_paths.has_vulnerabilities or data_flow_valid.has_concerns:
                validated.append(ValidatedEvidence(
                    code_slice=slice_obj,
                    taint_results=taint_analysis,
                    exception_analysis=exception_paths,
                    data_flow_analysis=data_flow_valid,
                    validation_confidence=self.calculate_validation_confidence(
                        taint_analysis, exception_paths, data_flow_valid
                    )
                ))
        
        return validated
```

## 3. 覆盖率控制机制

### 待办矩阵管理
```python
class CoverageController:
    def __init__(self):
        self.coverage_matrix = {}  # {module: {topic: status}}
        self.high_risk_topics = [
            'authentication', 'authorization', 'input_validation',
            'sql_injection', 'xss', 'csrf', 'file_upload',
            'session_management', 'crypto_usage', 'error_handling'
        ]
        self.audit_queue = PriorityQueue()
    
    def initialize_coverage_matrix(self, project_modules: List[Module]):
        """初始化覆盖率矩阵"""
        for module in project_modules:
            self.coverage_matrix[module.name] = {}
            
            # 为每个模块分配相关的高危主题
            relevant_topics = self.identify_relevant_topics(module)
            
            for topic in relevant_topics:
                self.coverage_matrix[module.name][topic] = {
                    'status': 'pending',
                    'priority': self.calculate_topic_priority(module, topic),
                    'attempts': 0,
                    'last_attempt': None,
                    'evidence_quality': 0.0
                }
    
    def get_uncovered_items(self) -> List[AuditTask]:
        """获取未覆盖的审计项"""
        uncovered = []
        
        for module_name, topics in self.coverage_matrix.items():
            for topic, status_info in topics.items():
                if status_info['status'] in ['pending', 'failed', 'insufficient']:
                    uncovered.append(AuditTask(
                        module=module_name,
                        topic=topic,
                        priority=status_info['priority'],
                        retry_count=status_info['attempts']
                    ))
        
        return sorted(uncovered, key=lambda x: x.priority, reverse=True)
    
    def update_coverage_status(self, module: str, topic: str, result: AuditResult):
        """更新覆盖状态"""
        if module in self.coverage_matrix and topic in self.coverage_matrix[module]:
            status_info = self.coverage_matrix[module][topic]
            
            # 根据审计结果更新状态
            if result.confidence_score >= 0.8 and result.evidence_quality >= 0.7:
                status_info['status'] = 'completed'
            elif result.confidence_score >= 0.6:
                status_info['status'] = 'partial'
            else:
                status_info['status'] = 'insufficient'
                # 重新排队
                self.requeue_audit_task(module, topic, status_info['attempts'] + 1)
            
            status_info['attempts'] += 1
            status_info['last_attempt'] = datetime.now()
            status_info['evidence_quality'] = result.evidence_quality
    
    def auto_queue_uncovered_items(self):
        """自动排队未覆盖项"""
        uncovered = self.get_uncovered_items()
        
        for task in uncovered:
            # 计算延迟时间（避免频繁重试）
            delay = min(2 ** task.retry_count, 3600)  # 指数退避，最大1小时
            
            self.audit_queue.put((
                task.priority,
                datetime.now() + timedelta(seconds=delay),
                task
            ))
```

## 4. 幻觉与重复防护机制

### 强制行号引用与代码证据
```python
class HallucinationGuard:
    def __init__(self):
        self.evidence_validator = EvidenceValidator()
        self.request_deduplicator = RequestDeduplicator()
        self.fallback_strategies = FallbackStrategies()
    
    async def validate_llm_response(self, response: LLMResponse, evidence: EvidenceSet) -> ValidationResult:
        """验证LLM响应的真实性"""
        
        validation_results = []
        
        # 1. 强制行号引用检查
        line_ref_validation = await self.validate_line_references(response, evidence)
        validation_results.append(line_ref_validation)
        
        # 2. 代码证据一致性检查
        code_consistency = await self.validate_code_consistency(response, evidence)
        validation_results.append(code_consistency)
        
        # 3. 逻辑一致性检查
        logic_consistency = await self.validate_logic_consistency(response)
        validation_results.append(logic_consistency)
        
        return ValidationResult(
            is_valid=all(v.is_valid for v in validation_results),
            confidence_score=sum(v.confidence for v in validation_results) / len(validation_results),
            validation_details=validation_results
        )
    
    async def validate_line_references(self, response: LLMResponse, evidence: EvidenceSet) -> LineRefValidation:
        """验证行号引用的准确性"""
        
        referenced_lines = self.extract_line_references(response.content)
        validation_errors = []
        
        for line_ref in referenced_lines:
            # 检查文件是否存在于证据集中
            if not evidence.contains_file(line_ref.file_path):
                validation_errors.append(f"引用了不存在的文件: {line_ref.file_path}")
                continue
            
            # 检查行号是否在有效范围内
            file_evidence = evidence.get_file_evidence(line_ref.file_path)
            if not file_evidence.contains_line(line_ref.line_number):
                validation_errors.append(f"引用了无效的行号: {line_ref.file_path}:{line_ref.line_number}")
                continue
            
            # 检查引用的代码内容是否匹配
            actual_code = file_evidence.get_line_content(line_ref.line_number)
            if line_ref.quoted_code and not self.code_matches(actual_code, line_ref.quoted_code):
                validation_errors.append(f"引用的代码内容不匹配: {line_ref.file_path}:{line_ref.line_number}")
        
        return LineRefValidation(
            is_valid=len(validation_errors) == 0,
            confidence=1.0 - (len(validation_errors) / max(len(referenced_lines), 1)),
            errors=validation_errors
        )
    
    def deduplicate_requests(self, new_request: CodeRequest, session_history: List[CodeRequest]) -> DeduplicationResult:
        """请求去重处理"""
        
        similar_requests = []
        
        for historical_request in session_history:
            similarity = self.calculate_request_similarity(new_request, historical_request)
            
            if similarity > 0.8:  # 高相似度阈值
                similar_requests.append({
                    'request': historical_request,
                    'similarity': similarity,
                    'timestamp': historical_request.timestamp
                })
        
        if similar_requests:
            # 找到最相似的请求
            most_similar = max(similar_requests, key=lambda x: x['similarity'])
            
            # 如果时间间隔很短，直接返回缓存结果
            time_diff = datetime.now() - most_similar['timestamp']
            if time_diff.total_seconds() < 300:  # 5分钟内
                return DeduplicationResult(
                    is_duplicate=True,
                    cached_result=most_similar['request'].cached_response,
                    reason="Recent similar request found"
                )
        
        return DeduplicationResult(is_duplicate=False)
    
    async def apply_fallback_strategy(self, failed_request: CodeRequest, failure_reason: str) -> FallbackResult:
        """失败策略处理"""
        
        fallback_strategies = [
            ('switch_model', self.try_alternative_model),
            ('change_retrieval', self.try_alternative_retrieval),
            ('simplify_request', self.simplify_request_scope),
            ('manual_intervention', self.request_manual_review)
        ]
        
        for strategy_name, strategy_func in fallback_strategies:
            try:
                result = await strategy_func(failed_request, failure_reason)
                if result.success:
                    return FallbackResult(
                        success=True,
                        strategy_used=strategy_name,
                        result=result,
                        confidence=result.confidence * 0.8  # 降低置信度
                    )
            except Exception as e:
                continue  # 尝试下一个策略
        
        return FallbackResult(
            success=False,
            reason="All fallback strategies failed",
            requires_manual_intervention=True
        )
```

## 5. 集成实现示例

### 完整的审计会话管理
```python
class EnhancedAuditSessionManager:
    def __init__(self):
        self.session_isolator = SessionIsolator()
        self.evidence_retriever = MinimalEvidenceRetriever()
        self.coverage_controller = CoverageController()
        self.hallucination_guard = HallucinationGuard()
    
    async def conduct_enhanced_audit(self, module: Module, project_summary: ProjectSummary) -> EnhancedAuditResult:
        """执行增强的审计流程"""
        
        # 1. 创建隔离会话
        isolated_session = self.session_isolator.create_isolated_session(module.name, project_summary)
        
        # 2. 初始化覆盖率矩阵
        audit_tasks = self.coverage_controller.get_uncovered_items_for_module(module.name)
        
        results = []
        
        for task in audit_tasks:
            try:
                # 3. 最小充分集取证
                evidence = await self.evidence_retriever.retrieve_evidence(task.to_code_request())
                
                # 4. 请求去重检查
                dedup_result = self.hallucination_guard.deduplicate_requests(
                    task.to_code_request(), 
                    isolated_session.get_request_history()
                )
                
                if dedup_result.is_duplicate:
                    results.append(dedup_result.cached_result)
                    continue
                
                # 5. LLM审计执行
                llm_response = await isolated_session.execute_audit(evidence, task)
                
                # 6. 幻觉防护验证
                validation = await self.hallucination_guard.validate_llm_response(llm_response, evidence)
                
                if validation.is_valid:
                    # 7. 更新覆盖率状态
                    self.coverage_controller.update_coverage_status(
                        module.name, 
                        task.topic, 
                        llm_response.to_audit_result()
                    )
                    results.append(llm_response.to_audit_result())
                else:
                    # 8. 应用失败策略
                    fallback_result = await self.hallucination_guard.apply_fallback_strategy(
                        task.to_code_request(), 
                        validation.failure_reason
                    )
                    results.append(fallback_result.to_audit_result())
                    
            except Exception as e:
                # 记录失败并继续下一个任务
                self.coverage_controller.mark_task_failed(module.name, task.topic, str(e))
                continue
        
        # 9. 自动排队未完成项
        self.coverage_controller.auto_queue_uncovered_items()
        
        return EnhancedAuditResult(
            module=module,
            results=results,
            coverage_report=self.coverage_controller.generate_coverage_report(module.name),
            session_summary=isolated_session.get_session_summary()
        )
```

这个增强策略完全包含了您提到的四个核心机制，确保审计过程的准确性、完整性和可靠性。
