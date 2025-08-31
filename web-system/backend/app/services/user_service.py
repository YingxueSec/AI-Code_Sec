from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional, List, TYPE_CHECKING
from app.models.user import User, UserLevel
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from datetime import datetime

if TYPE_CHECKING:
    from app.models.invitation import InvitationCode


class UserService:
    
    @staticmethod
    async def create_user(
        db: AsyncSession, 
        user_data: UserCreate, 
        invitation: Optional["InvitationCode"] = None
    ) -> User:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        existing_user = await UserService.get_user_by_username_or_email(
            db, user_data.username, user_data.email
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # 根据邀请码设置用户等级和限额
        user_level = UserLevel.free
        daily_token_limit = 1000
        
        if invitation:
            user_level = invitation.user_level
            daily_token_limit = invitation.token_limit
        
        # 创建新用户
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            user_level=user_level,
            daily_token_limit=daily_token_limit
        )
        
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username_or_email: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await UserService.get_user_by_username_or_email(db, username_or_email, username_or_email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    async def get_user_by_username_or_email(db: AsyncSession, username: str, email: str) -> Optional[User]:
        """通过用户名或邮箱获取用户"""
        result = await db.execute(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """更新用户"""
        # 构建更新数据
        update_data = {}
        for field, value in user_data.dict(exclude_unset=True).items():
            update_data[field] = value
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await db.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await db.commit()
        
        return await UserService.get_user_by_id(db, user_id)
    
    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: int):
        """更新最后登录时间"""
        await db.execute(
            update(User).where(User.id == user_id).values(last_login=datetime.utcnow())
        )
        await db.commit()
    
    @staticmethod
    async def get_users_list(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[User]:
        """获取用户列表"""
        query = select(User)
        
        if search:
            query = query.where(
                (User.username.like(f"%{search}%")) | 
                (User.email.like(f"%{search}%"))
            )
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def count_users(db: AsyncSession, search: Optional[str] = None) -> int:
        """统计用户数量"""
        query = select(User.id)
        
        if search:
            query = query.where(
                (User.username.like(f"%{search}%")) | 
                (User.email.like(f"%{search}%"))
            )
        
        result = await db.execute(query)
        return len(result.scalars().all())
    
    @staticmethod
    async def change_password(
        db: AsyncSession, 
        user: User, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """修改密码"""
        if not verify_password(current_password, user.password_hash):
            return False
        
        new_hash = get_password_hash(new_password)
        await db.execute(
            update(User).where(User.id == user.id).values(
                password_hash=new_hash,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        return True
