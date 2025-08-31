from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, Integer, JSON, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class FileStatus(str, enum.Enum):
    pending = "pending"
    analyzed = "analyzed"
    skipped = "skipped"
    error = "error"


class ReportFormat(str, enum.Enum):
    json = "json"
    pdf = "pdf"
    html = "html"
    markdown = "markdown"


class AuditTask(Base):
    __tablename__ = "audit_tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    config_params = Column(JSON)
    error_message = Column(Text)
    total_files = Column(Integer, default=0)
    analyzed_files = Column(Integer, default=0)
    progress_percent = Column(DECIMAL(5, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # 关系
    user = relationship("User", back_populates="audit_tasks")
    audit_result = relationship("AuditResult", back_populates="task", uselist=False)
    audit_files = relationship("AuditFile", back_populates="task")
    reports = relationship("Report", back_populates="task")


class AuditResult(Base):
    __tablename__ = "audit_results"

    id = Column(BigInteger, primary_key=True, index=True)
    task_id = Column(BigInteger, ForeignKey("audit_tasks.id"), unique=True, nullable=False)
    findings = Column(JSON)
    statistics = Column(JSON)
    summary = Column(Text)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    total_confidence = Column(DECIMAL(5, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("AuditTask", back_populates="audit_result")


class AuditFile(Base):
    __tablename__ = "audit_files"

    id = Column(BigInteger, primary_key=True, index=True)
    task_id = Column(BigInteger, ForeignKey("audit_tasks.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50))
    file_size = Column(BigInteger, default=0)
    analysis_result = Column(JSON)
    confidence_score = Column(DECIMAL(5, 2), default=0.00)
    status = Column(Enum(FileStatus), default=FileStatus.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("AuditTask", back_populates="audit_files")


class Report(Base):
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True, index=True)
    task_id = Column(BigInteger, ForeignKey("audit_tasks.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    report_name = Column(String(255), nullable=False)
    format = Column(Enum(ReportFormat), default=ReportFormat.json, nullable=False)
    file_path = Column(Text)
    file_size = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("AuditTask", back_populates="reports")
    user = relationship("User", back_populates="reports")
