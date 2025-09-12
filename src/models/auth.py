"""Authentication models - users, sessions, OAuth accounts."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst" 
    VIEWER = "viewer"


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # null for passwordless
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.VIEWER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    magic_links: Mapped[list["MagicLink"]] = relationship("MagicLink", back_populates="user", cascade="all, delete-orphan")
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """User session model."""
    
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # random token
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")


class MagicLink(Base):
    """Magic link for passwordless authentication."""
    
    __tablename__ = "magic_links"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # single-use token
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="magic_links")


class OAuthAccount(Base):
    """OAuth account linking (Google, etc.)."""
    
    __tablename__ = "oauth_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # 'google', etc.
    provider_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")
    
    __table_args__ = (
        # Unique constraint on provider + provider_user_id
        {"schema": None},
    )
