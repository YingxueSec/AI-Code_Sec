from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.user import UserLevel
from datetime import datetime
import enum


class InvitationStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    expired = "expired"


class InvitationCode(Base):
    __tablename__ = "invitation_codes"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True, default="")
    user_level = Column(SQLEnum(UserLevel), nullable=False, default=UserLevel.free)
    token_limit = Column(Integer, nullable=False, default=1000)
    max_uses = Column(Integer, nullable=False, default=1)
    used_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    @property
    def status(self) -> InvitationStatus:
        """获取邀请码状态"""
        if not self.is_active:
            return InvitationStatus.inactive
        if self.expires_at and self.expires_at < datetime.utcnow():
            return InvitationStatus.expired
        if self.used_count >= self.max_uses:
            return InvitationStatus.inactive
        return InvitationStatus.active
    
    @property
    def remaining_uses(self) -> int:
        """剩余使用次数"""
        return max(0, self.max_uses - self.used_count)
    
    def __repr__(self):
        return f"<InvitationCode(id={self.id}, code='{self.code}', status='{self.status}')>"
