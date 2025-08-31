from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.export_permission import ExportPermissionConfig, UserExportLog, ExportFormat, UserSpecificExportPermission
from app.models.user import User, UserLevel
from app.schemas.export_permission import (
    ExportPermissionConfigCreate, 
    ExportPermissionConfigUpdate,
    ExportPermissionCheck,
    ExportStatsResponse,
    CreateUserSpecificPermission,
    UpdateUserSpecificPermission,
    UserSpecificPermissionResponse
)
from fastapi import HTTPException


class ExportPermissionService:
    """导出权限管理服务"""

    @staticmethod
    async def create_permission_config(
        db: AsyncSession,
        config_data: ExportPermissionConfigCreate
    ) -> ExportPermissionConfig:
        """创建导出权限配置"""
        
        # 检查该用户等级是否已有配置
        existing = await db.execute(
            select(ExportPermissionConfig).where(
                and_(
                    ExportPermissionConfig.user_level == config_data.user_level,
                    ExportPermissionConfig.is_active == True
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"用户等级 {config_data.user_level} 已存在配置")

        # 创建新配置
        config = ExportPermissionConfig(
            user_level=config_data.user_level,
            allowed_formats=[format.value for format in config_data.allowed_formats],
            max_exports_per_day=config_data.max_exports_per_day,
            max_file_size_mb=config_data.max_file_size_mb,
            description=config_data.description
        )
        
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def update_permission_config(
        db: AsyncSession,
        config_id: int,
        update_data: ExportPermissionConfigUpdate
    ) -> ExportPermissionConfig:
        """更新导出权限配置"""
        
        config = await db.execute(
            select(ExportPermissionConfig).where(ExportPermissionConfig.id == config_id)
        )
        config = config.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        # 更新字段
        if update_data.allowed_formats is not None:
            config.allowed_formats = [format.value for format in update_data.allowed_formats]
        if update_data.max_exports_per_day is not None:
            config.max_exports_per_day = update_data.max_exports_per_day
        if update_data.max_file_size_mb is not None:
            config.max_file_size_mb = update_data.max_file_size_mb
        if update_data.description is not None:
            config.description = update_data.description
        if update_data.is_active is not None:
            config.is_active = update_data.is_active

        config.updated_at = datetime.now()
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def get_permission_configs(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20
    ) -> List[ExportPermissionConfig]:
        """获取所有导出权限配置"""
        
        offset = (page - 1) * page_size
        result = await db.execute(
            select(ExportPermissionConfig)
            .where(ExportPermissionConfig.is_active == True)
            .order_by(desc(ExportPermissionConfig.created_at))
            .offset(offset)
            .limit(page_size)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_permission_config(db: AsyncSession, config_id: int) -> bool:
        """删除导出权限配置（软删除）"""
        
        config = await db.execute(
            select(ExportPermissionConfig).where(ExportPermissionConfig.id == config_id)
        )
        config = config.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        config.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def check_export_permission(
        db: AsyncSession,
        user: User,
        export_format: str,
        file_size_mb: int = 0
    ) -> ExportPermissionCheck:
        """检查用户导出权限"""
        
        # 管理员拥有所有权限
        if user.role.value == "admin":
            return ExportPermissionCheck(
                allowed=True,
                allowed_formats=["json", "markdown", "pdf", "html", "csv", "xml"],
                remaining_exports_today=999,
                max_file_size_mb=1000
            )

        # 1. 优先检查用户专属权限配置
        user_specific_config = await db.execute(
            select(UserSpecificExportPermission).where(
                and_(
                    UserSpecificExportPermission.user_id == user.id,
                    UserSpecificExportPermission.is_active == True
                )
            )
        )
        user_specific_config = user_specific_config.scalar_one_or_none()
        
        # 如果有用户专属配置，使用专属配置
        if user_specific_config:
            config = user_specific_config
        else:
            # 2. 否则使用用户等级对应的权限配置
            config = await db.execute(
                select(ExportPermissionConfig).where(
                    and_(
                        ExportPermissionConfig.user_level == user.user_level.value,
                        ExportPermissionConfig.is_active == True
                    )
                )
            )
            config = config.scalar_one_or_none()
        
        if not config:
            # 如果没有配置，使用默认限制
            return ExportPermissionCheck(
                allowed=False,
                allowed_formats=[],
                remaining_exports_today=0,
                max_file_size_mb=0,
                reason="未找到用户等级权限配置"
            )

        # 检查格式是否允许
        if export_format not in config.allowed_formats:
            return ExportPermissionCheck(
                allowed=False,
                allowed_formats=config.allowed_formats,
                remaining_exports_today=0,
                max_file_size_mb=config.max_file_size_mb,
                reason=f"不支持 {export_format} 格式导出"
            )

        # 检查文件大小限制
        if file_size_mb > config.max_file_size_mb:
            return ExportPermissionCheck(
                allowed=False,
                allowed_formats=config.allowed_formats,
                remaining_exports_today=0,
                max_file_size_mb=config.max_file_size_mb,
                reason=f"文件大小超出限制 ({file_size_mb}MB > {config.max_file_size_mb}MB)"
            )

        # 检查今日导出次数
        today = datetime.now().date()
        exports_today = await db.execute(
            select(func.count(UserExportLog.id)).where(
                and_(
                    UserExportLog.user_id == user.id,
                    UserExportLog.export_status == "success",
                    func.date(UserExportLog.created_at) == today
                )
            )
        )
        exports_count = exports_today.scalar() or 0
        
        remaining_exports = config.max_exports_per_day - exports_count
        if remaining_exports <= 0:
            return ExportPermissionCheck(
                allowed=False,
                allowed_formats=config.allowed_formats,
                remaining_exports_today=0,
                max_file_size_mb=config.max_file_size_mb,
                reason="今日导出次数已达上限"
            )

        return ExportPermissionCheck(
            allowed=True,
            allowed_formats=config.allowed_formats,
            remaining_exports_today=remaining_exports,
            max_file_size_mb=config.max_file_size_mb
        )

    @staticmethod
    async def log_export_attempt(
        db: AsyncSession,
        user_id: int,
        task_id: int,
        export_format: str,
        file_size_mb: int = 0,
        status: str = "success",
        blocked_reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> UserExportLog:
        """记录导出尝试"""
        
        log = UserExportLog(
            user_id=user_id,
            task_id=task_id,
            export_format=export_format,
            file_size_mb=file_size_mb,
            export_status=status,
            blocked_reason=blocked_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_export_stats(
        db: AsyncSession,
        days: int = 7
    ) -> ExportStatsResponse:
        """获取导出统计信息"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 总导出次数
        total_exports = await db.execute(
            select(func.count(UserExportLog.id)).where(
                and_(
                    UserExportLog.created_at >= start_date,
                    UserExportLog.export_status == "success"
                )
            )
        )
        total_count = total_exports.scalar() or 0

        # 按格式统计
        format_stats = await db.execute(
            select(
                UserExportLog.export_format,
                func.count(UserExportLog.id).label('count')
            ).where(
                and_(
                    UserExportLog.created_at >= start_date,
                    UserExportLog.export_status == "success"
                )
            ).group_by(UserExportLog.export_format)
        )
        exports_by_format = {row.export_format: row.count for row in format_stats}

        # 被阻止的导出次数
        blocked_exports = await db.execute(
            select(func.count(UserExportLog.id)).where(
                and_(
                    UserExportLog.created_at >= start_date,
                    UserExportLog.export_status == "blocked"
                )
            )
        )
        blocked_count = blocked_exports.scalar() or 0

        # 平均文件大小
        avg_size = await db.execute(
            select(func.avg(UserExportLog.file_size_mb)).where(
                and_(
                    UserExportLog.created_at >= start_date,
                    UserExportLog.export_status == "success",
                    UserExportLog.file_size_mb > 0
                )
            )
        )
        average_file_size = round(avg_size.scalar() or 0, 2)

        return ExportStatsResponse(
            total_exports_today=total_count,
            exports_by_format=exports_by_format,
            exports_by_user_level={},  # 可以后续添加
            blocked_exports=blocked_count,
            average_file_size=average_file_size
        )

    @staticmethod
    async def init_default_configs(db: AsyncSession):
        """初始化默认的导出权限配置"""
        
        default_configs = [
            {
                "user_level": "free",
                "allowed_formats": ["json"],
                "max_exports_per_day": 3,
                "max_file_size_mb": 10,
                "description": "免费用户：仅支持JSON格式，每日3次，最大10MB"
            },
            {
                "user_level": "standard", 
                "allowed_formats": ["json", "markdown"],
                "max_exports_per_day": 10,
                "max_file_size_mb": 50,
                "description": "标准用户：支持JSON和Markdown格式，每日10次，最大50MB"
            },
            {
                "user_level": "premium",
                "allowed_formats": ["json", "markdown", "pdf", "html"],
                "max_exports_per_day": 50,
                "max_file_size_mb": 200,
                "description": "高级用户：支持多种格式，每日50次，最大200MB"
            }
        ]

        for config_data in default_configs:
            # 检查是否已存在
            existing = await db.execute(
                select(ExportPermissionConfig).where(
                    ExportPermissionConfig.user_level == config_data["user_level"]
                )
            )
            if not existing.scalar_one_or_none():
                config = ExportPermissionConfig(**config_data)
                db.add(config)

        await db.commit()

    # ==================== 用户专属权限管理方法 ====================
    
    @staticmethod
    async def create_user_specific_permission(
        db: AsyncSession,
        permission_data: CreateUserSpecificPermission
    ) -> UserSpecificPermissionResponse:
        """创建用户专属权限配置"""
        
        # 检查用户是否存在
        user = await db.execute(select(User).where(User.id == permission_data.user_id))
        user = user.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查是否已有配置
        existing = await db.execute(
            select(UserSpecificExportPermission).where(
                UserSpecificExportPermission.user_id == permission_data.user_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该用户已有专属权限配置")
        
        # 创建配置
        permission = UserSpecificExportPermission(
            user_id=permission_data.user_id,
            allowed_formats=[format.value for format in permission_data.allowed_formats],
            max_exports_per_day=permission_data.max_exports_per_day,
            max_file_size_mb=permission_data.max_file_size_mb,
            description=permission_data.description
        )
        
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        
        # 返回响应
        return UserSpecificPermissionResponse(
            id=permission.id,
            user_id=permission.user_id,
            username=user.username,
            allowed_formats=permission.allowed_formats,
            max_exports_per_day=permission.max_exports_per_day,
            max_file_size_mb=permission.max_file_size_mb,
            description=permission.description,
            is_active=permission.is_active,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
    
    @staticmethod
    async def get_user_specific_permissions(db: AsyncSession) -> List[UserSpecificPermissionResponse]:
        """获取所有用户专属权限配置"""
        
        result = await db.execute(
            select(UserSpecificExportPermission, User.username)
            .join(User, UserSpecificExportPermission.user_id == User.id)
            .order_by(UserSpecificExportPermission.created_at.desc())
        )
        
        permissions = []
        for permission, username in result.all():
            permissions.append(UserSpecificPermissionResponse(
                id=permission.id,
                user_id=permission.user_id,
                username=username,
                allowed_formats=permission.allowed_formats,
                max_exports_per_day=permission.max_exports_per_day,
                max_file_size_mb=permission.max_file_size_mb,
                description=permission.description,
                is_active=permission.is_active,
                created_at=permission.created_at,
                updated_at=permission.updated_at
            ))
        
        return permissions
    
    @staticmethod
    async def update_user_specific_permission(
        db: AsyncSession,
        permission_id: int,
        update_data: UpdateUserSpecificPermission
    ) -> UserSpecificPermissionResponse:
        """更新用户专属权限配置"""
        
        permission = await db.execute(
            select(UserSpecificExportPermission).where(UserSpecificExportPermission.id == permission_id)
        )
        permission = permission.scalar_one_or_none()
        if not permission:
            raise HTTPException(status_code=404, detail="权限配置不存在")
        
        # 更新字段
        if update_data.allowed_formats is not None:
            permission.allowed_formats = [format.value for format in update_data.allowed_formats]
        if update_data.max_exports_per_day is not None:
            permission.max_exports_per_day = update_data.max_exports_per_day
        if update_data.max_file_size_mb is not None:
            permission.max_file_size_mb = update_data.max_file_size_mb
        if update_data.description is not None:
            permission.description = update_data.description
        if update_data.is_active is not None:
            permission.is_active = update_data.is_active
        
        await db.commit()
        await db.refresh(permission)
        
        # 获取用户名
        user = await db.execute(select(User).where(User.id == permission.user_id))
        user = user.scalar_one_or_none()
        
        return UserSpecificPermissionResponse(
            id=permission.id,
            user_id=permission.user_id,
            username=user.username if user else None,
            allowed_formats=permission.allowed_formats,
            max_exports_per_day=permission.max_exports_per_day,
            max_file_size_mb=permission.max_file_size_mb,
            description=permission.description,
            is_active=permission.is_active,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
    
    @staticmethod
    async def delete_user_specific_permission(db: AsyncSession, permission_id: int) -> bool:
        """删除用户专属权限配置"""
        
        permission = await db.execute(
            select(UserSpecificExportPermission).where(UserSpecificExportPermission.id == permission_id)
        )
        permission = permission.scalar_one_or_none()
        if not permission:
            raise HTTPException(status_code=404, detail="权限配置不存在")
        
        await db.delete(permission)
        await db.commit()
        return True

    @staticmethod
    async def get_user_export_permissions(
        db: AsyncSession,
        user: User
    ) -> ExportPermissionCheck:
        """获取用户的完整导出权限信息（不检查特定格式）"""
        
        # 管理员拥有所有权限
        if user.role.value == "admin":
            return ExportPermissionCheck(
                allowed=True,
                allowed_formats=["json", "markdown", "pdf", "html", "csv", "xml"],
                remaining_exports_today=999,
                max_file_size_mb=1000
            )

        # 1. 优先检查用户专属权限配置
        user_specific_config = await db.execute(
            select(UserSpecificExportPermission).where(
                and_(
                    UserSpecificExportPermission.user_id == user.id,
                    UserSpecificExportPermission.is_active == True
                )
            )
        )
        user_specific_config = user_specific_config.scalar_one_or_none()
        
        # 如果有用户专属配置，使用专属配置
        if user_specific_config:
            config = user_specific_config
        else:
            # 2. 否则使用用户等级对应的权限配置
            config = await db.execute(
                select(ExportPermissionConfig).where(
                    and_(
                        ExportPermissionConfig.user_level == user.user_level.value,
                        ExportPermissionConfig.is_active == True
                    )
                )
            )
            config = config.scalar_one_or_none()
        
        if not config:
            # 如果没有配置，使用默认限制
            return ExportPermissionCheck(
                allowed=False,
                allowed_formats=[],
                remaining_exports_today=0,
                max_file_size_mb=0,
                reason="未找到用户权限配置"
            )

        # 检查今日导出次数
        today = datetime.now().date()
        exports_today = await db.execute(
            select(func.count(UserExportLog.id)).where(
                and_(
                    UserExportLog.user_id == user.id,
                    UserExportLog.export_status == "success",
                    func.date(UserExportLog.created_at) == today
                )
            )
        )
        exports_count = exports_today.scalar() or 0
        
        remaining_exports = config.max_exports_per_day - exports_count
        
        return ExportPermissionCheck(
            allowed=True,
            allowed_formats=config.allowed_formats,
            remaining_exports_today=max(0, remaining_exports),
            max_file_size_mb=config.max_file_size_mb,
            reason=None
        )
