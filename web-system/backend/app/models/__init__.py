from .user import User, UserRole, UserLevel
from .audit import AuditTask, AuditResult, AuditFile, Report, TaskStatus, FileStatus, ReportFormat
from .token_usage import TokenUsage
from .export_permission import UserExportPermission, ExportLog

# 添加关系到User模型
from sqlalchemy.orm import relationship

# 动态添加关系（避免循环导入）
User.audit_tasks = relationship("AuditTask", back_populates="user")
User.reports = relationship("Report", back_populates="user")
User.token_usage = relationship("TokenUsage", back_populates="user")

__all__ = [
    "User", "UserRole", "UserLevel",
    "AuditTask", "AuditResult", "AuditFile", "Report",
    "TaskStatus", "FileStatus", "ReportFormat",
    "TokenUsage",
    "UserExportPermission", "ExportLog"
]
