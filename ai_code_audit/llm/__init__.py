"""
LLM integration module for AI Code Audit System.

This module provides integration with various Large Language Models
including Qwen (SiliconFlow) and Kimi (MoonshotAI) for code analysis.
"""

from ai_code_audit.llm.base import BaseLLMProvider, LLMResponse, LLMRequest
from ai_code_audit.llm.qwen_provider import QwenProvider
from ai_code_audit.llm.kimi_provider import KimiProvider
from ai_code_audit.llm.manager import LLMManager
from ai_code_audit.llm.prompts import PromptManager

__all__ = [
    "BaseLLMProvider",
    "LLMResponse", 
    "LLMRequest",
    "QwenProvider",
    "KimiProvider",
    "LLMManager",
    "PromptManager",
]
