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
                logger.debug(f"Attempting request with provider: {provider_name}")
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
