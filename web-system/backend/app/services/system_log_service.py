from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.system_log import SystemLogCreate, SystemLogFilter, SystemLogStats


class SystemLogService:
    
    @staticmethod
    async def create_log(
        db: AsyncSession, 
        log_data: SystemLogCreate
    ) -> SystemLog:
        """创建系统日志"""
        log_entry = SystemLog(**log_data.dict())
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        
        return log_entry
    
    @staticmethod
    async def log_user_action(
        db: AsyncSession,
        user_id: Optional[int],
        action: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SystemLog:
        """记录用户操作日志"""
        log_data = SystemLogCreate(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return await SystemLogService.create_log(db, log_data)
    
    @staticmethod
    async def get_logs(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        log_filter: Optional[SystemLogFilter] = None
    ) -> tuple[List[SystemLog], int]:
        """获取系统日志列表"""
        query = select(SystemLog).order_by(SystemLog.created_at.desc())
        
        # 应用筛选条件
        if log_filter:
            conditions = []
            
            if log_filter.user_id:
                conditions.append(SystemLog.user_id == log_filter.user_id)
            
            if log_filter.action:
                conditions.append(SystemLog.action.ilike(f"%{log_filter.action}%"))
            
            if log_filter.start_date:
                conditions.append(SystemLog.created_at >= log_filter.start_date)
            
            if log_filter.end_date:
                conditions.append(SystemLog.created_at <= log_filter.end_date)
            
            if log_filter.ip_address:
                conditions.append(SystemLog.ip_address.ilike(f"%{log_filter.ip_address}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # 总数查询
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        logs = result.scalars().all()
        
        return list(logs), total
    
    @staticmethod
    async def get_logs_with_user(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        log_filter: Optional[SystemLogFilter] = None
    ) -> tuple[List[SystemLog], int]:
        """获取包含用户信息的系统日志列表"""
        from sqlalchemy.orm import selectinload
        
        query = select(SystemLog).options(
            selectinload(SystemLog.user)
        ).order_by(SystemLog.created_at.desc())
        
        # 应用筛选条件
        if log_filter:
            conditions = []
            
            if log_filter.user_id:
                conditions.append(SystemLog.user_id == log_filter.user_id)
            
            if log_filter.action:
                conditions.append(SystemLog.action.ilike(f"%{log_filter.action}%"))
            
            if log_filter.start_date:
                conditions.append(SystemLog.created_at >= log_filter.start_date)
            
            if log_filter.end_date:
                conditions.append(SystemLog.created_at <= log_filter.end_date)
            
            if log_filter.ip_address:
                conditions.append(SystemLog.ip_address.ilike(f"%{log_filter.ip_address}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # 总数查询
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        logs = result.scalars().all()
        
        return list(logs), total
    
    @staticmethod
    async def get_log_stats(db: AsyncSession) -> SystemLogStats:
        """获取日志统计信息"""
        # 总日志数
        total_result = await db.execute(select(func.count(SystemLog.id)))
        total_logs = total_result.scalar() or 0
        
        # 今日日志数
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_result = await db.execute(
            select(func.count(SystemLog.id)).where(
                and_(
                    SystemLog.created_at >= today_start,
                    SystemLog.created_at <= today_end
                )
            )
        )
        today_logs = today_result.scalar() or 0
        
        # 登录次数（今日）
        login_result = await db.execute(
            select(func.count(SystemLog.id)).where(
                and_(
                    SystemLog.action == 'login',
                    SystemLog.created_at >= today_start,
                    SystemLog.created_at <= today_end
                )
            )
        )
        login_count = login_result.scalar() or 0
        
        # 审计次数（今日）
        audit_result = await db.execute(
            select(func.count(SystemLog.id)).where(
                and_(
                    or_(
                        SystemLog.action == 'audit_start',
                        SystemLog.action == 'audit_complete'
                    ),
                    SystemLog.created_at >= today_start,
                    SystemLog.created_at <= today_end
                )
            )
        )
        audit_count = audit_result.scalar() or 0
        
        # 错误次数（今日）- 这里可以根据实际需要定义错误类型
        error_result = await db.execute(
            select(func.count(SystemLog.id)).where(
                and_(
                    SystemLog.action.ilike('%error%'),
                    SystemLog.created_at >= today_start,
                    SystemLog.created_at <= today_end
                )
            )
        )
        error_count = error_result.scalar() or 0
        
        return SystemLogStats(
            total_logs=total_logs,
            today_logs=today_logs,
            login_count=login_count,
            audit_count=audit_count,
            error_count=error_count
        )
    
    @staticmethod
    async def clean_old_logs(db: AsyncSession, days_to_keep: int = 90) -> int:
        """清理旧日志（保留指定天数）"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 查询要删除的日志数量
        count_result = await db.execute(
            select(func.count(SystemLog.id)).where(
                SystemLog.created_at < cutoff_date
            )
        )
        delete_count = count_result.scalar() or 0
        
        # 删除旧日志
        if delete_count > 0:
            await db.execute(
                SystemLog.__table__.delete().where(
                    SystemLog.created_at < cutoff_date
                )
            )
            await db.commit()
        
        return delete_count
