from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from app.db.base import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, TokenRefresh, ChangePassword, UserProfile
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.deps import get_current_user
from app.models.user import User
from app.core.config import settings
from app.services.invitation_service import InvitationService
from app.services.system_log_service import SystemLogService

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    - **username**: 用户名（唯一）
    - **email**: 邮箱（唯一）
    - **password**: 密码
    - **invitation_code**: 邀请码（可选）
    """
    # 验证邀请码逻辑
    invitation = None
    if user_data.invitation_code:
        try:
            invitation = await InvitationService.use_invitation_code(db, user_data.invitation_code)
        except HTTPException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"邀请码错误: {e.detail}"
            )
    
    # 创建用户（如果有邀请码则使用邀请码的配置）
    user = await UserService.create_user(db, user_data, invitation)
    
    # 记录注册日志
    await SystemLogService.log_user_action(
        db=db,
        user_id=user.id,
        action="register",
        details=f"用户 {user.username} 注册成功",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return user


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username_or_email**: 用户名或邮箱
    - **password**: 密码
    - **remember_me**: 是否记住登录状态
    """
    user = await UserService.authenticate_user(
        db, login_data.username_or_email, login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if login_data.remember_me:
        access_token_expires = timedelta(days=7)  # 记住登录延长到7天
    
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # 更新最后登录时间
    await UserService.update_last_login(db, user.id)
    
    # 记录登录日志
    await SystemLogService.log_user_action(
        db=db,
        user_id=user.id,
        action="login",
        details=f"用户 {user.username} 登录成功",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }


@router.post("/refresh", response_model=Token, summary="刷新令牌")
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    payload = verify_token(token_data.refresh_token, "refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    user = await UserService.get_user_by_username(db, username)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }


@router.get("/profile", response_model=UserProfile, summary="获取用户信息")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    
    - **current_password**: 当前密码
    - **new_password**: 新密码
    - **confirm_password**: 确认新密码
    """
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    success = await UserService.change_password(
        db, current_user, password_data.current_password, password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/logout", summary="用户登出")
async def logout():
    """
    用户登出
    
    注意：JWT令牌是无状态的，真正的登出需要前端清除令牌
    这个接口主要用于记录登出日志
    """
    # TODO: 可以在这里记录登出日志
    return {"message": "Logged out successfully"}
