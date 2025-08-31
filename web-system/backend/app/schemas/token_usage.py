from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TokenUsageBase(BaseModel):
    user_id: int
    task_id: Optional[int] = None
    tokens_consumed: int = Field(ge=0)
    provider: str = Field(max_length=50)
    model_name: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(default=0.0000, ge=0)


class TokenUsageCreate(TokenUsageBase):
    pass


class TokenUsageResponse(TokenUsageBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenUsageStats(BaseModel):
    total_tokens: int
    total_cost: Decimal
    total_requests: int
    avg_tokens_per_request: float
    most_used_provider: str
    daily_breakdown: list


class UserTokenStats(BaseModel):
    user_id: int
    username: str
    total_tokens_consumed: int
    total_requests: int
    total_cost: Decimal
    last_usage: Optional[datetime]
    most_used_provider: str
    
    class Config:
        from_attributes = True
