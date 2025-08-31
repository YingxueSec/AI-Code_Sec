from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.deps import get_current_admin_user, get_db
from app.models.user import User
from app.services.export_permission_service import ExportPermissionService
from app.schemas.export_permission import (
    UserExportPermissionResponse,
    UserExportPermissionList,
    SetExportPermissionRequest,
    BatchSetPermissionRequest,
    ExportLogResponse,
    ExportLogList
)

router = APIRouter(prefix="/admin/export", tags=["管理员-导出权限管理"])


@router.get("/permissions", response_model=UserExportPermissionList, summary="获取所有用户导出权限")
async def get_all_user_export_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户的导出权限配置（管理员专用）
    """
    result = await ExportPermissionService.get_all_user_permissions(db, page, page_size)
    return result


@router.post("/permissions/{user_id}", summary="设置用户导出权限")
async def set_user_export_permission(
    user_id: int,
    request: SetExportPermissionRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    设置指定用户的导出权限（管理员专用）
    """
    success = await ExportPermissionService.set_user_export_permission(
        db, user_id, request.allowed_formats, current_admin.id
    )
    
    if success:
        return {"message": "用户导出权限设置成功", "user_id": user_id}
    else:
        raise HTTPException(status_code=400, detail="设置用户导出权限失败")


@router.delete("/permissions/{user_id}", summary="重置用户导出权限")
async def reset_user_export_permission(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户导出权限到默认配置（管理员专用）
    """
    success = await ExportPermissionService.reset_user_permission(db, user_id)
    
    if success:
        return {"message": "用户导出权限已重置为默认配置", "user_id": user_id}
    else:
        raise HTTPException(status_code=400, detail="重置用户导出权限失败")


@router.post("/permissions/batch", summary="批量设置用户导出权限")
async def batch_set_export_permissions(
    request: BatchSetPermissionRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量设置多个用户的导出权限（管理员专用）
    """
    result = await ExportPermissionService.batch_set_permissions(
        db, request.user_ids, request.allowed_formats, current_admin.id
    )
    
    return {
        "message": f"批量设置完成，成功: {result['success']} 个，失败: {result['failed']} 个",
        "success_count": result["success"],
        "failed_count": result["failed"]
    }


@router.get("/logs", response_model=ExportLogList, summary="获取导出操作日志")
async def get_export_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    user_id: Optional[int] = Query(None, description="筛选指定用户"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取导出操作日志（管理员专用）
    """
    result = await ExportPermissionService.get_export_logs(db, user_id, page, page_size)
    return result


@router.get("/stats", summary="获取导出统计信息")
async def get_export_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取导出操作统计信息（管理员专用）
    """
    from sqlalchemy import select, func, text
    from app.models.export_permission import ExportLog
    from datetime import datetime, timedelta
    
    # 获取今日导出统计
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 今日导出次数
    today_count_query = select(func.count(ExportLog.id)).where(
        ExportLog.exported_at >= today_start
    )
    today_count_result = await db.execute(today_count_query)
    today_count = today_count_result.scalar()
    
    # 本周导出次数
    week_start = today_start - timedelta(days=today.weekday())
    week_count_query = select(func.count(ExportLog.id)).where(
        ExportLog.exported_at >= week_start
    )
    week_count_result = await db.execute(week_count_query)
    week_count = week_count_result.scalar()
    
    # 按格式统计
    format_stats_query = select(
        ExportLog.export_format,
        func.count(ExportLog.id).label('count')
    ).group_by(ExportLog.export_format)
    format_stats_result = await db.execute(format_stats_query)
    format_stats = {row.export_format: row.count for row in format_stats_result}
    
    # 成功率统计
    success_query = select(func.count(ExportLog.id)).where(ExportLog.success == "success")
    success_result = await db.execute(success_query)
    success_count = success_result.scalar()
    
    total_query = select(func.count(ExportLog.id))
    total_result = await db.execute(total_query)
    total_count = total_result.scalar()
    
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "today_exports": today_count,
        "week_exports": week_count,
        "total_exports": total_count,
        "success_rate": round(success_rate, 2),
        "format_stats": format_stats,
        "stats_time": datetime.now()
    }


@router.get("/formats", summary="获取支持的导出格式")
async def get_supported_formats(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    获取系统支持的所有导出格式（管理员专用）
    """
    return {
        "formats": [
            {
                "format": "json",
                "name": "JSON",
                "description": "结构化数据格式，便于程序处理",
                "file_extension": ".json",
                "content_type": "application/json"
            },
            {
                "format": "markdown",
                "name": "Markdown",
                "description": "Markdown文档格式，便于阅读",
                "file_extension": ".md",
                "content_type": "text/markdown"
            },
            {
                "format": "pdf",
                "name": "PDF",
                "description": "便携式文档格式，便于打印和分享",
                "file_extension": ".pdf",
                "content_type": "application/pdf"
            },
            {
                "format": "html",
                "name": "HTML",
                "description": "网页格式，可在浏览器中查看",
                "file_extension": ".html",
                "content_type": "text/html"
            }
        ],
        "default_permissions": {
            "free": ["json"],
            "standard": ["json", "markdown"],
            "premium": ["json", "markdown", "pdf"],
            "admin": ["json", "markdown", "pdf", "html"]
        }
    }
