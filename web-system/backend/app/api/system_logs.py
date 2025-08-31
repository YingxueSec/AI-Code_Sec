from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.core.deps import get_current_admin_user, get_current_user
from app.models.user import User
from app.schemas.system_log import SystemLogResponse, SystemLogFilter, SystemLogStats
from app.services.system_log_service import SystemLogService

router = APIRouter(prefix="/logs", tags=["系统日志"])


@router.get("/", response_model=List[SystemLogResponse], summary="获取系统日志")
async def get_system_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    ip_address: Optional[str] = Query(None, description="IP地址筛选"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统日志列表（管理员专用）"""
    try:
        # 构建筛选条件
        log_filter = SystemLogFilter(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address
        )
        
        logs, total = await SystemLogService.get_logs_with_user(
            db, page, page_size, log_filter
        )
        
        # 将模型转换为响应格式，包含用户信息
        response_logs = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "action_display": log.action_display,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at,
            }
            response_logs.append(SystemLogResponse(**log_dict))
        
        return response_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统日志失败: {str(e)}")


@router.get("/stats", response_model=SystemLogStats, summary="获取日志统计")
async def get_log_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统日志统计信息"""
    try:
        stats = await SystemLogService.get_log_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")


@router.delete("/cleanup", summary="清理旧日志")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=7, le=365, description="保留天数"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """清理旧日志（管理员专用）"""
    try:
        deleted_count = await SystemLogService.clean_old_logs(db, days_to_keep)
        
        # 记录清理操作
        await SystemLogService.log_user_action(
            db=db,
            user_id=current_admin.id,
            action="log_cleanup",
            details=f"清理了 {deleted_count} 条超过 {days_to_keep} 天的日志"
        )
        
        return {
            "message": f"成功清理了 {deleted_count} 条旧日志",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")


# 中间件：自动记录用户操作日志
async def log_user_action_middleware(request: Request, call_next):
    """记录用户操作的中间件"""
    response = await call_next(request)
    
    # 这里可以根据需要记录特定的操作
    # 例如：POST, PUT, DELETE 请求
    if request.method in ["POST", "PUT", "DELETE"]:
        # 获取当前用户信息（如果有的话）
        # 记录到数据库
        pass
    
    return response
