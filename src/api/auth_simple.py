"""Simplified authentication routes that work without database."""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Simple in-memory user storage for demo (replace with database in production)
DEMO_USERS = {}
DEMO_SESSIONS = {}

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
    role: str = "viewer"
    created_at: str


class MessageResponse(BaseModel):
    message: str


def hash_password_simple(password: str) -> str:
    """Simple password hashing for demo."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password_simple(password: str, hashed: str) -> bool:
    """Simple password verification for demo."""
    return hash_password_simple(password) == hashed


def generate_session_token() -> str:
    """Generate simple session token."""
    import secrets
    return secrets.token_urlsafe(32)


@router.post("/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """Create a new user account (simplified for demo)."""
    try:
        email = request.email.lower()
        
        # Check if user exists
        if email in DEMO_USERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Validate password
        if request.password and len(request.password) < 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 12 characters long"
            )
        
        # Create user
        user_id = len(DEMO_USERS) + 1
        user_data = {
            "id": user_id,
            "email": email,
            "name": request.name or "User",
            "password_hash": hash_password_simple(request.password) if request.password else None,
            "role": "admin" if user_id == 1 else "viewer",  # First user is admin
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        DEMO_USERS[email] = user_data
        
        logger.info(f"Demo user created: {email}")
        
        return UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            created_at=user_data["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Signup failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login", response_model=MessageResponse)
async def login(request: LoginRequest, response: Response):
    """Login with email and password (simplified for demo)."""
    
    try:
        email = request.email.lower()
        
        # Check if user exists
        if email not in DEMO_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = DEMO_USERS[email]
        
        # Check password
        if not user["password_hash"] or not verify_password_simple(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create session
        session_token = generate_session_token()
        DEMO_SESSIONS[session_token] = {
            "user_id": user["id"],
            "email": email,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Set session cookie
        response.set_cookie(
            key="sid",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400,  # 24 hours
        )
        
        logger.info(f"Demo user logged in: {email}")
        return MessageResponse(message="Login successful")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response, request: Request):
    """Logout and revoke session (simplified for demo)."""
    
    try:
        # Get session token from cookie
        session_token = request.cookies.get("sid")
        
        if session_token and session_token in DEMO_SESSIONS:
            del DEMO_SESSIONS[session_token]
            logger.info("Demo user logged out")
        
        # Clear cookie
        response.delete_cookie(key="sid")
        
        return MessageResponse(message="Logout successful")
        
    except Exception as e:
        logger.exception("Logout failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/magic-link", response_model=MessageResponse)
async def send_magic_link(request: MagicLinkRequest):
    """Send magic link for passwordless authentication (simplified for demo)."""
    
    try:
        email = request.email.lower()
        
        # Create user if doesn't exist (for magic link)
        if email not in DEMO_USERS:
            user_id = len(DEMO_USERS) + 1
            DEMO_USERS[email] = {
                "id": user_id,
                "email": email,
                "name": "Magic Link User",
                "password_hash": None,  # Passwordless
                "role": "viewer",
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
            logger.info(f"Created passwordless user: {email}")
        
        # Generate magic token (in production, send via email)
        magic_token = generate_session_token()
        
        # Store magic link session (expires in 10 minutes)
        DEMO_SESSIONS[f"magic_{magic_token}"] = {
            "user_id": DEMO_USERS[email]["id"],
            "email": email,
            "type": "magic_link",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        # In demo mode, log the magic link
        magic_url = f"https://web-production-fab37a.up.railway.app/auth/magic?token={magic_token}"
        logger.info(f"Magic link for {email}: {magic_url}")
        
        return MessageResponse(
            message=f"Magic link sent! For demo: /auth/magic?token={magic_token[:16]}..."
        )
        
    except Exception as e:
        logger.exception("Magic link failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Magic link failed: {str(e)}"
        )


@router.get("/magic", response_model=MessageResponse)
async def verify_magic_link(token: str, response: Response):
    """Verify and consume magic link (simplified for demo)."""
    
    try:
        magic_key = f"magic_{token}"
        
        if magic_key not in DEMO_SESSIONS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired magic link"
            )
        
        magic_session = DEMO_SESSIONS[magic_key]
        
        # Check expiration
        if datetime.utcnow() > magic_session["expires_at"]:
            del DEMO_SESSIONS[magic_key]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Magic link has expired"
            )
        
        # Create regular session
        session_token = generate_session_token()
        DEMO_SESSIONS[session_token] = {
            "user_id": magic_session["user_id"],
            "email": magic_session["email"],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Remove magic link session (single use)
        del DEMO_SESSIONS[magic_key]
        
        # Set session cookie
        response.set_cookie(
            key="sid",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production
            samesite="lax",
            max_age=86400,
        )
        
        logger.info(f"Magic link verified for: {magic_session['email']}")
        return MessageResponse(message="Authentication successful")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Magic link verification failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Magic link verification failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request):
    """Get current user information (simplified for demo)."""
    
    try:
        session_token = request.cookies.get("sid")
        
        if not session_token or session_token not in DEMO_SESSIONS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        session = DEMO_SESSIONS[session_token]
        
        # Check expiration
        if datetime.utcnow() > session["expires_at"]:
            del DEMO_SESSIONS[session_token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
        user = DEMO_USERS[session["email"]]
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            created_at=user["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get user info failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get user info failed: {str(e)}"
        )


@router.get("/status")
async def auth_status():
    """Get auth system status for debugging."""
    return {
        "status": "active",
        "demo_users": len(DEMO_USERS),
        "active_sessions": len(DEMO_SESSIONS),
        "users": [{"email": email, "role": user["role"]} for email, user in DEMO_USERS.items()]
    }
