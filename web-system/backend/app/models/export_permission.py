from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Enum, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class ExportFormat(str, enum.Enum):
    json = "json"
    markdown = "markdown" 
    pdf = "pdf"
    html = "html"
    csv = "csv"
    xml = "xml"


class ExportPermissionConfig(Base):
    """导出权限配置表"""
    __tablename__ = "export_permission_configs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_level = Column(String(50), nullable=False, index=True)  # free, standard, premium, admin
    allowed_formats = Column(JSON, nullable=False)  # 允许的导出格式列表
    max_exports_per_day = Column(BigInteger, default=10, nullable=False)  # 每日最大导出次数
    max_file_size_mb = Column(BigInteger, default=50, nullable=False)  # 最大文件大小(MB)
    description = Column(Text, nullable=True)  # 配置描述
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ExportPermissionConfig(id={self.id}, user_level='{self.user_level}', formats={self.allowed_formats})>"


class UserExportLog(Base):
    """用户导出记录表"""
    __tablename__ = "user_export_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    task_id = Column(BigInteger, nullable=False, index=True)
    export_format = Column(Enum(ExportFormat), nullable=False)
    file_size_mb = Column(BigInteger, default=0, nullable=False)
    export_status = Column(String(20), default="success", nullable=False)  # success, failed, blocked
    blocked_reason = Column(String(255), nullable=True)  # 被阻止的原因
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserExportLog(id={self.id}, user_id={self.user_id}, format='{self.export_format}', status='{self.export_status}')>"


class UserSpecificExportPermission(Base):
    """用户专属导出权限配置表"""
    __tablename__ = "user_specific_export_permissions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    allowed_formats = Column(JSON, nullable=False)  # 允许的导出格式列表
    max_exports_per_day = Column(BigInteger, default=0, nullable=False)
    max_file_size_mb = Column(BigInteger, default=0, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserSpecificExportPermission(id={self.id}, user_id={self.user_id}, formats={self.allowed_formats})>"
