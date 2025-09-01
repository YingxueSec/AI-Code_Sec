from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from datetime import datetime

from app.db.base import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.audit import (
    AuditTaskCreate, AuditTaskResponse, AuditTaskList, AuditProgress,
    AuditResultResponse, AuditConfig, ReportGenerate, ReportResponse
)
from app.services.audit_service import AuditService
from app.services.task_queue_service import task_queue_service

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
    
    # 检查项目文件是否存在
    if not Path(project_path).exists():
        raise HTTPException(
            status_code=400, 
            detail=f"项目文件不存在，请重新上传项目文件。项目路径: {project_path}"
        )
    
    # 检查项目目录是否为空
    if not any(Path(project_path).iterdir()):
        raise HTTPException(
            status_code=400, 
            detail="项目目录为空，请上传有效的项目文件"
        )
    
    # 添加任务到队列
    queue_result = await task_queue_service.add_task_to_queue(
        task_id=task_id,
        user=current_user,
        project_path=project_path,
        db=db
    )
    
    return {
        "message": queue_result["message"],
        "task_id": task_id,
        "queue_status": queue_result
    }


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
    
    # 先尝试从队列中取消任务
    await task_queue_service.cancel_queued_task(task_id, db)
    
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
    format: str = "json",  # json, markdown, pdf, html
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出审计报告
    
    - **task_id**: 任务ID
    - **format**: 导出格式（json, markdown, pdf, html）
    """
    from pathlib import Path
    from app.core.config import settings
    from app.services.export_permission_service import ExportPermissionService
    
    # 验证任务权限
    task = await AuditService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务未完成，无法导出")
    
    # 获取文件大小（估算）
    report_file_path = None
    file_size_mb = 0
    
    if format == "json":
        report_file_path = Path(settings.REPORTS_PATH) / f"task_{task_id}_results.json"
    elif format == "markdown":
        report_file_path = Path(settings.REPORTS_PATH) / f"task_{task_id}_results_report.md"
    elif format == "pdf":
        report_file_path = Path(settings.REPORTS_PATH) / f"task_{task_id}_results_report.pdf"
    elif format == "html":
        report_file_path = Path(settings.REPORTS_PATH) / f"task_{task_id}_results_report.html"
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")
    
    # 计算文件大小
    if report_file_path and report_file_path.exists():
        file_size_bytes = report_file_path.stat().st_size
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    
    # 检查导出权限
    permission_check = await ExportPermissionService.check_export_permission(
        db, current_user, format, file_size_mb
    )
    
    if not permission_check.allowed:
        # 记录被阻止的导出尝试
        await ExportPermissionService.log_export_attempt(
            db=db,
            user_id=current_user.id,
            task_id=task_id,
            export_format=format,
            file_size_mb=file_size_mb,
            status="blocked",
            blocked_reason=permission_check.reason
        )
        raise HTTPException(
            status_code=403, 
            detail=f"导出权限不足: {permission_check.reason}。允许的格式: {', '.join(permission_check.allowed_formats)}"
        )
    
    # 检查文件是否存在并返回
    if report_file_path and report_file_path.exists():
        # 记录成功的导出操作
        await ExportPermissionService.log_export_attempt(
            db=db,
            user_id=current_user.id,
            task_id=task_id,
            export_format=format,
            file_size_mb=file_size_mb,
            status="success"
        )
        
        # 设置正确的媒体类型
        media_type_map = {
            "json": "application/json",
            "markdown": "text/markdown", 
            "pdf": "application/pdf",
            "html": "text/html"
        }
        
        return FileResponse(
            path=str(report_file_path),
            filename=f"{task.project_name}_audit_report.{format}",
            media_type=media_type_map.get(format, "application/octet-stream")
        )
    
    # 记录文件不存在的情况
    await ExportPermissionService.log_export_attempt(
        db=db,
        user_id=current_user.id,
        task_id=task_id,
        export_format=format,
        file_size_mb=0,
        status="failed",
        blocked_reason="报告文件不存在"
    )
    
    raise HTTPException(status_code=404, detail="报告文件不存在")


@router.get("/queue/status", summary="获取队列状态")
async def get_queue_status(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前队列状态
    
    返回队列长度、运行中任务数、用户位置等信息
    """
    
    # 获取全局队列状态
    queue_status = await task_queue_service.get_queue_status()
    
    # 获取当前用户的队列信息
    user_queue_info = await task_queue_service.get_user_queue_info(current_user.id)
    
    return {
        "global_status": queue_status,
        "user_status": user_queue_info,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/queue/cancel/{task_id}", summary="取消队列中的任务")
async def cancel_queued_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消队列中的任务
    
    - **task_id**: 任务ID
    """
    
    success = await task_queue_service.cancel_queued_task(task_id, db)
    if success:
        return {"message": "队列任务已取消", "task_id": task_id}
    else:
        raise HTTPException(status_code=400, detail="任务不在队列中或已开始执行")
