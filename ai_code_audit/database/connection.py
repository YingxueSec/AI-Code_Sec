"""
Database connection management for AI Code Audit System.

This module handles async database connections, session management,
and connection pooling using SQLAlchemy with aiomysql.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any

import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from ai_code_audit.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration container."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        username: str = "root", 
        password: str = "jackhou.",
        database: str = "ai_code_audit_system",
        charset: str = "utf8mb4",
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.charset = charset
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
    
    @property
    def database_url(self) -> str:
        """Generate SQLAlchemy database URL."""
        return (
            f"mysql+aiomysql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset={self.charset}"
        )
    
    @property
    def connection_params(self) -> Dict[str, Any]:
        """Get aiomysql connection parameters."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "db": self.database,
            "charset": self.charset,
        }


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._initialized:
            logger.warning("Database already initialized")
            return
        
        try:
            # Test basic connectivity first
            await self._test_connection()
            
            # Create async engine
            self.engine = create_async_engine(
                self.config.database_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
                poolclass=NullPool if self.config.pool_size == 0 else None,
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            # Test engine connectivity
            await self._test_engine()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def _test_connection(self) -> None:
        """Test basic MySQL connectivity."""
        try:
            conn = await aiomysql.connect(**self.config.connection_params)
            await conn.ping()
            conn.close()
            logger.debug("Basic MySQL connection test passed")
        except Exception as e:
            raise DatabaseError(f"Cannot connect to MySQL: {e}")
    
    async def _test_engine(self) -> None:
        """Test SQLAlchemy engine connectivity."""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                row = result.fetchone()  # Remove await here
            logger.debug("SQLAlchemy engine test passed")
        except Exception as e:
            raise DatabaseError(f"SQLAlchemy engine test failed: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup."""
        if not self._initialized:
            raise DatabaseError("Database not initialized. Call initialize() first.")
        
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            await session.close()
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        try:
            from ai_code_audit.database.models import Base
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        try:
            from ai_code_audit.database.models import Base
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("Database tables dropped successfully")
            
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise DatabaseError(f"Table drop failed: {e}")
    
    async def check_tables_exist(self) -> bool:
        """Check if database tables exist."""
        if not self._initialized:
            return False

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = :schema AND table_name = 'projects'"
                ), {"schema": self.config.database})
                count = result.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.debug(f"Table check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
        
        self._initialized = False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def init_database(config: Optional[DatabaseConfig] = None) -> DatabaseManager:
    """Initialize the global database manager."""
    global _db_manager
    
    if _db_manager is not None:
        logger.warning("Database manager already initialized")
        return _db_manager
    
    _db_manager = DatabaseManager(config)
    await _db_manager.initialize()
    
    return _db_manager


def get_db_session():
    """Get a database session from the global manager."""
    if _db_manager is None:
        raise DatabaseError("Database not initialized. Call init_database() first.")

    return _db_manager.get_session()


async def close_database() -> None:
    """Close the global database manager."""
    global _db_manager
    
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None


async def ensure_database_exists(config: DatabaseConfig) -> None:
    """Ensure the target database exists, create if not."""
    try:
        # Connect without specifying database
        temp_config = DatabaseConfig(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            database="mysql",  # Connect to default mysql database
            charset=config.charset,
        )
        
        conn = await aiomysql.connect(**temp_config.connection_params)
        cursor = await conn.cursor()
        
        # Create database if it doesn't exist
        await cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {config.database} "
            f"CHARACTER SET {config.charset} COLLATE {config.charset}_unicode_ci"
        )
        
        await cursor.close()
        conn.close()
        
        logger.info(f"Database {config.database} ensured to exist")
        
    except Exception as e:
        raise DatabaseError(f"Failed to ensure database exists: {e}")
