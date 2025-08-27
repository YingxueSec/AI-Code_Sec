# 数据库实现方案

## MySQL数据库配置

### 连接配置
- **主机**: localhost
- **端口**: 3306
- **用户名**: root
- **密码**: jackhou.
- **数据库**: ai_code_audit
- **字符集**: utf8mb4

## 数据库表结构设计

### 1. 项目表 (projects)
```sql
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    project_type ENUM('web_application', 'api_service', 'desktop_application', 'library', 'microservice', 'unknown') DEFAULT 'unknown',
    languages JSON,
    architecture_pattern VARCHAR(100),
    total_files INT DEFAULT 0,
    total_lines INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_scanned_at TIMESTAMP NULL,
    INDEX idx_name (name),
    INDEX idx_created_at (created_at)
);
```

### 2. 文件表 (files)
```sql
CREATE TABLE files (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    path TEXT NOT NULL,
    absolute_path TEXT NOT NULL,
    language VARCHAR(50),
    size BIGINT DEFAULT 0,
    hash VARCHAR(64),
    last_modified TIMESTAMP,
    functions JSON,
    classes JSON,
    imports JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_language (language),
    INDEX idx_hash (hash)
);
```

### 3. 模块表 (modules)
```sql
CREATE TABLE modules (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    business_logic TEXT,
    risk_level ENUM('critical', 'high', 'medium', 'low') DEFAULT 'medium',
    files JSON,
    entry_points JSON,
    dependencies JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_risk_level (risk_level)
);
```

### 4. 审计会话表 (audit_sessions)
```sql
CREATE TABLE audit_sessions (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    module_id VARCHAR(36),
    model_used VARCHAR(50) NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration INT DEFAULT 0,
    total_findings INT DEFAULT 0,
    critical_findings INT DEFAULT 0,
    high_findings INT DEFAULT 0,
    medium_findings INT DEFAULT 0,
    low_findings INT DEFAULT 0,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
);
```

### 5. 安全发现表 (security_findings)
```sql
CREATE TABLE security_findings (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    module_id VARCHAR(36),
    file_path TEXT NOT NULL,
    line_number INT,
    vulnerability_type ENUM('sql_injection', 'xss', 'csrf', 'authentication_bypass', 'authorization_failure', 'data_validation', 'sensitive_data_exposure', 'insecure_crypto', 'code_injection', 'path_traversal') NOT NULL,
    severity ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    code_snippet TEXT,
    recommendation TEXT,
    confidence DECIMAL(3,2) DEFAULT 0.00,
    cwe_id VARCHAR(20),
    owasp_category VARCHAR(100),
    status ENUM('open', 'fixed', 'false_positive', 'accepted_risk') DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES audit_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE SET NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_project_id (project_id),
    INDEX idx_severity (severity),
    INDEX idx_vulnerability_type (vulnerability_type),
    INDEX idx_status (status)
);
```

### 6. 审计报告表 (audit_reports)
```sql
CREATE TABLE audit_reports (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    report_type ENUM('module', 'project', 'comprehensive') DEFAULT 'module',
    format ENUM('json', 'html', 'pdf', 'markdown') DEFAULT 'json',
    title VARCHAR(500),
    summary TEXT,
    content LONGTEXT,
    file_path TEXT,
    file_size BIGINT DEFAULT 0,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES audit_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_project_id (project_id),
    INDEX idx_report_type (report_type)
);
```

### 7. 缓存表 (cache_entries)
```sql
CREATE TABLE cache_entries (
    id VARCHAR(36) PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_type ENUM('project_analysis', 'code_snippet', 'llm_response', 'file_hash') NOT NULL,
    content LONGTEXT,
    metadata JSON,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cache_key (cache_key),
    INDEX idx_cache_type (cache_type),
    INDEX idx_expires_at (expires_at)
);
```

## SQLAlchemy模型实现

