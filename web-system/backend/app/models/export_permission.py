from sqlalchemy import Column, BigInteger, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from typing import List


class UserExportPermission(Base):
    """用户导出权限配置"""
    __tablename__ = "user_export_permissions"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    allowed_formats = Column(JSON, nullable=False, default=lambda: ["json"])  # 允许的导出格式列表
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)  # 更新者（管理员ID）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", foreign_keys=[user_id], backref="export_permission")
    updated_by_user = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<UserExportPermission(user_id={self.user_id}, formats={self.allowed_formats})>"


class ExportLog(Base):
    """导出操作日志"""
    __tablename__ = "export_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(BigInteger, ForeignKey("audit_tasks.id", ondelete="CASCADE"), nullable=False)
    export_format = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=True)  # 文件大小（字节）
    success = Column(String(10), nullable=False, default="success")  # success, failed
    error_message = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # 支持IPv6
    user_agent = Column(String(500), nullable=True)
    exported_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", backref="export_logs")
    task = relationship("AuditTask", backref="export_logs")

    def __repr__(self):
        return f"<ExportLog(user_id={self.user_id}, task_id={self.task_id}, format={self.export_format})>"
