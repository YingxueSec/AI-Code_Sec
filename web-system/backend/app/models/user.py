from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Enum, Integer
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class UserLevel(str, enum.Enum):
    free = "free"
    standard = "standard"
    premium = "premium"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    user_level = Column(Enum(UserLevel), default=UserLevel.free, nullable=False)
    daily_token_limit = Column(Integer, default=1000, nullable=False)
    used_tokens_today = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
