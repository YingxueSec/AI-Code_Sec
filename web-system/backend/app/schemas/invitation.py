from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.user import UserLevel
from app.models.invitation import InvitationStatus


class InvitationCodeBase(BaseModel):
    description: Optional[str] = Field(default="", max_length=255)
    user_level: UserLevel = UserLevel.free
    token_limit: int = Field(default=1000, ge=100, le=100000)
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_at: Optional[datetime] = None


class InvitationCodeCreate(InvitationCodeBase):
    batch_count: Optional[int] = Field(default=1, ge=1, le=100)  # 批量生成数量


class InvitationCodeUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    max_uses: Optional[int] = Field(None, ge=1, le=1000)
    expires_at: Optional[datetime] = None


class InvitationCodeResponse(InvitationCodeBase):
    id: int
    code: str
    used_count: int
    is_active: bool
    status: InvitationStatus
    remaining_uses: int
    created_at: Optional[datetime] = None
    created_by: int
    
    class Config:
        from_attributes = True


class InvitationCodeVerify(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)


class InvitationCodeStats(BaseModel):
    total_codes: int
    active_codes: int
    expired_codes: int
    used_codes: int
    total_uses: int
    remaining_uses: int
