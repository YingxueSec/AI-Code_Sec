from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, UserLevel


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.user
    user_level: UserLevel = UserLevel.free
    daily_token_limit: int = 1000
    is_active: bool = True


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    invitation_code: Optional[str] = None


class UserLogin(BaseModel):
    username_or_email: str
    password: str
    remember_me: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    user_level: Optional[UserLevel] = None
    daily_token_limit: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    used_tokens_today: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    user_level: UserLevel
    daily_token_limit: int
    used_tokens_today: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str
