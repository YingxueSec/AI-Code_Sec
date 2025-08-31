from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.invitation import InvitationCode, InvitationStatus
from app.models.user import User, UserLevel
from app.schemas.invitation import InvitationCodeCreate, InvitationCodeUpdate, InvitationCodeStats
from app.core.security import generate_invitation_code


class InvitationService:
    
    @staticmethod
    async def create_invitation_codes(
        db: AsyncSession, 
        invitation_data: InvitationCodeCreate, 
        created_by: int
    ) -> List[InvitationCode]:
        """创建邀请码（支持批量）"""
        codes = []
        batch_count = invitation_data.batch_count or 1
        
        for _ in range(batch_count):
            # 生成唯一邀请码
            code = generate_invitation_code()
            while await InvitationService.get_invitation_by_code(db, code):
                code = generate_invitation_code()
            
            invitation = InvitationCode(
                code=code,
                description=invitation_data.description or f"{invitation_data.user_level.value}级邀请码",
                user_level=invitation_data.user_level,
                token_limit=invitation_data.token_limit,
                max_uses=invitation_data.max_uses,
                expires_at=invitation_data.expires_at,
                created_by=created_by
            )
            
            db.add(invitation)
            codes.append(invitation)
        
        try:
            await db.commit()
            for code in codes:
                await db.refresh(code)
            return codes
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create invitation codes"
            )
    
    @staticmethod
    async def get_invitation_by_code(db: AsyncSession, code: str) -> Optional[InvitationCode]:
        """根据邀请码获取邀请码信息"""
        result = await db.execute(
            select(InvitationCode).where(InvitationCode.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def verify_invitation_code(db: AsyncSession, code: str) -> tuple[bool, Optional[InvitationCode]]:
        """验证邀请码是否有效"""
        invitation = await InvitationService.get_invitation_by_code(db, code)
        
        if not invitation:
            return False, None
        
        # 检查邀请码状态
        if invitation.status != InvitationStatus.active:
            return False, invitation
        
        return True, invitation
    
    @staticmethod
    async def use_invitation_code(db: AsyncSession, code: str) -> Optional[InvitationCode]:
        """使用邀请码（增加使用次数）"""
        is_valid, invitation = await InvitationService.verify_invitation_code(db, code)
        
        if not is_valid or not invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation code"
            )
        
        # 增加使用次数
        invitation.used_count += 1
        await db.commit()
        await db.refresh(invitation)
        
        return invitation
    
    @staticmethod
    async def get_invitation_list(
        db: AsyncSession, 
        page: int = 1, 
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> tuple[List[InvitationCode], int]:
        """获取邀请码列表"""
        query = select(InvitationCode).order_by(InvitationCode.created_at.desc())
        
        # 状态筛选
        if status_filter == "active":
            query = query.where(
                and_(
                    InvitationCode.is_active == True,
                    InvitationCode.used_count < InvitationCode.max_uses,
                    (InvitationCode.expires_at.is_(None) | (InvitationCode.expires_at > datetime.utcnow()))
                )
            )
        elif status_filter == "inactive":
            query = query.where(InvitationCode.is_active == False)
        elif status_filter == "expired":
            query = query.where(
                and_(
                    InvitationCode.expires_at.isnot(None),
                    InvitationCode.expires_at <= datetime.utcnow()
                )
            )
        
        # 总数
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        invitations = result.scalars().all()
        
        return list(invitations), total
    
    @staticmethod
    async def update_invitation(
        db: AsyncSession, 
        invitation_id: int, 
        invitation_data: InvitationCodeUpdate
    ) -> Optional[InvitationCode]:
        """更新邀请码"""
        result = await db.execute(
            select(InvitationCode).where(InvitationCode.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation code not found"
            )
        
        # 更新字段
        for field, value in invitation_data.dict(exclude_unset=True).items():
            setattr(invitation, field, value)
        
        await db.commit()
        await db.refresh(invitation)
        return invitation
    
    @staticmethod
    async def delete_invitation(db: AsyncSession, invitation_id: int) -> bool:
        """删除邀请码"""
        result = await db.execute(
            select(InvitationCode).where(InvitationCode.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation code not found"
            )
        
        await db.delete(invitation)
        await db.commit()
        return True
    
    @staticmethod
    async def get_invitation_stats(db: AsyncSession) -> InvitationCodeStats:
        """获取邀请码统计信息"""
        # 总数
        total_result = await db.execute(select(func.count(InvitationCode.id)))
        total_codes = total_result.scalar() or 0
        
        # 活跃的
        active_result = await db.execute(
            select(func.count(InvitationCode.id)).where(
                and_(
                    InvitationCode.is_active == True,
                    InvitationCode.used_count < InvitationCode.max_uses,
                    (InvitationCode.expires_at.is_(None) | (InvitationCode.expires_at > datetime.utcnow()))
                )
            )
        )
        active_codes = active_result.scalar() or 0
        
        # 过期的
        expired_result = await db.execute(
            select(func.count(InvitationCode.id)).where(
                and_(
                    InvitationCode.expires_at.isnot(None),
                    InvitationCode.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_codes = expired_result.scalar() or 0
        
        # 已用完的
        used_result = await db.execute(
            select(func.count(InvitationCode.id)).where(
                InvitationCode.used_count >= InvitationCode.max_uses
            )
        )
        used_codes = used_result.scalar() or 0
        
        # 总使用次数
        total_uses_result = await db.execute(select(func.sum(InvitationCode.used_count)))
        total_uses = total_uses_result.scalar() or 0
        
        # 剩余使用次数
        remaining_result = await db.execute(
            select(func.sum(InvitationCode.max_uses - InvitationCode.used_count)).where(
                and_(
                    InvitationCode.is_active == True,
                    InvitationCode.used_count < InvitationCode.max_uses,
                    (InvitationCode.expires_at.is_(None) | (InvitationCode.expires_at > datetime.utcnow()))
                )
            )
        )
        remaining_uses = remaining_result.scalar() or 0
        
        return InvitationCodeStats(
            total_codes=total_codes,
            active_codes=active_codes,
            expired_codes=expired_codes,
            used_codes=used_codes,
            total_uses=total_uses,
            remaining_uses=remaining_uses
        )
