from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.api import auth, audit, admin, invitation, system_logs, analytics, token_usage, export_permission
from app.db.base import init_db
import logging

# 配置日志
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI代码安全审计系统 - 后端API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加可信主机中间件（生产环境建议启用）
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"]
    )

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(invitation.router, prefix="/api/v1")
app.include_router(system_logs.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(token_usage.router, prefix="/api/v1")
app.include_router(export_permission.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Starting AI Code Audit System API...")
    
    # 初始化数据库
    await init_db()
    logger.info("Database initialized")
    
    # 初始化队列服务
    try:
        from app.services.task_queue_service import task_queue_service
        redis = await task_queue_service.get_redis()
        await redis.ping()
        logger.info("Task queue service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize task queue service: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down AI Code Audit System API...")
    
    # 关闭队列服务
    try:
        from app.services.task_queue_service import task_queue_service
        await task_queue_service.close()
        logger.info("Task queue service closed")
    except Exception as e:
        logger.error(f"Failed to close task queue service: {e}")


@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "message": "AI代码安全审计系统 API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": "ai-code-audit-api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        access_log=True
    )
