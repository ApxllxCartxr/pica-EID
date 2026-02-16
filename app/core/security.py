"""
Security module: JWT tokens, password hashing, token verification, and token revocation.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings


# Password hashing context (bcrypt, 12 rounds)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with a unique JTI for revocation support."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None.
    Also checks the token against the Redis blacklist.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        # Check if this token has been revoked
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            return None
        return payload
    except JWTError:
        return None


def revoke_token(jti: str, ttl_seconds: int = 86400) -> bool:
    """Add a token's JTI to the Redis blacklist."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.setex(f"prismid:token_blacklist:{jti}", ttl_seconds, "revoked")
        return True
    except Exception:
        return False


def is_token_revoked(jti: str) -> bool:
    """Check if a token JTI is in the Redis blacklist."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        return r.exists(f"prismid:token_blacklist:{jti}") > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# API Key utilities
# ---------------------------------------------------------------------------

import secrets
import hashlib


def generate_api_key() -> str:
    """Generate a secure random API key with a recognisable prefix."""
    random_part = secrets.token_hex(32)  # 64 hex chars
    return f"prismid_{random_part}"


def hash_api_key(key: str) -> str:
    """Create a SHA-256 hash of an API key (one-way, for storage)."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_api_key_prefix(key: str) -> str:
    """Return the first 12 characters of a key for display / lookup."""
    return key[:12]

