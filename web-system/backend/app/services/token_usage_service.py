from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.token_usage import TokenUsage
from app.models.user import User
from app.models.audit import AuditTask
from app.schemas.token_usage import TokenUsageCreate, TokenUsageStats, UserTokenStats


class TokenUsageService:
    
    @staticmethod
    async def record_token_usage(
        db: AsyncSession,
        user_id: int,
        tokens_consumed: int,
        provider: str,
        model_name: Optional[str] = None,
        task_id: Optional[int] = None,
        cost: Optional[Decimal] = None
    ) -> TokenUsage:
        """记录Token使用"""
        
        # 创建使用记录
        usage = TokenUsage(
            user_id=user_id,
            task_id=task_id,
            tokens_consumed=tokens_consumed,
            provider=provider,
            model_name=model_name,
            cost=cost or Decimal('0.0000')
        )
        
        db.add(usage)
        
        # 更新用户的今日Token使用量
        await db.execute(
            select(User).where(User.id == user_id)
        )
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if user:
            user.used_tokens_today += tokens_consumed
        
        await db.commit()
        await db.refresh(usage)
        
        return usage
    
    @staticmethod
    async def get_user_token_usage(
        db: AsyncSession,
        user_id: int,
        days: int = 30,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[TokenUsage], int]:
        """获取用户Token使用记录"""
        
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询
        query = select(TokenUsage).where(
            and_(
                TokenUsage.user_id == user_id,
                TokenUsage.created_at >= start_date,
                TokenUsage.created_at <= end_date
            )
        ).order_by(desc(TokenUsage.created_at))
        
        # 获取总数
        count_query = select(func.count()).select_from(
            select(TokenUsage).where(
                and_(
                    TokenUsage.user_id == user_id,
                    TokenUsage.created_at >= start_date,
                    TokenUsage.created_at <= end_date
                )
            ).subquery()
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        usages = result.scalars().all()
        
        return list(usages), total
    
    @staticmethod
    async def get_system_token_stats(
        db: AsyncSession,
        days: int = 30
    ) -> TokenUsageStats:
        """获取系统Token使用统计"""
        
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础统计
        stats_result = await db.execute(
            select(
                func.sum(TokenUsage.tokens_consumed).label('total_tokens'),
                func.sum(TokenUsage.cost).label('total_cost'),
                func.count(TokenUsage.id).label('total_requests'),
                func.avg(TokenUsage.tokens_consumed).label('avg_tokens')
            ).where(
                and_(
                    TokenUsage.created_at >= start_date,
                    TokenUsage.created_at <= end_date
                )
            )
        )
        stats = stats_result.first()
        
        # 最常用的提供商
        provider_result = await db.execute(
            select(
                TokenUsage.provider,
                func.count(TokenUsage.id).label('usage_count')
            ).where(
                and_(
                    TokenUsage.created_at >= start_date,
                    TokenUsage.created_at <= end_date
                )
            ).group_by(TokenUsage.provider)
            .order_by(desc(func.count(TokenUsage.id)))
            .limit(1)
        )
        most_used_provider = provider_result.scalar_one_or_none() or "未知"
        
        # 每日使用统计
        daily_result = await db.execute(
            select(
                func.date(TokenUsage.created_at).label('usage_date'),
                func.sum(TokenUsage.tokens_consumed).label('daily_tokens'),
                func.count(TokenUsage.id).label('daily_requests'),
                func.sum(TokenUsage.cost).label('daily_cost')
            ).where(
                and_(
                    TokenUsage.created_at >= start_date,
                    TokenUsage.created_at <= end_date
                )
            ).group_by(func.date(TokenUsage.created_at))
            .order_by(func.date(TokenUsage.created_at))
        )
        
        daily_breakdown = []
        for row in daily_result:
            daily_breakdown.append({
                'date': row.usage_date.isoformat() if row.usage_date else '',
                'tokens': int(row.daily_tokens or 0),
                'requests': int(row.daily_requests or 0),
                'cost': float(row.daily_cost or 0)
            })
        
        return TokenUsageStats(
            total_tokens=int(stats.total_tokens or 0),
            total_cost=Decimal(str(stats.total_cost or 0)),
            total_requests=int(stats.total_requests or 0),
            avg_tokens_per_request=float(stats.avg_tokens or 0),
            most_used_provider=most_used_provider,
            daily_breakdown=daily_breakdown
        )
    
    @staticmethod
    async def get_all_user_token_stats(
        db: AsyncSession,
        days: int = 30,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[UserTokenStats], int]:
        """获取所有用户Token使用统计"""
        
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 用户统计查询
        query = select(
            User.id.label('user_id'),
            User.username,
            func.coalesce(func.sum(TokenUsage.tokens_consumed), 0).label('total_tokens'),
            func.count(TokenUsage.id).label('total_requests'),
            func.coalesce(func.sum(TokenUsage.cost), 0).label('total_cost'),
            func.max(TokenUsage.created_at).label('last_usage')
        ).select_from(
            User.__table__.outerjoin(
                TokenUsage.__table__,
                and_(
                    User.id == TokenUsage.user_id,
                    TokenUsage.created_at >= start_date,
                    TokenUsage.created_at <= end_date
                )
            )
        ).group_by(User.id, User.username).order_by(
            desc(func.coalesce(func.sum(TokenUsage.tokens_consumed), 0))
        )
        
        # 获取总数
        count_result = await db.execute(select(func.count(User.id)))
        total = count_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        
        user_stats = []
        for row in result:
            # 获取最常用的提供商
            if row.total_requests > 0:
                provider_result = await db.execute(
                    select(TokenUsage.provider)
                    .where(
                        and_(
                            TokenUsage.user_id == row.user_id,
                            TokenUsage.created_at >= start_date,
                            TokenUsage.created_at <= end_date
                        )
                    )
                    .group_by(TokenUsage.provider)
                    .order_by(desc(func.count(TokenUsage.id)))
                    .limit(1)
                )
                most_used_provider = provider_result.scalar_one_or_none() or "未知"
            else:
                most_used_provider = "未使用"
            
            user_stats.append(UserTokenStats(
                user_id=row.user_id,
                username=row.username,
                total_tokens_consumed=int(row.total_tokens),
                total_requests=int(row.total_requests),
                total_cost=Decimal(str(row.total_cost)),
                last_usage=row.last_usage,
                most_used_provider=most_used_provider
            ))
        
        return user_stats, total