### database/models.py
```python
from sqlalchemy import Column, String, Text, Integer, BigInteger, Timestamp, Enum, JSON, Decimal, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class ProjectType(PyEnum):
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    DESKTOP_APPLICATION = "desktop_application"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    UNKNOWN = "unknown"

class SeverityLevel(PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class VulnerabilityType(PyEnum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATA_VALIDATION = "data_validation"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSECURE_CRYPTO = "insecure_crypto"
    CODE_INJECTION = "code_injection"
    PATH_TRAVERSAL = "path_traversal"

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False)
    project_type = Column(Enum(ProjectType), default=ProjectType.UNKNOWN)
    languages = Column(JSON)
    architecture_pattern = Column(String(100))
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    created_at = Column(Timestamp, default=func.now())
    updated_at = Column(Timestamp, default=func.now(), onupdate=func.now())
    last_scanned_at = Column(Timestamp)
    
    # 关系
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="project", cascade="all, delete-orphan")
    audit_sessions = relationship("AuditSession", back_populates="project", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = 'files'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False)
    path = Column(Text, nullable=False)
    absolute_path = Column(Text, nullable=False)
    language = Column(String(50))
    size = Column(BigInteger, default=0)
    hash = Column(String(64))
    last_modified = Column(Timestamp)
    functions = Column(JSON)
    classes = Column(JSON)
    imports = Column(JSON)
    created_at = Column(Timestamp, default=func.now())
    updated_at = Column(Timestamp, default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="files")

class Module(Base):
    __tablename__ = 'modules'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    business_logic = Column(Text)
    risk_level = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    files = Column(JSON)
    entry_points = Column(JSON)
    dependencies = Column(JSON)
    created_at = Column(Timestamp, default=func.now())
    updated_at = Column(Timestamp, default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="modules")
    audit_sessions = relationship("AuditSession", back_populates="module")
    security_findings = relationship("SecurityFinding", back_populates="module")

class AuditSession(Base):
    __tablename__ = 'audit_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False)
    module_id = Column(String(36), ForeignKey('modules.id'))
    model_used = Column(String(50), nullable=False)
    status = Column(Enum('pending', 'running', 'completed', 'failed', 'cancelled'), default='pending')
    start_time = Column(Timestamp, default=func.now())
    end_time = Column(Timestamp)
    duration = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    config = Column(JSON)
    created_at = Column(Timestamp, default=func.now())
    updated_at = Column(Timestamp, default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="audit_sessions")
    module = relationship("Module", back_populates="audit_sessions")
    security_findings = relationship("SecurityFinding", back_populates="session", cascade="all, delete-orphan")
    audit_reports = relationship("AuditReport", back_populates="session", cascade="all, delete-orphan")

class SecurityFinding(Base):
    __tablename__ = 'security_findings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('audit_sessions.id'), nullable=False)
    project_id = Column(String(36), ForeignKey('projects.id'), nullable=False)
    module_id = Column(String(36), ForeignKey('modules.id'))
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer)
    vulnerability_type = Column(Enum(VulnerabilityType), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    code_snippet = Column(Text)
    recommendation = Column(Text)
    confidence = Column(Decimal(3,2), default=0.00)
    cwe_id = Column(String(20))
    owasp_category = Column(String(100))
    status = Column(Enum('open', 'fixed', 'false_positive', 'accepted_risk'), default='open')
    created_at = Column(Timestamp, default=func.now())
    updated_at = Column(Timestamp, default=func.now(), onupdate=func.now())
    
    # 关系
    session = relationship("AuditSession", back_populates="security_findings")
    project = relationship("Project")
    module = relationship("Module", back_populates="security_findings")
```

## 数据库连接管理

### database/connection.py
```python
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """初始化数据库连接"""
        database_url = (
            f"mysql+aiomysql://{self.config.username}:{self.config.password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
            f"?charset={self.config.charset}"
        )
        
        self.engine = create_async_engine(
            database_url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            echo=False
        )
        
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("数据库连接初始化完成")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")

# 全局数据库管理器实例
db_manager = DatabaseManager(None)

async def init_database(config):
    """初始化数据库"""
    global db_manager
    db_manager.config = config.database
    await db_manager.initialize()

async def get_db_session():
    """获取数据库会话的便捷函数"""
    return db_manager.get_session()
```

这个数据库实现方案提供了完整的MySQL数据库支持，包括表结构设计、SQLAlchemy模型定义和连接管理。所有配置都已更新为使用硅基流动的API和本地MySQL数据库。
