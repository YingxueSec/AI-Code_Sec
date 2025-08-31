from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SystemLogBase(BaseModel):
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SystemLogCreate(SystemLogBase):
    user_id: Optional[int] = None


class SystemLogResponse(SystemLogBase):
    id: int
    user_id: Optional[int]
    action_display: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SystemLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None


class SystemLogStats(BaseModel):
    total_logs: int
    today_logs: int
    login_count: int
    audit_count: int
    error_count: int
