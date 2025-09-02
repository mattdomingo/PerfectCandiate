"""
Database configuration and setup
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from typing import AsyncGenerator

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/perfectcandidate"
)

# Convert sync URL to async if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
