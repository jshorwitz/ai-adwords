"""Database connection and session management."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://ads_user:ads_pass@localhost:5432/ai_adwords"
)

# Convert sync URL to async if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("mysql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+aiomysql://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Async engine and session
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine for migrations and non-async operations
sync_engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Get sync database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
