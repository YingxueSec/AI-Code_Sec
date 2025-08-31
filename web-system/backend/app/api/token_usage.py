from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.base import get_db
from app.core.deps import get_current_user, get_current_admin_user
from app.models.user import User
from app.schemas.token_usage import TokenUsageResponse, TokenUsageStats, UserTokenStats
from app.services.token_usage_service import TokenUsageService

router = APIRouter(prefix="/token-usage", tags=["Token使用记录"])


@router.get("/my-usage", response_model=dict, summary="获取我的Token使用记录")
async def get_my_token_usage(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的Token使用记录"""
    try:
        usages, total = await TokenUsageService.get_user_token_usage(
            db, current_user.id, days, page, page_size
        )
        
        return {
            "data": [
                {
                    "id": usage.id,
                    "tokens_consumed": usage.tokens_consumed,
                    "provider": usage.provider,
                    "provider_display": usage.provider_display,
                    "model_name": usage.model_name,
                    "cost": float(usage.cost),
                    "created_at": usage.created_at.isoformat(),
                    "task_id": usage.task_id
                }
                for usage in usages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Token使用记录失败: {str(e)}")


@router.get("/stats", response_model=TokenUsageStats, summary="获取系统Token使用统计")
async def get_token_usage_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统Token使用统计（管理员专用）"""
    try:
        return await TokenUsageService.get_system_token_stats(db, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Token统计失败: {str(e)}")


@router.get("/user-stats", response_model=dict, summary="获取所有用户Token使用统计")
async def get_all_user_token_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有用户Token使用统计（管理员专用）"""
    try:
        user_stats, total = await TokenUsageService.get_all_user_token_stats(
            db, days, page, page_size
        )
        
        return {
            "data": [
                {
                    "user_id": stat.user_id,
                    "username": stat.username,
                    "total_tokens_consumed": stat.total_tokens_consumed,
                    "total_requests": stat.total_requests,
                    "total_cost": float(stat.total_cost),
                    "last_usage": stat.last_usage.isoformat() if stat.last_usage else None,
                    "most_used_provider": stat.most_used_provider
                }
                for stat in user_stats
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")


@router.get("/user/{user_id}", response_model=dict, summary="获取指定用户Token使用记录")
async def get_user_token_usage(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定用户的Token使用记录（管理员专用）"""
    try:
        usages, total = await TokenUsageService.get_user_token_usage(
            db, user_id, days, page, page_size
        )
        
        return {
            "data": [
                {
                    "id": usage.id,
                    "tokens_consumed": usage.tokens_consumed,
                    "provider": usage.provider,
                    "provider_display": usage.provider_display,
                    "model_name": usage.model_name,
                    "cost": float(usage.cost),
                    "created_at": usage.created_at.isoformat(),
                    "task_id": usage.task_id
                }
                for usage in usages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户Token使用记录失败: {str(e)}")
