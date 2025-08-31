from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "AI代码审计系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "mysql+aiomysql://root:jackhou.@localhost:3306/ai_code_audit_web"
    
    # JWT配置
    SECRET_KEY: str = "ai-code-audit-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 104857600  # 100MB
    UPLOAD_PATH: str = "./uploads"
    REPORTS_PATH: str = "./reports"
    
    # LLM配置
    QWEN_API_KEY: Optional[str] = None
    QWEN_BASE_URL: str = "https://api.siliconflow.cn/v1"
    KIMI_API_KEY: Optional[str] = None
    KIMI_BASE_URL: str = "https://api.siliconflow.cn/v1"
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs(settings.REPORTS_PATH, exist_ok=True)
