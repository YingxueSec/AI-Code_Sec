#!/usr/bin/env python3
"""
创建管理员用户脚本
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, update
from app.models.user import User, UserRole, UserLevel
from app.core.security import get_password_hash
from app.core.config import settings

async def create_admin_user():
    """创建或更新管理员用户"""
    # 创建数据库连接
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with SessionLocal() as db:
        try:
            # 检查是否已存在用户
            result = await db.execute(select(User).where(User.username == "admin"))
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                # 更新现有用户为管理员
                admin_user.role = UserRole.admin
                admin_user.user_level = UserLevel.premium
                admin_user.daily_token_limit = 10000
                admin_user.is_active = True
                print(f"已将用户 {admin_user.username} 更新为管理员")
            else:
                # 创建新的管理员用户
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=get_password_hash("admin123"),
                    role=UserRole.admin,
                    user_level=UserLevel.premium,
                    daily_token_limit=10000,
                    is_active=True
                )
                db.add(admin_user)
                print("已创建新的管理员用户")
            
            # 同时检查并升级现有的newuser为管理员（用于测试）
            result = await db.execute(select(User).where(User.username == "newuser"))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                existing_user.role = UserRole.admin
                existing_user.user_level = UserLevel.premium
                existing_user.daily_token_limit = 10000
                print(f"已将用户 {existing_user.username} 升级为管理员")
            
            await db.commit()
            
            # 显示所有用户
            result = await db.execute(select(User))
            users = result.scalars().all()
            print("\n当前用户列表:")
            for user in users:
                print(f"  ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {user.role}")
                
        except Exception as e:
            await db.rollback()
            print(f"创建管理员用户失败: {e}")
            return False
        finally:
            await engine.dispose()
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(create_admin_user())
        if success:
            print("\n✅ 管理员用户创建/更新成功！")
            print("管理员账户信息:")
            print("  用户名: admin")
            print("  密码: admin123")
            print("  邮箱: admin@example.com")
            print("\n测试管理员账户信息:")
            print("  用户名: newuser") 
            print("  密码: password123")
        else:
            print("❌ 操作失败")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        sys.exit(1)
