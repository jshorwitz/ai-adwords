"""Authentication service - user management, sessions, magic links."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auth import User, Session, MagicLink, OAuthAccount, UserRole
from .security import (
    hash_password,
    verify_password,
    generate_session_token,
    generate_magic_token,
    get_session_expire_time,
    get_magic_link_expire_time,
    is_session_expired,
    check_password_strength,
    is_email_valid,
    sanitize_user_agent,
    sanitize_ip,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        name: Optional[str] = None,
        role: UserRole = UserRole.VIEWER,
    ) -> Optional[User]:
        """Create a new user account."""
        
        if not is_email_valid(email):
            raise ValueError("Invalid email address")
        
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Validate password if provided
        password_hash = None
        if password:
            is_strong, message = check_password_strength(password)
            if not is_strong:
                raise ValueError(f"Password validation failed: {message}")
            password_hash = hash_password(password)
        
        # Create user
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            name=name,
            role=role,
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        logger.info(f"Created user: {email} with role {role}")
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        
        if not user or not user.is_active:
            return None
        
        if not user.password_hash:
            # User is passwordless-only
            return None
        
        if verify_password(password, user.password_hash):
            logger.info(f"User authenticated: {email}")
            return user
        
        logger.warning(f"Failed authentication attempt: {email}")
        return None

    async def create_session(
        self,
        user: User,
        user_agent: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> Session:
        """Create a new user session."""
        
        # Clean up expired sessions for this user
        await self.cleanup_expired_sessions(user.id)
        
        session = Session(
            user_id=user.id,
            session_token=generate_session_token(),
            expires_at=get_session_expire_time(),
            user_agent=sanitize_user_agent(user_agent),
            ip=sanitize_ip(ip),
        )
        
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        
        logger.info(f"Created session for user {user.email}")
        return session

    async def get_session_by_token(self, session_token: str) -> Optional[Session]:
        """Get session by token."""
        stmt = select(Session).where(Session.session_token == session_token)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session and is_session_expired(session.expires_at):
            # Session expired, clean it up
            await self.db.delete(session)
            return None
        
        return session

    async def get_user_by_session_token(self, session_token: str) -> Optional[User]:
        """Get user by session token."""
        session = await self.get_session_by_token(session_token)
        if not session:
            return None
        
        return await self.get_user_by_id(session.user_id)

    async def revoke_session(self, session_token: str) -> bool:
        """Revoke a session."""
        session = await self.get_session_by_token(session_token)
        if session:
            await self.db.delete(session)
            logger.info(f"Revoked session for user {session.user_id}")
            return True
        return False

    async def cleanup_expired_sessions(self, user_id: Optional[int] = None):
        """Clean up expired sessions."""
        stmt = delete(Session).where(Session.expires_at < datetime.utcnow())
        if user_id:
            stmt = stmt.where(Session.user_id == user_id)
        
        await self.db.execute(stmt)

    async def create_magic_link(self, email: str) -> tuple[Optional[User], Optional[MagicLink]]:
        """Create or get user and generate magic link."""
        
        if not is_email_valid(email):
            raise ValueError("Invalid email address")
        
        # Get or create user
        user = await self.get_user_by_email(email)
        if not user:
            # Create new user with viewer role
            user = await self.create_user(email=email, role=UserRole.VIEWER)
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Clean up old magic links for this user
        stmt = delete(MagicLink).where(MagicLink.user_id == user.id)
        await self.db.execute(stmt)
        
        # Create new magic link
        magic_link = MagicLink(
            user_id=user.id,
            token=generate_magic_token(),
            expires_at=get_magic_link_expire_time(),
        )
        
        self.db.add(magic_link)
        await self.db.flush()
        await self.db.refresh(magic_link)
        
        logger.info(f"Created magic link for user {email}")
        return user, magic_link

    async def verify_magic_link(self, token: str) -> Optional[User]:
        """Verify and consume magic link."""
        stmt = select(MagicLink).where(
            MagicLink.token == token,
            MagicLink.used_at.is_(None),
            MagicLink.expires_at > datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        magic_link = result.scalar_one_or_none()
        
        if not magic_link:
            return None
        
        # Mark as used
        magic_link.used_at = datetime.utcnow()
        
        # Get user
        user = await self.get_user_by_id(magic_link.user_id)
        if user and user.is_active:
            logger.info(f"Magic link verified for user {user.email}")
            return user
        
        return None

    async def link_oauth_account(
        self,
        user: User,
        provider: str,
        provider_user_id: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> OAuthAccount:
        """Link OAuth account to user."""
        
        # Check if OAuth account already exists
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id
        )
        result = await self.db.execute(stmt)
        oauth_account = result.scalar_one_or_none()
        
        if oauth_account:
            # Update existing
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            oauth_account.expires_at = expires_at
        else:
            # Create new
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            self.db.add(oauth_account)
        
        await self.db.flush()
        await self.db.refresh(oauth_account)
        
        logger.info(f"Linked {provider} account for user {user.email}")
        return oauth_account

    async def get_oauth_account(self, provider: str, provider_user_id: str) -> Optional[OAuthAccount]:
        """Get OAuth account by provider and provider user ID."""
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        """Update user role (admin only)."""
        user = await self.get_user_by_id(user_id)
        if user:
            old_role = user.role
            user.role = new_role
            user.updated_at = datetime.utcnow()
            await self.db.flush()
            logger.info(f"Updated user {user.email} role from {old_role} to {new_role}")
            return user
        return None

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        user = await self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            # Revoke all sessions
            stmt = delete(Session).where(Session.user_id == user_id)
            await self.db.execute(stmt)
            
            logger.info(f"Deactivated user {user.email}")
            return True
        return False
