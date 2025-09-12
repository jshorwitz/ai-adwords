"""Authentication and RBAC middleware."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..auth.service import AuthService
from ..models.auth import User, UserRole
from ..models.database import get_async_db

logger = logging.getLogger(__name__)

# Security scheme for Bearer tokens
security = HTTPBearer(auto_error=False)


async def get_auth_service(db=Depends(get_async_db)):
    """Get authentication service."""
    async with db as session:
        yield AuthService(session)


async def get_current_user_optional(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get current user from session cookie or Bearer token (optional)."""
    
    # Try session cookie first
    session_token = request.cookies.get("sid")
    if session_token:
        user = await auth_service.get_user_by_session_token(session_token)
        if user:
            return user
    
    # Try Bearer token
    if credentials:
        user = await auth_service.get_user_by_session_token(credentials.credentials)
        if user:
            return user
    
    return None


async def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Get current user (required)."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )
    
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Require specific user roles."""
    
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_roles}",
            )
        return current_user
    
    return role_checker


# Common role dependencies
require_admin = require_role([UserRole.ADMIN])
require_admin_or_analyst = require_role([UserRole.ADMIN, UserRole.ANALYST])
require_any_role = require_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])


def get_user_ip(request: Request) -> Optional[str]:
    """Extract user IP from request."""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    if request.client:
        return request.client.host
    
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")
