"""
LLM Manager for AI Code Audit System.

This module provides a unified interface for managing multiple LLM providers
and handling load balancing, fallback, and cost optimization.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
import random

from ai_code_audit.llm.base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMModelType, MessageRole
)
from ai_code_audit.llm.qwen_provider import QwenProvider
from ai_code_audit.llm.kimi_provider import KimiProvider
from ai_code_audit.llm.concurrency_manager import AdaptiveConcurrencyManager, ConcurrencyContext
from ai_code_audit.llm.rate_limiter import get_rate_limiter
from ai_code_audit.core.exceptions import LLMError, ConfigurationError

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for multiple providers."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""
    provider_type: str
    api_key: str
    base_url: Optional[str] = None
    enabled: bool = True
    priority: int = 1
    max_requests_per_minute: int = 60
    cost_weight: float = 1.0
    performance_weight: float = 1.0


class LLMManager:
    """Manages multiple LLM providers with load balancing and fallback."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM manager.
        
        Args:
            config: Optional configuration dict, will load from app config if not provided
        """
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.provider_configs: Dict[str, ProviderConfig] = {}
        self.request_counts: Dict[str, int] = {}
        self.last_used_provider: Optional[str] = None
        self.load_balancing_strategy = LoadBalancingStrategy.COST_OPTIMIZED

        # 初始化并发管理器
        if config:
            max_parallel = config.get('performance', {}).get('max_parallel_requests', 10)
        else:
            max_parallel = 10
        self.concurrency_manager = AdaptiveConcurrencyManager(
            initial_concurrency=max_parallel,
            min_concurrency=max(1, max_parallel // 3),  # 最小并发为初始值的1/3
            max_concurrency=min(max_parallel * 2, 25)   # 基于TPM限制，最大25个并发
        )

        # 初始化分析器 (延迟导入避免循环依赖)
        self.confidence_calculator = None
        self.context_analyzer = None
        self.cross_file_analyzer = None
        self.project_path = None  # 用于跨文件分析
        
        # Load configuration
        if config is None:
            config = self._get_default_config()
        
        self._load_providers(config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration from config system."""
        from ai_code_audit.core.config import get_config

        app_config = get_config()

        config = {'llm': {}}

        if app_config.llm.qwen and app_config.llm.qwen.api_key:
            config['llm']['qwen'] = {
                'api_key': app_config.llm.qwen.api_key,
                'base_url': app_config.llm.qwen.base_url,
                'enabled': app_config.llm.qwen.enabled,
                'priority': app_config.llm.qwen.priority,
                'max_requests_per_minute': app_config.llm.qwen.max_requests_per_minute,
                'cost_weight': app_config.llm.qwen.cost_weight,
                'performance_weight': app_config.llm.qwen.performance_weight,
            }

        if app_config.llm.kimi and app_config.llm.kimi.api_key:
            config['llm']['kimi'] = {
                'api_key': app_config.llm.kimi.api_key,
                'base_url': app_config.llm.kimi.base_url,
                'enabled': app_config.llm.kimi.enabled,
                'priority': app_config.llm.kimi.priority,
                'max_requests_per_minute': app_config.llm.kimi.max_requests_per_minute,
                'cost_weight': app_config.llm.kimi.cost_weight,
                'performance_weight': app_config.llm.kimi.performance_weight,
            }

        return config
    
    def _load_providers(self, config: Dict[str, Any]) -> None:
        """Load and initialize LLM providers from configuration."""
        llm_config = config.get('llm', {})
        
        # Load Qwen provider
        qwen_config = llm_config.get('qwen', {})
        if qwen_config.get('api_key'):
            try:
                provider_config = ProviderConfig(
                    provider_type='qwen',
                    api_key=qwen_config['api_key'],
                    base_url=qwen_config.get('base_url'),
                    enabled=qwen_config.get('enabled', True),
                    priority=qwen_config.get('priority', 1),
                    max_requests_per_minute=qwen_config.get('max_requests_per_minute', 60),
                    cost_weight=qwen_config.get('cost_weight', 1.0),
                    performance_weight=qwen_config.get('performance_weight', 1.0),
                )
                
                if provider_config.enabled:
                    provider = QwenProvider(
                        api_key=provider_config.api_key,
                        base_url=provider_config.base_url
                    )
                    self.providers['qwen'] = provider
                    self.provider_configs['qwen'] = provider_config
                    self.request_counts['qwen'] = 0
                    logger.info("Qwen provider initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize Qwen provider: {e}")
        
        # Load Kimi provider
        kimi_config = llm_config.get('kimi', {})
        if kimi_config.get('api_key'):
            try:
                provider_config = ProviderConfig(
                    provider_type='kimi',
                    api_key=kimi_config['api_key'],
                    base_url=kimi_config.get('base_url'),
                    enabled=kimi_config.get('enabled', True),
                    priority=kimi_config.get('priority', 1),
                    max_requests_per_minute=kimi_config.get('max_requests_per_minute', 60),
                    cost_weight=kimi_config.get('cost_weight', 1.2),  # Kimi is typically more expensive
                    performance_weight=kimi_config.get('performance_weight', 1.1),  # But often faster
                )
                
                if provider_config.enabled:
                    provider = KimiProvider(
                        api_key=provider_config.api_key,
                        base_url=provider_config.base_url
                    )
                    self.providers['kimi'] = provider
                    self.provider_configs['kimi'] = provider_config
                    self.request_counts['kimi'] = 0
                    logger.info("Kimi provider initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize Kimi provider: {e}")
        
        if not self.providers:
            logger.warning("No LLM providers configured - using mock provider for testing")
            # For testing purposes, we'll continue without providers
        else:
            logger.info(f"LLM Manager initialized with {len(self.providers)} providers: {list(self.providers.keys())}")
    
    async def chat_completion(
        self, 
        request: LLMRequest, 
        preferred_provider: Optional[str] = None,
        fallback: bool = True
    ) -> LLMResponse:
        """
        Send chat completion request with automatic provider selection and fallback.
        
        Args:
            request: LLM request
            preferred_provider: Preferred provider name (optional)
            fallback: Whether to try other providers if preferred fails
            
        Returns:
            LLM response
            
        Raises:
            LLMError: If all providers fail
        """
        if not self.providers:
            raise LLMError("No LLM providers available - please configure API keys")

        # 使用并发控制
        async with ConcurrencyContext(self.concurrency_manager) as ctx:
            # Determine provider order
            provider_order = self._get_provider_order(request, preferred_provider)

            last_error = None

            for provider_name in provider_order:
                provider = self.providers.get(provider_name)
                if not provider:
                    continue

                # Check if provider supports the requested model
                if not provider.is_model_supported(request.model):
                    logger.debug(f"Provider {provider_name} does not support model {request.model.value}")
                    continue

                try:
                    logger.debug(f"Attempting request with provider: {provider_name} "
                               f"(concurrency: {self.concurrency_manager.current_concurrency})")
                    response = await provider.chat_completion(request)

                    # Update request count
                    self.request_counts[provider_name] += 1
                    self.last_used_provider = provider_name

                    # Add provider info to response metadata
                    response.metadata = response.metadata or {}
                    response.metadata['provider_used'] = provider_name

                    logger.info(f"Request completed successfully with {provider_name}")
                    return response

                except Exception as e:
                    last_error = e
                    logger.warning(f"Provider {provider_name} failed: {e}")

                    if not fallback:
                        raise

                    # Continue to next provider
                    continue
        
        # All providers failed
        if last_error:
            raise last_error
        else:
            raise LLMError("No suitable providers available for request")
    
    def _get_provider_order(self, request: LLMRequest, preferred_provider: Optional[str] = None) -> List[str]:
        """Get ordered list of providers to try for the request."""
        available_providers = []
        
        # Filter providers that support the requested model
        for name, provider in self.providers.items():
            if provider.is_model_supported(request.model):
                available_providers.append(name)
        
        if not available_providers:
            return []
        
        # If preferred provider is specified and available, try it first
        if preferred_provider and preferred_provider in available_providers:
            ordered = [preferred_provider]
            ordered.extend([p for p in available_providers if p != preferred_provider])
            return ordered
        
        # Apply load balancing strategy
        if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_order(available_providers)
        elif self.load_balancing_strategy == LoadBalancingStrategy.RANDOM:
            return self._random_order(available_providers)
        elif self.load_balancing_strategy == LoadBalancingStrategy.COST_OPTIMIZED:
            return self._cost_optimized_order(available_providers)
        elif self.load_balancing_strategy == LoadBalancingStrategy.PERFORMANCE_OPTIMIZED:
            return self._performance_optimized_order(available_providers)
        else:
            return available_providers
    
    def _round_robin_order(self, providers: List[str]) -> List[str]:
        """Round-robin provider selection."""
        if not self.last_used_provider or self.last_used_provider not in providers:
            return providers
        
        last_index = providers.index(self.last_used_provider)
        next_index = (last_index + 1) % len(providers)
        
        return providers[next_index:] + providers[:next_index]
    
    def _random_order(self, providers: List[str]) -> List[str]:
        """Random provider selection."""
        shuffled = providers.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def _cost_optimized_order(self, providers: List[str]) -> List[str]:
        """Cost-optimized provider selection (cheapest first)."""
        return sorted(providers, key=lambda p: self.provider_configs[p].cost_weight)
    
    def _performance_optimized_order(self, providers: List[str]) -> List[str]:
        """Performance-optimized provider selection (fastest first)."""
        return sorted(providers, key=lambda p: self.provider_configs[p].performance_weight)
    
    async def validate_providers(self) -> Dict[str, bool]:
        """Validate all configured providers."""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                is_valid = await provider.validate_api_key()
                results[name] = is_valid
                logger.info(f"Provider {name} validation: {'✓' if is_valid else '✗'}")
            except Exception as e:
                results[name] = False
                logger.error(f"Provider {name} validation failed: {e}")
        
        return results
    
    def get_available_models(self) -> Dict[str, List[LLMModelType]]:
        """Get available models for each provider."""
        models = {}
        
        for name, provider in self.providers.items():
            models[name] = provider.supported_models
        
        return models
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        
        for name, provider in self.providers.items():
            config = self.provider_configs[name]
            stats[name] = {
                'provider_type': config.provider_type,
                'enabled': config.enabled,
                'priority': config.priority,
                'request_count': self.request_counts[name],
                'supported_models': [model.value for model in provider.supported_models],
                'cost_weight': config.cost_weight,
                'performance_weight': config.performance_weight,
            }
        
        return stats
    
    async def close(self):
        """Close all provider connections."""
        for provider in self.providers.values():
            try:
                await provider.close()
            except Exception as e:
                logger.warning(f"Error closing provider: {e}")

    def get_concurrency_stats(self) -> Dict:
        """获取并发控制统计信息"""
        return self.concurrency_manager.get_stats()

    def get_provider_stats(self) -> Dict:
        """获取提供商统计信息"""
        return {
            "providers": list(self.providers.keys()),
            "request_counts": self.request_counts.copy(),
            "last_used_provider": self.last_used_provider,
            "load_balancing_strategy": self.load_balancing_strategy.value
        }

    def get_rate_limit_stats(self) -> Dict:
        """获取限流统计信息"""
        rate_limiter = get_rate_limiter()
        return rate_limiter.get_stats()

    def get_comprehensive_stats(self) -> Dict:
        """获取综合统计信息"""
        return {
            "concurrency": self.get_concurrency_stats(),
            "providers": self.get_provider_stats(),
            "rate_limits": self.get_rate_limit_stats()
        }
    
    def set_load_balancing_strategy(self, strategy: LoadBalancingStrategy):
        """Set load balancing strategy."""
        self.load_balancing_strategy = strategy
        logger.info(f"Load balancing strategy set to: {strategy.value}")
    
    def add_provider(self, name: str, provider: BaseLLMProvider, config: ProviderConfig):
        """Add a new provider at runtime."""
        self.providers[name] = provider
        self.provider_configs[name] = config
        self.request_counts[name] = 0
        logger.info(f"Added provider: {name}")
    
    def remove_provider(self, name: str):
        """Remove a provider."""
        if name in self.providers:
            del self.providers[name]
            del self.provider_configs[name]
            del self.request_counts[name]
            logger.info(f"Removed provider: {name}")
    
    def enable_provider(self, name: str):
        """Enable a provider."""
        if name in self.provider_configs:
            self.provider_configs[name].enabled = True
            logger.info(f"Enabled provider: {name}")
    
    def disable_provider(self, name: str):
        """Disable a provider."""
        if name in self.provider_configs:
            self.provider_configs[name].enabled = False
            logger.info(f"Disabled provider: {name}")

    async def analyze_code(
        self,
        code: str,
        file_path: str,
        language: str,
        template: str = "security_audit_chinese"
    ) -> Dict[str, Any]:
        """
        分析代码安全问题

        Args:
            code: 代码内容
            file_path: 文件路径
            language: 编程语言
            template: 分析模板

        Returns:
            Dict包含分析结果和发现的问题
        """
        from .base import LLMRequest

        # 构建安全分析提示词
        security_prompt = self._build_security_analysis_prompt(code, file_path, language, template)

        # 创建LLM请求 - 使用具体模型而不是"auto"
        from .base import LLMModelType, LLMMessage, MessageRole

        # 选择第一个可用的模型
        available_model = None
        for provider_name, provider in self.providers.items():
            if hasattr(provider, 'supported_models') and provider.supported_models:
                available_model = provider.supported_models[0]
                break

        if not available_model:
            # 如果没有找到可用模型，使用默认模型
            available_model = LLMModelType.QWEN_CODER_30B

        # 创建正确格式的消息
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="你是一个专业的代码安全审计专家，专门识别代码中的安全漏洞。"),
            LLMMessage(role=MessageRole.USER, content=security_prompt)
        ]

        request = LLMRequest(
            messages=messages,
            model=available_model,  # 使用具体的模型
            temperature=0.1,  # 低温度确保一致性
            max_tokens=4000
        )

        try:
            # 调用LLM进行分析
            response = await self.chat_completion(request)

            # 调试：打印响应格式
            logger.info(f"LLM response type: {type(response)}")
            logger.info(f"LLM response attributes: {dir(response) if hasattr(response, '__dict__') else 'No attributes'}")
            if isinstance(response, dict):
                logger.info(f"LLM response keys: {list(response.keys())}")

            # 解析响应并提取安全问题
            # 检查响应格式
            if hasattr(response, 'content'):
                response_content = response.content
            elif isinstance(response, dict) and 'content' in response:
                response_content = response['content']
            elif isinstance(response, dict) and 'message' in response:
                response_content = response['message']
            else:
                logger.error(f"Unexpected response format: {type(response)}, {response}")
                response_content = str(response)

            findings = self._parse_security_response(response_content, file_path, language)

            # 过滤误报
            findings = self._filter_false_positives(findings, file_path, code)

            # 增强置信度评估
            findings = await self._enhance_confidence_scores(findings, file_path, code)

            return {
                "success": True,
                "findings": findings,
                "raw_response": response.content,
                "file_path": file_path,
                "language": language
            }

        except Exception as e:
            logger.error(f"Code analysis failed for {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "findings": [],
                "file_path": file_path,
                "language": language
            }

    def _build_security_analysis_prompt(self, code: str, file_path: str, language: str, template: str) -> str:
        """构建改进的安全分析提示词"""

        # 使用配置系统检测技术栈和框架
        try:
            from ..config.security_config import get_security_config
            security_config = get_security_config()
            framework_info = security_config.detect_frameworks(code, file_path)
        except ImportError as e:
            logger.warning(f"Failed to import security_config: {e}")
            framework_info = {}
        architecture_layer = self._detect_architecture_layer(file_path)

        # 根据编程语言获取检查项
        if 'security_config' in locals():
            language_info = security_config.get_language_info(language)
            language_specific_checks = language_info.checks
            # 构建框架特定的安全规则
            framework_rules = security_config.get_framework_rules_text(framework_info)
        else:
            # 回退到默认检查项
            language_specific_checks = self._get_default_language_checks(language)
            framework_rules = ""

        # 构建检查项列表
        checks_text = "\n".join([f"- {check}" for check in language_specific_checks])

        # 检测到的框架信息
        detected_frameworks = [name for name, detected in framework_info.items() if detected]
        frameworks_text = ", ".join(detected_frameworks) if detected_frameworks else "无特定框架"

        prompt = f"""请对以下{language}代码进行专业的安全审计分析。

**重要提醒 - 避免误报**:
{framework_rules}

**架构层次**: {architecture_layer}层代码
**检测到的框架**: {frameworks_text}

**文件路径**: {file_path}
**编程语言**: {language}

**重点检查以下安全问题**:
{checks_text}

**代码内容**:
```{language}
{code}
```

**分析要求**:
1. **框架感知**: 仔细识别代码使用的框架和安全机制，避免将框架提供的安全特性误报为漏洞
2. **架构理解**: 考虑代码在系统架构中的层次和职责，不要在错误的层次要求安全控制
3. **技术准确性**: 区分真实的安全风险和框架的正常安全实现
4. **上下文分析**: 理解代码的业务逻辑和调用上下文
5. **置信度评估**: 对每个发现的问题评估置信度，避免不确定的报告

**特别注意**:
- DAO/Repository层不负责权限验证，这是Controller/Service层的职责
- 使用参数化查询的代码通常不存在SQL注入风险
- 已有安全框架保护的代码需要仔细评估是否真的存在问题

**输出格式**:
请按以下JSON格式输出分析结果:
```json
{{
  "findings": [
    {{
      "type": "漏洞类型",
      "severity": "high|medium|low",
      "confidence": 0.9,
      "line": 行号,
      "description": "详细描述安全问题",
      "code_snippet": "有问题的代码片段",
      "impact": "潜在影响",
      "recommendation": "修复建议",
      "framework_context": "框架相关说明"
    }}
  ],
  "summary": {{
    "total_issues": 总问题数,
    "high_severity": 高危问题数,
    "medium_severity": 中危问题数,
    "low_severity": 低危问题数
  }}
}}
```

**重要**: 只报告确实存在的安全问题。如果代码使用了安全的框架特性（如参数化查询），请不要报告为漏洞。置信度请如实评估：
- 0.9-1.0: 确定存在安全问题
- 0.7-0.8: 很可能存在问题
- 0.5-0.6: 可能存在问题，需要进一步确认
- 0.3-0.4: 不太确定，可能是误报
- 0.1-0.2: 很可能是误报"""

        return prompt

    def _parse_security_response(self, response_content: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """解析LLM的安全分析响应"""
        import json
        import re

        findings = []

        try:
            # 尝试提取JSON格式的响应
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_response = json.loads(json_str)

                if "findings" in parsed_response:
                    for finding in parsed_response["findings"]:
                        findings.append({
                            "file": file_path,
                            "language": language,
                            "type": finding.get("type", "security_issue"),
                            "severity": finding.get("severity", "medium"),
                            "line": finding.get("line", 0),
                            "description": finding.get("description", ""),
                            "code_snippet": finding.get("code_snippet", ""),
                            "impact": finding.get("impact", ""),
                            "recommendation": finding.get("recommendation", ""),
                            "issues": [finding.get("description", "")]
                        })

                    logger.info(f"Parsed {len(findings)} security findings from LLM response")
                    return findings

            # 如果JSON解析失败，尝试文本解析
            if "漏洞" in response_content or "安全问题" in response_content or "vulnerability" in response_content.lower():
                # 简单的文本解析逻辑
                lines = response_content.split('\n')
                current_finding = {}

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 检测可能的安全问题描述
                    if any(keyword in line for keyword in ["SQL注入", "命令注入", "路径遍历", "XSS", "CSRF", "漏洞", "安全问题"]):
                        if current_finding:
                            findings.append(current_finding)

                        current_finding = {
                            "file": file_path,
                            "language": language,
                            "type": "security_issue",
                            "severity": "medium",
                            "description": line,
                            "issues": [line]
                        }

                if current_finding:
                    findings.append(current_finding)

                logger.info(f"Text-parsed {len(findings)} security findings")
                return findings

            # 如果没有发现安全问题的明确指示，但响应很长，可能包含分析
            if len(response_content) > 100:
                logger.warning(f"LLM response received but no clear security findings extracted. Response length: {len(response_content)}")
                # 可以在这里添加更复杂的解析逻辑

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error(f"Error parsing security response: {e}")

        return findings



    def _detect_architecture_layer(self, file_path: str) -> str:
        """检测代码所在的架构层次"""
        path_lower = file_path.lower()

        if any(indicator in path_lower for indicator in ['controller', 'rest', 'api', 'endpoint']):
            return 'controller'
        elif any(indicator in path_lower for indicator in ['service', 'business', 'logic']):
            return 'service'
        elif any(indicator in path_lower for indicator in ['dao', 'repository', 'mapper', 'model']):
            return 'dao'
        elif any(indicator in path_lower for indicator in ['entity', 'domain', 'pojo']):
            return 'entity'
        elif any(indicator in path_lower for indicator in ['config', 'configuration']):
            return 'config'
        else:
            return 'unknown'



    def _filter_false_positives(self, findings: List[Dict], file_path: str, code: str) -> List[Dict]:
        """过滤明显的误报"""
        filtered_findings = []

        for finding in findings:
            if self._is_false_positive(finding, file_path, code):
                logger.info(f"Filtered false positive: {finding.get('type', 'unknown')} in {file_path}")
                continue
            filtered_findings.append(finding)

        return filtered_findings

    def _is_false_positive(self, finding: Dict, file_path: str, code: str) -> bool:
        """判断是否为误报"""
        try:
            from ..config.security_config import get_security_config
            security_config = get_security_config()
        except ImportError as e:
            logger.warning(f"Failed to import security_config: {e}")
            return False
        finding_type = finding.get('type', '')
        description = finding.get('description', '')
        code_snippet = finding.get('code_snippet', '')
        confidence = finding.get('confidence', 1.0)

        # 置信度过低的问题
        confidence_threshold = security_config.get_confidence_threshold()
        if confidence < confidence_threshold:
            return True

        # SQL注入误报检查
        if 'SQL注入' in finding_type or 'SQL注入' in description:
            if security_config.is_safe_sql_pattern(code_snippet):
                return True

        # 权限验证误报检查
        if '权限' in finding_type or '越权' in finding_type or '权限' in description:
            if security_config.is_dao_layer_permission_issue(file_path, code_snippet):
                return True

        return False

    async def _enhance_confidence_scores(self, findings: List[Dict], file_path: str, code: str) -> List[Dict]:
        """使用智能置信度计算器增强置信度评估"""
        from ..config.security_config import get_security_config

        security_config = get_security_config()
        enhanced_findings = []

        # 延迟初始化置信度计算器
        if self.confidence_calculator is None:
            try:
                from ..analysis.confidence_calculator import ConfidenceCalculator
                self.confidence_calculator = ConfidenceCalculator()
            except ImportError as e:
                logger.warning(f"Failed to import ConfidenceCalculator: {e}")
                # 如果导入失败，直接返回原始findings
                return findings

        # 构建上下文信息
        context = {
            'file_path': file_path,
            'frameworks': security_config.detect_frameworks(code, file_path),
            'architecture_layer': self._detect_architecture_layer(file_path),
            'tech_stack': self._get_tech_stack_info(file_path),
            'security_config': self._get_security_config_info(file_path),
            'call_chain': None,  # 可以后续添加调用链分析
        }

        for finding in findings:
            try:
                # 使用置信度计算器
                confidence_result = self.confidence_calculator.calculate_confidence(finding, context)

                # 更新finding的置信度和相关信息
                finding['confidence'] = confidence_result.final_score
                finding['confidence_factors'] = {
                    'framework_protection': confidence_result.factors.framework_protection,
                    'architecture_appropriateness': confidence_result.factors.architecture_appropriateness,
                    'code_complexity': confidence_result.factors.code_complexity,
                    'pattern_reliability': confidence_result.factors.pattern_reliability,
                    'context_completeness': confidence_result.factors.context_completeness,
                    'historical_accuracy': confidence_result.factors.historical_accuracy
                }
                finding['confidence_reasoning'] = confidence_result.reasoning
                finding['risk_level'] = confidence_result.risk_level

                # 对中低置信度问题进行跨文件分析
                # 调整触发条件：置信度 < 0.98 且 > 0.4，或者特定问题类型
                should_analyze_cross_file = (
                    self.cross_file_analyzer and (
                        (confidence_result.final_score < 0.98 and confidence_result.final_score > 0.4) or
                        any(keyword in finding.get('type', '') for keyword in ['文件上传', 'XSS', '路径遍历', '权限'])
                    )
                )

                if should_analyze_cross_file:
                    try:
                        cross_file_result = await self.cross_file_analyzer.analyze_uncertain_finding(
                            finding, file_path, code, self
                        )

                        # 更新置信度和相关信息
                        finding['confidence'] = cross_file_result.adjusted_confidence
                        finding['cross_file_analysis'] = {
                            'original_confidence': cross_file_result.original_confidence,
                            'adjusted_confidence': cross_file_result.adjusted_confidence,
                            'related_files': [
                                {
                                    'path': rf.path,
                                    'relationship': rf.relationship,
                                    'reason': rf.reason
                                } for rf in cross_file_result.related_files
                            ],
                            'evidence': cross_file_result.evidence,
                            'recommendation': cross_file_result.recommendation
                        }

                        logger.info(f"Cross-file analysis adjusted confidence: {cross_file_result.original_confidence:.2f} → {cross_file_result.adjusted_confidence:.2f}")

                    except Exception as e:
                        logger.warning(f"Cross-file analysis failed: {e}")

                enhanced_findings.append(finding)

            except Exception as e:
                logger.warning(f"Failed to calculate confidence for finding: {e}")
                # 保留原始finding，使用默认置信度
                if 'confidence' not in finding:
                    finding['confidence'] = 0.5
                enhanced_findings.append(finding)

        return enhanced_findings

    def _get_tech_stack_info(self, file_path: str) -> Dict[str, Any]:
        """获取技术栈信息"""
        # 简化实现，可以后续集成项目分析器
        return {
            'language': self._detect_language_from_path(file_path),
            'frameworks': [],
            'build_tools': []
        }

    def _get_security_config_info(self, file_path: str) -> Dict[str, Any]:
        """获取安全配置信息"""
        # 简化实现，可以后续添加安全配置检测
        return {
            'authentication_enabled': False,
            'authorization_enabled': False,
            'csrf_protection': False
        }

    def _detect_language_from_path(self, file_path: str) -> str:
        """从文件路径检测编程语言"""
        from pathlib import Path
        extension = Path(file_path).suffix.lower()
        language_map = {
            '.java': 'java',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.php': 'php',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rb': 'ruby'
        }
        return language_map.get(extension, 'unknown')

    def _get_default_language_checks(self, language: str) -> List[str]:
        """获取默认的语言检查项"""
        default_checks = {
            "java": [
                "SQL注入漏洞",
                "命令注入漏洞",
                "路径遍历漏洞",
                "反序列化漏洞",
                "XML外部实体注入",
                "硬编码密钥和敏感信息",
                "权限验证绕过"
            ],
            "python": [
                "SQL注入漏洞",
                "命令注入漏洞",
                "路径遍历漏洞",
                "反序列化漏洞",
                "代码注入漏洞",
                "硬编码密钥和敏感信息"
            ],
            "javascript": [
                "XSS跨站脚本攻击",
                "原型污染漏洞",
                "代码注入",
                "路径遍历漏洞",
                "敏感信息泄露"
            ],
            "php": [
                "SQL注入漏洞",
                "文件包含漏洞",
                "代码注入",
                "命令注入漏洞",
                "路径遍历漏洞"
            ]
        }
        return default_checks.get(language, default_checks.get("java", []))

    def set_project_path(self, project_path: str):
        """设置项目路径，用于跨文件分析"""
        self.project_path = project_path
        # 初始化跨文件分析器
        try:
            from ..analysis.cross_file_analyzer import CrossFileAnalyzer
            self.cross_file_analyzer = CrossFileAnalyzer(project_path)
        except ImportError as e:
            logger.warning(f"Failed to import CrossFileAnalyzer: {e}")
            self.cross_file_analyzer = None


