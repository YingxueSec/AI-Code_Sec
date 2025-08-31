from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.audit import TaskStatus, FileStatus, ReportFormat


class AuditTaskCreate(BaseModel):
    project_name: str
    description: Optional[str] = None
    config_params: Optional[Dict[str, Any]] = None


class AuditTaskResponse(BaseModel):
    id: int
    user_id: int
    project_name: str
    description: Optional[str]
    status: TaskStatus
    config_params: Optional[Dict[str, Any]]
    error_message: Optional[str]
    total_files: int
    analyzed_files: int
    progress_percent: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuditTaskList(BaseModel):
    tasks: List[AuditTaskResponse]
    total: int
    page: int
    page_size: int


class AuditProgress(BaseModel):
    task_id: int
    status: TaskStatus
    progress_percent: float
    analyzed_files: int
    total_files: int
    error_message: Optional[str] = None


class SecurityFinding(BaseModel):
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    severity: str  # high, medium, low
    type: str
    description: str
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    language: Optional[str] = None


class AuditResultResponse(BaseModel):
    id: int
    task_id: int
    findings: List[SecurityFinding]
    statistics: Optional[Dict[str, Any]]
    summary: Optional[str]
    high_issues: int
    medium_issues: int
    low_issues: int
    total_confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class AuditFileResponse(BaseModel):
    id: int
    task_id: int
    file_path: str
    file_type: Optional[str]
    file_size: int
    analysis_result: Optional[List[SecurityFinding]]
    confidence_score: float
    status: FileStatus
    created_at: datetime

    class Config:
        from_attributes = True


class AuditConfig(BaseModel):
    template: str = "security_audit_chinese"
    max_files: int = 100
    enable_cross_file: bool = True
    enable_frontend_opt: bool = True
    enable_confidence_calc: bool = True
    min_confidence: float = 0.3
    max_confidence: float = 1.0
    quick_mode: bool = False


class ReportGenerate(BaseModel):
    task_id: int
    format: ReportFormat = ReportFormat.json
    include_code_snippets: bool = True


class ReportResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    report_name: str
    format: ReportFormat
    file_path: Optional[str]
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True
