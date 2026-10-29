from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
from .settings import get_settings
from ..models.base import Base
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.async_session = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory."""
        try:
            self.engine = create_async_engine(
                self.settings.DATABASE_URL,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Enable foreign keys in SQLite (not needed for PostgreSQL)
            if self.engine.dialect.name == "sqlite":
                @event.listens_for(self.engine.sync_engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            
            self.async_session = sessionmaker(
                self.engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            
            logger.info(f"Database connected: {self.settings.DATABASE_URL}")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def create_tables(self):
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    def get_session(self):
        """Get a new async database session."""
        return self.async_session()

# Global database instance
database = DatabaseConfig()
