from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.db.base import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.audit import (
    AuditTaskCreate, AuditTaskResponse, AuditTaskList, AuditProgress,
    AuditResultResponse, AuditConfig, ReportGenerate, ReportResponse
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["代码审计"])


@router.post("/upload", response_model=AuditTaskResponse, summary="上传项目文件并创建审计任务")
async def upload_project(
    project_name: str = Form(..., description="项目名称"),
    description: Optional[str] = Form(None, description="项目描述"),
    config: Optional[str] = Form(None, description="审计配置JSON"),
    files: List[UploadFile] = File(..., description="项目文件或压缩包"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传项目文件并创建审计任务
    
    - **project_name**: 项目名称
    - **description**: 项目描述（可选）
    - **config**: 审计配置JSON字符串（可选）
    - **files**: 项目文件或压缩包（支持.zip）
    """
    
    # 验证文件
    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个文件")
    
    # 解析配置
    config_params = None
    if config:
        try:
            config_params = json.loads(config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="配置JSON格式错误")
    
    # 创建审计任务
    task = await AuditService.create_audit_task(
        db=db,
        user=current_user,
        project_name=project_name,
        description=description,
        config_params=config_params
    )
    
    try:
        # 上传并处理文件
        project_path = await AuditService.upload_project_files(
            task_id=task.id,
            files=files,
            db=db
        )
        
        return task
        
    except Exception as e:
        # 如果上传失败，删除任务
        await AuditService.delete_task(db, task.id, current_user.id)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start/{task_id}", response_model=dict, summary="开始审计分析")
async def start_audit(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    开始对已上传的项目进行审计分析
    
    - **task_id**: 任务ID
    """
    
    # 验证任务
    task = await AuditService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="任务状态不允许启动分析")
    
    # 构建项目路径
    from pathlib import Path
    from app.core.config import settings
    project_path = str(Path(settings.UPLOAD_PATH) / str(task_id) / "project")
    
    # 启动审计分析
    success = await AuditService.start_audit_analysis(
        task_id=task_id,
        project_path=project_path,
        user=current_user,
        db=db
    )
    
    if success:
        return {"message": "审计分析已启动", "task_id": task_id}
    else:
        raise HTTPException(status_code=500, detail="启动审计分析失败")


@router.get("/tasks", response_model=AuditTaskList, summary="获取用户的审计任务列表")
async def get_user_tasks(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的审计任务列表
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    """
    
    skip = (page - 1) * page_size
    tasks = await AuditService.get_user_tasks(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size
    )
    
    # TODO: 实现总数统计
    total = len(tasks)  # 简化版本，实际应该查询总数
    
    return AuditTaskList(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tasks/{task_id}", response_model=AuditTaskResponse, summary="获取审计任务详情")
async def get_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定审计任务的详细信息
    
    - **task_id**: 任务ID
    """
    
    task = await AuditService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task


@router.get("/tasks/{task_id}/progress", response_model=AuditProgress, summary="获取任务进度")
async def get_task_progress(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计任务的实时进度
    
    - **task_id**: 任务ID
    """
    
    task = await AuditService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return AuditProgress(
        task_id=task.id,
        status=task.status,
        progress_percent=task.progress_percent,
        analyzed_files=task.analyzed_files,
        total_files=task.total_files,
        error_message=task.error_message
    )


@router.get("/results/{task_id}", response_model=AuditResultResponse, summary="获取审计结果")
async def get_audit_results(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计任务的分析结果
    
    - **task_id**: 任务ID
    """
    
    result = await AuditService.get_task_results(db, task_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="审计结果不存在或任务未完成")
    
    return result


@router.post("/tasks/{task_id}/cancel", summary="取消审计任务")
async def cancel_audit_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消正在进行的审计任务
    
    - **task_id**: 任务ID
    """
    
    success = await AuditService.cancel_task(db, task_id, current_user.id)
    if success:
        return {"message": "任务已取消"}
    else:
        raise HTTPException(status_code=400, detail="无法取消该任务")


@router.delete("/tasks/{task_id}", summary="删除审计任务")
async def delete_audit_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除审计任务及相关文件
    
    - **task_id**: 任务ID
    """
    
    success = await AuditService.delete_task(db, task_id, current_user.id)
    if success:
        return {"message": "任务已删除"}
    else:
        raise HTTPException(status_code=400, detail="删除任务失败")


@router.get("/templates", summary="获取可用的审计模板")
async def get_audit_templates():
    """
    获取系统支持的审计模板列表
    """
    
    templates = [
        {
            "name": "security_audit_chinese",
            "display_name": "中文安全审计",
            "description": "全面的中文安全漏洞检测模板"
        },
        {
            "name": "owasp_top_10_2021", 
            "display_name": "OWASP Top 10 2021",
            "description": "基于OWASP Top 10 2021的安全检测"
        },
        {
            "name": "code_quality",
            "display_name": "代码质量检查",
            "description": "代码质量和最佳实践检查"
        }
    ]
    
    return {"templates": templates}


@router.get("/results/{task_id}/export", summary="导出审计报告")
async def export_audit_report(
    task_id: int,
    request: Request,
    format: str = "json",  # json, markdown, pdf, html
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出审计报告
    
    - **task_id**: 任务ID
    - **format**: 导出格式（json, markdown, pdf, html）
    """
    from app.services.export_permission_service import ExportPermissionService
    
    # 验证任务权限
    task = await AuditService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务未完成，无法导出")
    
    # 检查用户导出格式权限
    if not await ExportPermissionService.check_export_permission(db, current_user.id, format):
        allowed_formats = await ExportPermissionService.get_user_allowed_formats(db, current_user.id)
        raise HTTPException(
            status_code=403, 
            detail=f"您没有导出 {format} 格式的权限。允许的格式: {', '.join(allowed_formats)}"
        )
    
    # 获取报告文件路径
    from pathlib import Path
    from app.core.config import settings
    import os
    
    report_file = None
    media_type = "application/octet-stream"
    filename = f"{task.project_name}_audit_report.{format}"
    
    if format == "json":
        report_file = Path(settings.REPORTS_PATH) / f"task_{task_id}_results.json"
        media_type = "application/json"
    elif format == "markdown":
        report_file = Path(settings.REPORTS_PATH) / f"task_{task_id}_results_report.md"
        media_type = "text/markdown"
    elif format == "pdf":
        # PDF格式暂时返回JSON（后续可扩展PDF生成）
        report_file = Path(settings.REPORTS_PATH) / f"task_{task_id}_results.json"
        media_type = "application/pdf"
        filename = f"{task.project_name}_audit_report.pdf"
    elif format == "html":
        # HTML格式暂时返回JSON（后续可扩展HTML生成）
        report_file = Path(settings.REPORTS_PATH) / f"task_{task_id}_results.json"
        media_type = "text/html"
        filename = f"{task.project_name}_audit_report.html"
    
    if not report_file or not report_file.exists():
        # 记录失败的导出日志
        await ExportPermissionService.log_export_operation(
            db=db,
            user_id=current_user.id,
            task_id=task_id,
            export_format=format,
            file_name=filename,
            success="failed",
            error_message="报告文件不存在",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        raise HTTPException(status_code=404, detail="报告文件不存在")
    
    # 记录成功的导出日志
    file_size = os.path.getsize(report_file) if report_file.exists() else None
    await ExportPermissionService.log_export_operation(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
        export_format=format,
        file_name=filename,
        file_size=file_size,
        success="success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return FileResponse(
        path=str(report_file),
        filename=filename,
        media_type=media_type
    )


@router.get("/export/formats", summary="获取用户允许的导出格式")
async def get_user_export_formats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户允许的导出格式列表
    """
    from app.services.export_permission_service import ExportPermissionService
    
    allowed_formats = await ExportPermissionService.get_user_allowed_formats(db, current_user.id)
    
    # 格式描述映射
    format_descriptions = {
        "json": {"name": "JSON", "description": "结构化数据格式", "icon": "file-text"},
        "markdown": {"name": "Markdown", "description": "Markdown文档格式", "icon": "file-markdown"},
        "pdf": {"name": "PDF", "description": "便携式文档格式", "icon": "file-pdf"},
        "html": {"name": "HTML", "description": "网页格式", "icon": "global"}
    }
    
    return {
        "allowed_formats": [
            {
                "format": fmt,
                **format_descriptions.get(fmt, {"name": fmt.upper(), "description": f"{fmt.upper()}格式", "icon": "file"})
            }
            for fmt in allowed_formats
        ],
        "user_level": current_user.user_level,
        "user_role": current_user.role
    }
