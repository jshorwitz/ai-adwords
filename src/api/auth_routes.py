"""Authentication API routes - signup, login, logout, magic links."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from ..auth.service import AuthService
from ..models.auth import User, UserRole
from .middleware import (
    get_auth_service,
    get_current_user,
    get_current_user_optional,
    get_user_agent,
    get_user_ip,
    require_admin,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: str

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )


class MessageResponse(BaseModel):
    message: str


@router.post("/signup", response_model=UserResponse)
async def signup(
    request: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new user account."""
    try:
        user = await auth_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        logger.info(f"User signed up: {request.email}")
        return UserResponse.from_user(user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=MessageResponse)
async def login(
    request: LoginRequest,
    response: Response,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with email and password."""
    
    user = await auth_service.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create session
    session = await auth_service.create_session(
        user=user,
        user_agent=get_user_agent(http_request),
        ip=get_user_ip(http_request),
    )
    
    # Set session cookie
    response.set_cookie(
        key="sid",
        value=session.session_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=86400,  # 24 hours
    )
    
    logger.info(f"User logged in: {user.email}")
    return MessageResponse(message="Login successful")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    http_request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout and revoke session."""
    
    # Get session token from cookie
    session_token = http_request.cookies.get("sid")
    
    if session_token:
        await auth_service.revoke_session(session_token)
    
    # Clear cookie
    response.delete_cookie(key="sid")
    
    if current_user:
        logger.info(f"User logged out: {current_user.email}")
    
    return MessageResponse(message="Logout successful")


@router.post("/magic-link", response_model=MessageResponse)
async def send_magic_link(
    request: MagicLinkRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Send magic link for passwordless authentication."""
    try:
        user, magic_link = await auth_service.create_magic_link(request.email)
        
        if not user or not magic_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create magic link"
            )
        
        # TODO: Send email with magic link
        # For now, just log the token (in production, this would be sent via email)
        magic_url = f"https://app.example.com/auth/magic?token={magic_link.token}"
        logger.info(f"Magic link created for {request.email}: {magic_url}")
        
        return MessageResponse(message="Magic link sent to your email")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/magic", response_model=MessageResponse)
async def verify_magic_link(
    token: str,
    response: Response,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verify and consume magic link."""
    
    user = await auth_service.verify_magic_link(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )
    
    # Create session
    session = await auth_service.create_session(
        user=user,
        user_agent=get_user_agent(http_request),
        ip=get_user_ip(http_request),
    )
    
    # Set session cookie
    response.set_cookie(
        key="sid",
        value=session.session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    
    logger.info(f"User authenticated via magic link: {user.email}")
    return MessageResponse(message="Authentication successful")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserResponse.from_user(current_user)


@router.post("/rotate", response_model=MessageResponse)
async def rotate_session(
    response: Response,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Rotate session token to extend session."""
    
    # Revoke current session
    current_session_token = http_request.cookies.get("sid")
    if current_session_token:
        await auth_service.revoke_session(current_session_token)
    
    # Create new session
    new_session = await auth_service.create_session(
        user=current_user,
        user_agent=get_user_agent(http_request),
        ip=get_user_ip(http_request),
    )
    
    # Set new session cookie
    response.set_cookie(
        key="sid",
        value=new_session.session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    
    logger.info(f"Session rotated for user: {current_user.email}")
    return MessageResponse(message="Session rotated successfully")


# Admin-only routes
@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Update user role (admin only)."""
    
    updated_user = await auth_service.update_user_role(user_id, new_role)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Admin {current_user.email} updated user {updated_user.email} role to {new_role}")
    return UserResponse.from_user(updated_user)


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Deactivate user account (admin only)."""
    
    success = await auth_service.deactivate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Admin {current_user.email} deactivated user {user_id}")
    return MessageResponse(message="User deactivated successfully")
