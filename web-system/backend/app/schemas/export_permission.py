from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.export_permission import ExportFormat


class ExportPermissionConfigCreate(BaseModel):
    """创建导出权限配置"""
    user_level: str = Field(..., description="用户等级")
    allowed_formats: List[ExportFormat] = Field(..., description="允许的导出格式")
    max_exports_per_day: int = Field(10, description="每日最大导出次数")
    max_file_size_mb: int = Field(50, description="最大文件大小(MB)")
    description: Optional[str] = Field(None, description="配置描述")


class ExportPermissionConfigUpdate(BaseModel):
    """更新导出权限配置"""
    allowed_formats: Optional[List[ExportFormat]] = None
    max_exports_per_day: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExportPermissionConfigResponse(BaseModel):
    """导出权限配置响应"""
    id: int
    user_level: str
    allowed_formats: List[str]
    max_exports_per_day: int
    max_file_size_mb: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserExportLogResponse(BaseModel):
    """用户导出记录响应"""
    id: int
    user_id: int
    task_id: int
    export_format: str
    file_size_mb: int
    export_status: str
    blocked_reason: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExportPermissionCheck(BaseModel):
    """导出权限检查结果"""
    allowed: bool
    allowed_formats: List[str]
    remaining_exports_today: int
    max_file_size_mb: int
    reason: Optional[str] = None


class ExportStatsResponse(BaseModel):
    """导出统计响应"""
    total_exports_today: int
    exports_by_format: dict
    exports_by_user_level: dict
    blocked_exports: int
    average_file_size: float


# 用户专属权限相关schemas
class CreateUserSpecificPermission(BaseModel):
    """创建用户专属权限"""
    user_id: int = Field(..., description="用户ID")
    allowed_formats: List[ExportFormat] = Field(..., description="允许的导出格式")
    max_exports_per_day: int = Field(10, description="每日最大导出次数")
    max_file_size_mb: int = Field(50, description="最大文件大小(MB)")
    description: Optional[str] = Field(None, description="配置描述")


class UpdateUserSpecificPermission(BaseModel):
    """更新用户专属权限"""
    allowed_formats: Optional[List[ExportFormat]] = None
    max_exports_per_day: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class UserSpecificPermissionResponse(BaseModel):
    """用户专属权限响应"""
    id: int
    user_id: int
    username: Optional[str] = None  # 用户名，用于显示
    allowed_formats: List[str]
    max_exports_per_day: int
    max_file_size_mb: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
