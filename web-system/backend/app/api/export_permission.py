from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.base import get_db
from app.core.deps import get_current_admin_user, get_current_user
from app.models.user import User
from app.services.export_permission_service import ExportPermissionService
from app.schemas.export_permission import (
    ExportPermissionConfigCreate,
    ExportPermissionConfigUpdate, 
    ExportPermissionConfigResponse,
    ExportPermissionCheck,
    ExportStatsResponse,
    UserExportLogResponse,
    CreateUserSpecificPermission,
    UpdateUserSpecificPermission,
    UserSpecificPermissionResponse
)

router = APIRouter(prefix="/export-permission", tags=["导出权限管理"])


@router.post("/configs", response_model=ExportPermissionConfigResponse, summary="创建导出权限配置")
async def create_export_permission_config(
    config_data: ExportPermissionConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建导出权限配置（仅管理员）
    
    - **user_level**: 用户等级 (free, standard, premium)
    - **allowed_formats**: 允许的导出格式
    - **max_exports_per_day**: 每日最大导出次数
    - **max_file_size_mb**: 最大文件大小(MB)
    - **description**: 配置描述
    """
    try:
        config = await ExportPermissionService.create_permission_config(db, config_data)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建权限配置失败: {str(e)}")


@router.get("/configs", response_model=List[ExportPermissionConfigResponse], summary="获取导出权限配置列表")
async def get_export_permission_configs(
    page: int = 1,
    page_size: int = 20,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有导出权限配置（仅管理员）"""
    try:
        configs = await ExportPermissionService.get_permission_configs(db, page, page_size)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取权限配置失败: {str(e)}")


@router.put("/configs/{config_id}", response_model=ExportPermissionConfigResponse, summary="更新导出权限配置")
async def update_export_permission_config(
    config_id: int,
    update_data: ExportPermissionConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新导出权限配置（仅管理员）"""
    try:
        config = await ExportPermissionService.update_permission_config(db, config_id, update_data)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新权限配置失败: {str(e)}")


@router.delete("/configs/{config_id}", summary="删除导出权限配置")
async def delete_export_permission_config(
    config_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除导出权限配置（仅管理员）"""
    try:
        success = await ExportPermissionService.delete_permission_config(db, config_id)
        return {"success": success, "message": "权限配置已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除权限配置失败: {str(e)}")


@router.get("/check", response_model=ExportPermissionCheck, summary="检查当前用户导出权限")
async def check_export_permission(
    format: str,
    file_size_mb: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查当前用户的导出权限
    
    - **format**: 要导出的格式
    - **file_size_mb**: 文件大小(MB)
    """
    try:
        permission_check = await ExportPermissionService.check_export_permission(
            db, current_user, format, file_size_mb
        )
        return permission_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查导出权限失败: {str(e)}")


@router.get("/my-permissions", response_model=ExportPermissionCheck, summary="获取我的导出权限")
async def get_my_export_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的导出权限信息"""
    try:
        permission_check = await ExportPermissionService.get_user_export_permissions(
            db, current_user
        )
        return permission_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导出权限失败: {str(e)}")


@router.get("/stats", response_model=ExportStatsResponse, summary="获取导出统计信息")
async def get_export_stats(
    days: int = 7,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取导出统计信息（仅管理员）
    
    - **days**: 统计天数，默认7天
    """
    try:
        stats = await ExportPermissionService.get_export_stats(db, days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导出统计失败: {str(e)}")


@router.post("/init-defaults", summary="初始化默认权限配置")
async def init_default_export_configs(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """初始化默认的导出权限配置（仅管理员）"""
    try:
        await ExportPermissionService.init_default_configs(db)
        return {"success": True, "message": "默认权限配置已初始化"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化默认配置失败: {str(e)}")


@router.post("/log-export", summary="记录导出操作")
async def log_export_operation(
    task_id: int,
    export_format: str,
    file_size_mb: int = 0,
    status: str = "success",
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    记录导出操作（内部使用）
    
    - **task_id**: 任务ID
    - **export_format**: 导出格式
    - **file_size_mb**: 文件大小
    - **status**: 操作状态
    """
    try:
        # 获取客户端信息
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        log = await ExportPermissionService.log_export_attempt(
            db=db,
            user_id=current_user.id,
            task_id=task_id,
            export_format=export_format,
            file_size_mb=file_size_mb,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return {"success": True, "log_id": log.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录导出操作失败: {str(e)}")


# ==================== 用户专属权限管理API ====================

@router.post("/user-specific", response_model=UserSpecificPermissionResponse, summary="创建用户专属权限")
async def create_user_specific_permission(
    permission_data: CreateUserSpecificPermission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    创建用户专属导出权限配置
    
    - **user_id**: 用户ID
    - **allowed_formats**: 允许的导出格式列表
    - **max_exports_per_day**: 每日最大导出次数
    - **max_file_size_mb**: 最大文件大小(MB)
    - **description**: 配置描述
    """
    return await ExportPermissionService.create_user_specific_permission(db, permission_data)


@router.get("/user-specific", response_model=List[UserSpecificPermissionResponse], summary="获取所有用户专属权限")
async def get_user_specific_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    获取所有用户专属导出权限配置
    """
    return await ExportPermissionService.get_user_specific_permissions(db)


@router.put("/user-specific/{permission_id}", response_model=UserSpecificPermissionResponse, summary="更新用户专属权限")
async def update_user_specific_permission(
    permission_id: int,
    update_data: UpdateUserSpecificPermission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    更新用户专属导出权限配置
    
    - **permission_id**: 权限配置ID
    - **allowed_formats**: 允许的导出格式列表
    - **max_exports_per_day**: 每日最大导出次数
    - **max_file_size_mb**: 最大文件大小(MB)
    - **description**: 配置描述
    - **is_active**: 是否启用
    """
    return await ExportPermissionService.update_user_specific_permission(db, permission_id, update_data)


@router.delete("/user-specific/{permission_id}", summary="删除用户专属权限")
async def delete_user_specific_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    删除用户专属导出权限配置
    
    - **permission_id**: 权限配置ID
    """
    success = await ExportPermissionService.delete_user_specific_permission(db, permission_id)
    return {"success": success}
