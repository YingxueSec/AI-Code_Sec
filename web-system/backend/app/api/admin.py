from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.base import get_db
from app.core.deps import get_current_admin_user
from app.models.user import User
from app.models.audit import AuditTask, AuditResult
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/stats", summary="获取系统统计信息")
async def get_system_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    try:
        # 查询用户统计
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0
        
        # 查询任务统计
        total_tasks_result = await db.execute(select(func.count(AuditTask.id)))
        total_tasks = total_tasks_result.scalar() or 0
        
        completed_tasks_result = await db.execute(
            select(func.count(AuditTask.id)).where(AuditTask.status == 'completed')
        )
        completed_tasks = completed_tasks_result.scalar() or 0
        
        failed_tasks_result = await db.execute(
            select(func.count(AuditTask.id)).where(AuditTask.status == 'failed')
        )
        failed_tasks = failed_tasks_result.scalar() or 0
        
        # 查询今日API调用次数（模拟数据）
        today = datetime.now().date()
        
        # 查询今日token使用
        today_token_usage_result = await db.execute(
            select(func.sum(User.used_tokens_today))
        )
        today_token_usage = today_token_usage_result.scalar() or 0
        
        # 计算发现的问题总数（从审计结果中统计）
        total_issues_result = await db.execute(
            select(
                func.sum(AuditResult.high_issues + AuditResult.medium_issues + AuditResult.low_issues)
            )
        )
        total_issues_found = total_issues_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "total_issues_found": total_issues_found,
            "storage_used": 2.5,  # 模拟存储使用量
            "api_calls_today": today_token_usage  # 使用token使用量作为API调用次数的近似值
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")


@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    page: int = 1,
    page_size: int = 20,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    try:
        offset = (page - 1) * page_size
        result = await db.execute(
            select(User).offset(offset).limit(page_size).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.post("/users", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员创建用户"""
    try:
        user = await UserService.create_user(db, user_data)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建用户失败: {str(e)}")


@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员更新用户信息"""
    try:
        # 查询用户
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新用户信息
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"更新用户失败: {str(e)}")


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员删除用户"""
    try:
        # 不允许删除管理员自己
        if user_id == current_admin.id:
            raise HTTPException(status_code=400, detail="不能删除自己的账户")
        
        # 查询用户
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 删除用户
        await db.delete(user)
        await db.commit()
        
        return {"message": "用户删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"删除用户失败: {str(e)}")


@router.get("/logs", summary="获取系统日志")
async def get_system_logs(
    page: int = 1,
    page_size: int = 50,
    level: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统日志"""
    try:
        # 这里返回模拟的系统日志数据
        # 在实际项目中，你可能需要从日志文件或日志数据库中读取
        logs = []
        
        # 生成一些示例日志
        import random
        from datetime import datetime, timedelta
        
        log_levels = ['INFO', 'WARNING', 'ERROR']
        log_messages = [
            '用户登录系统',
            '审计任务开始执行',
            '审计任务完成',
            '审计任务执行失败',
            '文件上传成功',
            'AI服务连接失败',
            '数据库连接超时',
            '系统内存使用率过高',
            '新用户注册'
        ]
        
        for i in range(50):
            log_time = datetime.now() - timedelta(hours=random.randint(0, 72))
            logs.append({
                "id": i + 1,
                "timestamp": log_time.isoformat(),
                "level": random.choice(log_levels),
                "message": random.choice(log_messages),
                "ip_address": f"192.168.1.{random.randint(1, 255)}"
            })
        
        # 按时间倒序排列
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 应用分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = logs[start_idx:end_idx]
        
        return {
            "logs": paginated_logs,
            "total": len(logs),
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统日志失败: {str(e)}")


@router.get("/export-report", summary="导出系统报告")
async def export_system_report(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """导出系统报告"""
    try:
        import io
        import json
        from fastapi.responses import StreamingResponse
        
        # 获取系统统计信息
        stats_response = await get_system_stats(current_admin, db)
        users_response = await get_users(1, 1000, current_admin, db)  # 获取所有用户
        
        # 创建报告数据
        report_data = {
            "export_time": datetime.now().isoformat(),
            "system_stats": stats_response,
            "total_users_count": len(users_response),
            "users_summary": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "user_level": user.user_level,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users_response
            ]
        }
        
        # 转换为JSON字符串
        json_str = json.dumps(report_data, ensure_ascii=False, indent=2)
        
        # 创建文件流
        file_like = io.StringIO(json_str)
        
        # 返回文件下载响应
        return StreamingResponse(
            io.BytesIO(json_str.encode('utf-8')),
            media_type='application/json',
            headers={
                "Content-Disposition": f"attachment; filename=system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出系统报告失败: {str(e)}")


@router.get("/audit-records", summary="获取审计记录")
async def get_audit_records(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[int] = None,
    project_name: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取审计记录（管理员专用）"""
    try:
        # 构建查询条件
        query = select(
            AuditTask.id,
            AuditTask.user_id,
            AuditTask.project_name,
            AuditTask.description,
            AuditTask.status,
            AuditTask.total_files,
            AuditTask.analyzed_files,
            AuditTask.progress_percent,
            AuditTask.created_at,
            AuditTask.started_at,
            AuditTask.completed_at,
            AuditTask.error_message,
            User.username,
            User.email,
            User.user_level
        ).select_from(AuditTask).join(User, AuditTask.user_id == User.id)
        
        # 应用筛选条件
        if user_id:
            query = query.where(AuditTask.user_id == user_id)
        if project_name:
            query = query.where(AuditTask.project_name.ilike(f"%{project_name}%"))
        if status:
            query = query.where(AuditTask.status == status)
        if start_date:
            query = query.where(AuditTask.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.where(AuditTask.created_at <= datetime.fromisoformat(end_date))
        
        # 按创建时间降序排列
        query = query.order_by(AuditTask.created_at.desc())
        
        # 查询总数
        count_query = select(func.count(AuditTask.id)).select_from(AuditTask).join(User, AuditTask.user_id == User.id)
        if user_id:
            count_query = count_query.where(AuditTask.user_id == user_id)
        if project_name:
            count_query = count_query.where(AuditTask.project_name.ilike(f"%{project_name}%"))
        if status:
            count_query = count_query.where(AuditTask.status == status)
        if start_date:
            count_query = count_query.where(AuditTask.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            count_query = count_query.where(AuditTask.created_at <= datetime.fromisoformat(end_date))
            
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        records = result.fetchall()
        
        # 格式化返回数据
        audit_records = []
        for record in records:
            audit_record = {
                "id": record.id,
                "user_id": record.user_id,
                "username": record.username,
                "email": record.email,
                "user_level": record.user_level,
                "project_name": record.project_name,
                "description": record.description,
                "status": record.status,
                "total_files": record.total_files,
                "analyzed_files": record.analyzed_files,
                "progress_percent": record.progress_percent,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "started_at": record.started_at.isoformat() if record.started_at else None,
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "error_message": record.error_message,
                "duration": None
            }
            
            # 计算任务持续时间
            if record.started_at and record.completed_at:
                duration = record.completed_at - record.started_at
                audit_record["duration"] = str(duration).split('.')[0]  # 去掉微秒
            
            audit_records.append(audit_record)
        
        return {
            "records": audit_records,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审计记录失败: {str(e)}")
