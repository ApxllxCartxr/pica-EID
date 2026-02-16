"""
FastAPI dependency injection — authentication (JWT + API Key) and database session.
"""

from datetime import datetime
from typing import Optional, Union

from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_token, hash_api_key
from app.models.admin import AdminAccount, AccessLevel
from app.models.api_key import ApiKey
from app.core.permissions import check_access_level


security_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_admin_from_jwt(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
) -> AdminAccount:
    """Validate JWT and return the owning AdminAccount."""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin_id = payload.get("sub")
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    admin = db.query(AdminAccount).filter(
        AdminAccount.id == int(admin_id),
        AdminAccount.is_active == True,
    ).first()

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account not found or inactive",
        )

    return admin


def _resolve_api_key(
    raw_key: str,
    db: Session,
) -> ApiKey:
    """Validate an API key string and return the ApiKey row."""
    hashed = hash_api_key(raw_key)
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == hashed,
        ApiKey.is_active == True,
    ).first()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Check expiry
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Touch last_used_at (fire-and-forget, don't fail the request)
    try:
        api_key.last_used_at = datetime.utcnow()
        db.commit()
    except Exception:
        db.rollback()

    return api_key


# ---------------------------------------------------------------------------
# Public dependencies
# ---------------------------------------------------------------------------

def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> AdminAccount:
    """
    Resolve the caller's identity.
    Accepts EITHER:
      • Bearer JWT  (existing admin login flow)
      • X-API-Key header  (external application flow — resolves to the key's owner)
    """
    # 1. Try JWT first
    if credentials is not None:
        return _resolve_admin_from_jwt(credentials, db)

    # 2. Fall back to API key
    if x_api_key is not None:
        api_key = _resolve_api_key(x_api_key, db)
        return api_key.owner

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing credentials. Provide a Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> ApiKey:
    """Dependency that *requires* an API key (not JWT)."""
    return _resolve_api_key(x_api_key, db)


# ---------------------------------------------------------------------------
# Scope-checking dependency factory
# ---------------------------------------------------------------------------

def require_scope(scope: str):
    """
    Return a dependency that verifies the caller has a given scope.
    Works for both JWT (admin always has all scopes) and API key callers.
    """

    def _checker(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
        x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
        db: Session = Depends(get_db),
    ) -> AdminAccount:
        # JWT callers are trusted with all scopes
        if credentials is not None:
            return _resolve_admin_from_jwt(credentials, db)

        if x_api_key is not None:
            api_key = _resolve_api_key(x_api_key, db)
            if not api_key.has_scope(scope):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key does not have the required scope: {scope}",
                )
            return api_key.owner

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _checker


# ---------------------------------------------------------------------------
# Access-level gates (unchanged API, now also works with API keys)
# ---------------------------------------------------------------------------

def require_viewer(current_admin: AdminAccount = Depends(get_current_admin)) -> AdminAccount:
    """Require at least VIEWER access level."""
    if not check_access_level(AccessLevel.VIEWER, current_admin.access_level):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_admin


def require_admin(current_admin: AdminAccount = Depends(get_current_admin)) -> AdminAccount:
    """Require at least ADMIN access level."""
    if not check_access_level(AccessLevel.ADMIN, current_admin.access_level):
        raise HTTPException(status_code=403, detail="Requires ADMIN access or higher")
    return current_admin


def require_superadmin(current_admin: AdminAccount = Depends(get_current_admin)) -> AdminAccount:
    """Require SUPERADMIN access level."""
    if not check_access_level(AccessLevel.SUPERADMIN, current_admin.access_level):
        raise HTTPException(status_code=403, detail="Requires SUPERADMIN access")
    return current_admin
