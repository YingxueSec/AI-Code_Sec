from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class SetExportPermissionRequest(BaseModel):
    """设置导出权限请求"""
    allowed_formats: List[str] = Field(..., description="允许的导出格式列表")
    
    @validator('allowed_formats')
    def validate_formats(cls, v):
        valid_formats = {"json", "markdown", "pdf", "html"}
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f"不支持的导出格式: {fmt}")
        if not v:
            raise ValueError("至少需要允许一种导出格式")
        return v


class BatchSetPermissionRequest(BaseModel):
    """批量设置权限请求"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    allowed_formats: List[str] = Field(..., description="允许的导出格式列表")
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError("用户ID列表不能为空")
        return v
    
    @validator('allowed_formats')
    def validate_formats(cls, v):
        valid_formats = {"json", "markdown", "pdf", "html"}
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f"不支持的导出格式: {fmt}")
        if not v:
            raise ValueError("至少需要允许一种导出格式")
        return v


class UserExportPermissionResponse(BaseModel):
    """用户导出权限响应"""
    user_id: int
    username: str
    email: str
    role: str
    user_level: str
    allowed_formats: List[str]
    is_custom: bool = Field(description="是否为自定义权限（非默认）")
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserExportPermissionList(BaseModel):
    """用户导出权限列表响应"""
    items: List[UserExportPermissionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExportLogResponse(BaseModel):
    """导出日志响应"""
    id: int
    user_id: int
    username: Optional[str] = None
    task_id: int
    project_name: Optional[str] = None
    export_format: str
    file_name: str
    file_size: Optional[int] = None
    success: str
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    exported_at: datetime
    
    class Config:
        from_attributes = True


class ExportLogList(BaseModel):
    """导出日志列表响应"""
    items: List[ExportLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExportFormatInfo(BaseModel):
    """导出格式信息"""
    format: str
    name: str
    description: str
    icon: str = "file"


class UserExportFormatsResponse(BaseModel):
    """用户允许的导出格式响应"""
    allowed_formats: List[ExportFormatInfo]
    user_level: str
    user_role: str


class ExportStatsResponse(BaseModel):
    """导出统计响应"""
    today_exports: int
    week_exports: int
    total_exports: int
    success_rate: float
    format_stats: dict
    stats_time: datetime
