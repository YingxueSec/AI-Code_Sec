from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole, UserLevel
from app.models.export_permission import UserExportPermission, ExportLog
from app.models.audit import ReportFormat
from datetime import datetime


class ExportPermissionService:
    """导出权限管理服务"""

    # 默认权限配置
    DEFAULT_PERMISSIONS = {
        UserLevel.free: ["json"],
        UserLevel.standard: ["json", "markdown"],
        UserLevel.premium: ["json", "markdown", "pdf"],
    }

    @staticmethod
    async def get_user_allowed_formats(db: AsyncSession, user_id: int) -> List[str]:
        """获取用户允许的导出格式"""
        # 查询用户信息
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []

        # 管理员拥有所有格式权限
        if user.role == UserRole.admin:
            return ["json", "markdown", "pdf", "html"]

        # 查询自定义权限配置
        permission_result = await db.execute(
            select(UserExportPermission).where(UserExportPermission.user_id == user_id)
        )
        permission = permission_result.scalar_one_or_none()

        if permission:
            return permission.allowed_formats

        # 使用默认权限配置
        return ExportPermissionService.DEFAULT_PERMISSIONS.get(user.user_level, ["json"])

    @staticmethod
    async def check_export_permission(db: AsyncSession, user_id: int, format: str) -> bool:
        """检查用户是否有指定格式的导出权限"""
        allowed_formats = await ExportPermissionService.get_user_allowed_formats(db, user_id)
        return format in allowed_formats

    @staticmethod
    async def set_user_export_permission(
        db: AsyncSession, 
        user_id: int, 
        allowed_formats: List[str], 
        admin_id: int
    ) -> bool:
        """设置用户导出权限（管理员操作）"""
        try:
            # 验证格式有效性
            valid_formats = ["json", "markdown", "pdf", "html"]
            for fmt in allowed_formats:
                if fmt not in valid_formats:
                    return False

            # 查找现有权限配置
            existing_result = await db.execute(
                select(UserExportPermission).where(UserExportPermission.user_id == user_id)
            )
            existing_permission = existing_result.scalar_one_or_none()

            if existing_permission:
                # 更新现有配置
                await db.execute(
                    update(UserExportPermission)
                    .where(UserExportPermission.user_id == user_id)
                    .values(
                        allowed_formats=allowed_formats,
                        updated_by=admin_id,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # 创建新配置
                new_permission = UserExportPermission(
                    user_id=user_id,
                    allowed_formats=allowed_formats,
                    updated_by=admin_id
                )
                db.add(new_permission)

            await db.commit()
            return True

        except Exception:
            await db.rollback()
            return False

    @staticmethod
    async def get_all_user_permissions(
        db: AsyncSession, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取所有用户的导出权限配置"""
        offset = (page - 1) * page_size

        # 查询用户及其权限配置
        query = (
            select(User)
            .options(selectinload(User.export_permission))
            .offset(offset)
            .limit(page_size)
        )
        
        result = await db.execute(query)
        users = result.scalars().all()

        # 统计总数
        count_result = await db.execute(select(func.count(User.id)))
        total = count_result.scalar()

        # 构建响应数据
        user_permissions = []
        for user in users:
            # 获取用户允许的格式
            allowed_formats = await ExportPermissionService.get_user_allowed_formats(db, user.id)
            
            # 获取最新的导出权限记录
            latest_permission = None
            if hasattr(user, 'export_permissions') and user.export_permissions:
                # 如果是列表，取最新的一个
                if isinstance(user.export_permissions, list):
                    latest_permission = user.export_permissions[0] if user.export_permissions else None
                else:
                    latest_permission = user.export_permissions
            elif hasattr(user, 'export_permission'):
                # 如果是单个对象
                if isinstance(user.export_permission, list):
                    latest_permission = user.export_permission[0] if user.export_permission else None
                else:
                    latest_permission = user.export_permission
            
            user_permissions.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "user_level": user.user_level,
                "allowed_formats": allowed_formats,
                "is_custom": latest_permission is not None,
                "updated_at": latest_permission.updated_at if latest_permission else None
            })

        return {
            "items": user_permissions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def reset_user_permission(db: AsyncSession, user_id: int) -> bool:
        """重置用户权限到默认配置"""
        try:
            await db.execute(
                delete(UserExportPermission).where(UserExportPermission.user_id == user_id)
            )
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False

    @staticmethod
    async def log_export_operation(
        db: AsyncSession,
        user_id: int,
        task_id: int,
        export_format: str,
        file_name: str,
        file_size: Optional[int] = None,
        success: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录导出操作日志"""
        try:
            export_log = ExportLog(
                user_id=user_id,
                task_id=task_id,
                export_format=export_format,
                file_name=file_name,
                file_size=file_size,
                success=success,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(export_log)
            await db.commit()
        except Exception:
            await db.rollback()

    @staticmethod
    async def get_export_logs(
        db: AsyncSession,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """获取导出操作日志"""
        offset = (page - 1) * page_size

        query = (
            select(ExportLog)
            .options(selectinload(ExportLog.user), selectinload(ExportLog.task))
            .order_by(ExportLog.exported_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        if user_id:
            query = query.where(ExportLog.user_id == user_id)

        result = await db.execute(query)
        logs = result.scalars().all()

        # 统计总数
        count_query = select(func.count(ExportLog.id))
        if user_id:
            count_query = count_query.where(ExportLog.user_id == user_id)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        return {
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "task_id": log.task_id,
                    "project_name": log.task.project_name if log.task else None,
                    "export_format": log.export_format,
                    "file_name": log.file_name,
                    "file_size": log.file_size,
                    "success": log.success,
                    "error_message": log.error_message,
                    "ip_address": log.ip_address,
                    "exported_at": log.exported_at
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    async def batch_set_permissions(
        db: AsyncSession,
        user_ids: List[int],
        allowed_formats: List[str],
        admin_id: int
    ) -> Dict[str, int]:
        """批量设置用户导出权限"""
        success_count = 0
        failed_count = 0

        for user_id in user_ids:
            if await ExportPermissionService.set_user_export_permission(
                db, user_id, allowed_formats, admin_id
            ):
                success_count += 1
            else:
                failed_count += 1

        return {"success": success_count, "failed": failed_count}
