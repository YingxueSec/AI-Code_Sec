from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    task_id = Column(BigInteger, ForeignKey("audit_tasks.id"), nullable=True)
    tokens_consumed = Column(Integer, nullable=False)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=True)
    cost = Column(DECIMAL(10, 4), default=0.0000)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    task = relationship("AuditTask", foreign_keys=[task_id])
    
    def __repr__(self):
        return f"<TokenUsage(id={self.id}, user_id={self.user_id}, tokens={self.tokens_consumed})>"
    
    @property
    def provider_display(self) -> str:
        """获取提供商的显示名称"""
        provider_map = {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'azure': 'Azure OpenAI',
            'gemini': 'Google Gemini',
            'local': '本地模型',
            'deepseek': 'DeepSeek',
            'zhipu': '智谱AI',
            'qwen': '通义千问',
            'baidu': '百度文心',
        }
        return provider_map.get(self.provider, self.provider.title())
