"""OAuth token management service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from ..models.auth import OAuthAccount, User
from ..models.database import get_async_db

logger = logging.getLogger(__name__)

# Environment-based encryption key
import os
ENCRYPTION_KEY = os.getenv("OAUTH_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("⚠️ Using generated encryption key - set OAUTH_ENCRYPTION_KEY in production")

cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


class OAuthTokenService:
    """Service for managing OAuth tokens with encryption."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage."""
        if not token:
            return ""
        return cipher_suite.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token from storage."""
        if not encrypted_token:
            return ""
        return cipher_suite.decrypt(encrypted_token.encode()).decode()
    
    async def store_tokens(
        self, 
        user_id: int, 
        provider: str,
        provider_user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Store or update OAuth tokens for a user."""
        try:
            encrypted_access = self._encrypt_token(access_token)
            encrypted_refresh = self._encrypt_token(refresh_token) if refresh_token else None
            
            stmt = insert(OAuthAccount).values(
                user_id=user_id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                expires_at=expires_at
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id', 'provider'],
                set_=dict(
                    provider_user_id=stmt.excluded.provider_user_id,
                    access_token=stmt.excluded.access_token,
                    refresh_token=stmt.excluded.refresh_token,
                    expires_at=stmt.excluded.expires_at
                )
            )
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            logger.info(f"✅ Stored {provider} tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing {provider} tokens: {e}")
            await self.db.rollback()
            return False
    
    async def get_tokens(self, user_id: int, provider: str) -> Optional[Dict]:
        """Retrieve OAuth tokens for a user and provider."""
        try:
            stmt = select(OAuthAccount).where(
                OAuthAccount.user_id == user_id,
                OAuthAccount.provider == provider
            )
            
            result = await self.db.execute(stmt)
            oauth_account = result.scalar_one_or_none()
            
            if not oauth_account:
                return None
            
            access_token = self._decrypt_token(oauth_account.access_token or "")
            refresh_token = self._decrypt_token(oauth_account.refresh_token or "") if oauth_account.refresh_token else None
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": oauth_account.expires_at,
                "provider_user_id": oauth_account.provider_user_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error retrieving {provider} tokens for user {user_id}: {e}")
            return None
