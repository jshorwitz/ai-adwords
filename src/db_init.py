"""Database initialization script."""

import asyncio
import logging
import os
from datetime import datetime

from models.database import create_tables, get_async_db
from models.auth import User, UserRole
from auth.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with tables and seed data."""
    
    logger.info("🔄 Initializing database...")
    
    # Create tables
    await create_tables()
    logger.info("✅ Database tables created")
    
    # Add seed data
    async with get_async_db() as db:
        # Check if admin user exists
        admin_email = "admin@example.com"
        
        # Simple query to check if user exists
        from sqlalchemy import select
        stmt = select(User).where(User.email == admin_email)
        result = await db.execute(stmt)
        existing_admin = result.scalar_one_or_none()
        
        if not existing_admin:
            # Create admin user
            admin_password = "admin123456789"  # Change in production
            admin_user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                name="Admin User",
                role=UserRole.ADMIN,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            db.add(admin_user)
            await db.flush()
            
            logger.info(f"✅ Created admin user: {admin_email}")
            logger.info(f"📝 Admin password: {admin_password}")
        else:
            logger.info(f"ℹ️  Admin user already exists: {admin_email}")
        
        # Create sample viewer user
        viewer_email = "viewer@example.com"
        stmt = select(User).where(User.email == viewer_email)
        result = await db.execute(stmt)
        existing_viewer = result.scalar_one_or_none()
        
        if not existing_viewer:
            viewer_user = User(
                email=viewer_email,
                name="Viewer User",
                role=UserRole.VIEWER,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            db.add(viewer_user)
            await db.flush()
            
            logger.info(f"✅ Created viewer user: {viewer_email} (passwordless)")
        else:
            logger.info(f"ℹ️  Viewer user already exists: {viewer_email}")
        
        await db.commit()
    
    logger.info("🎉 Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_database())
