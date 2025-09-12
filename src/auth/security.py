"""Security utilities - password hashing, token generation, session management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from passlib.context import CryptContext

# Password hashing with Argon2 (preferred) and bcrypt fallback
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"], 
    deprecated="auto"
)

# Argon2 hasher for new passwords
argon2_hasher = PasswordHasher()

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    try:
        # Try Argon2 first
        argon2_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        # Fallback to passlib context (handles bcrypt, etc.)
        return pwd_context.verify(plain_password, hashed_password)


def generate_session_token() -> str:
    """Generate secure random session token."""
    return secrets.token_urlsafe(48)


def generate_magic_token() -> str:
    """Generate secure random magic link token."""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def check_password_strength(password: str) -> tuple[bool, str]:
    """Check if password meets security requirements."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    # Check for common patterns
    if password.lower() in ["password123", "123456789", "qwerty123"]:
        return False, "Password is too common"
    
    # Basic strength checks
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
    
    strength_score = sum([has_upper, has_lower, has_digit, has_special])
    
    if strength_score < 3:
        return False, "Password should contain uppercase, lowercase, numbers, and special characters"
    
    return True, "Password strength is adequate"


def is_email_valid(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def get_session_expire_time() -> datetime:
    """Get session expiration time (24 hours from now)."""
    return datetime.utcnow() + timedelta(hours=24)


def get_magic_link_expire_time() -> datetime:
    """Get magic link expiration time (10 minutes from now)."""
    return datetime.utcnow() + timedelta(minutes=10)


def is_session_expired(expires_at: datetime) -> bool:
    """Check if session is expired."""
    return datetime.utcnow() > expires_at


def sanitize_user_agent(user_agent: Optional[str]) -> Optional[str]:
    """Sanitize user agent string for storage."""
    if not user_agent:
        return None
    
    # Truncate to reasonable length
    return user_agent[:255] if len(user_agent) > 255 else user_agent


def sanitize_ip(ip: Optional[str]) -> Optional[str]:
    """Sanitize IP address for storage."""
    if not ip:
        return None
    
    # Basic IPv4/IPv6 validation and truncation
    return ip[:64] if len(ip) > 64 else ip
