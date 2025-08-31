from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.base import get_db
from app.core.deps import get_current_admin_user
from app.models.user import User
from app.schemas.invitation import (
    InvitationCodeCreate, 
    InvitationCodeUpdate, 
    InvitationCodeResponse, 
    InvitationCodeVerify,
    InvitationCodeStats
)
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/invitation", tags=["邀请码管理"])


@router.post("/codes", response_model=List[InvitationCodeResponse], summary="创建邀请码")
async def create_invitation_codes(
    invitation_data: InvitationCodeCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建邀请码（支持批量生成）
    
    - **user_level**: 用户等级（free/standard/premium）
    - **token_limit**: Token限额
    - **max_uses**: 最大使用次数
    - **expires_at**: 过期时间（可选）
    - **batch_count**: 批量生成数量（1-100）
    """
    try:
        codes = await InvitationService.create_invitation_codes(
            db, invitation_data, current_admin.id
        )
        return codes
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建邀请码失败: {str(e)}")


@router.get("/codes", response_model=List[InvitationCodeResponse], summary="获取邀请码列表")
async def get_invitation_codes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选: active/inactive/expired"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邀请码列表"""
    try:
        codes, total = await InvitationService.get_invitation_list(
            db, page, page_size, status_filter
        )
        return codes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取邀请码列表失败: {str(e)}")


@router.get("/codes/stats", response_model=InvitationCodeStats, summary="获取邀请码统计")
async def get_invitation_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邀请码统计信息"""
    try:
        stats = await InvitationService.get_invitation_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.put("/codes/{invitation_id}", response_model=InvitationCodeResponse, summary="更新邀请码")
async def update_invitation_code(
    invitation_id: int,
    invitation_data: InvitationCodeUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新邀请码信息"""
    try:
        invitation = await InvitationService.update_invitation(
            db, invitation_id, invitation_data
        )
        return invitation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新邀请码失败: {str(e)}")


@router.delete("/codes/{invitation_id}", summary="删除邀请码")
async def delete_invitation_code(
    invitation_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除邀请码"""
    try:
        await InvitationService.delete_invitation(db, invitation_id)
        return {"message": "邀请码删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"删除邀请码失败: {str(e)}")


@router.post("/verify", summary="验证邀请码")
async def verify_invitation_code(
    verify_data: InvitationCodeVerify,
    db: AsyncSession = Depends(get_db)
):
    """验证邀请码是否有效（公开接口）"""
    try:
        is_valid, invitation = await InvitationService.verify_invitation_code(
            db, verify_data.code
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邀请码无效或已过期"
            )
        
        return {
            "valid": True,
            "user_level": invitation.user_level.value,
            "token_limit": invitation.token_limit,
            "remaining_uses": invitation.remaining_uses
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"验证邀请码失败: {str(e)}")
