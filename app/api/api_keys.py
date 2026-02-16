"""API Key management endpoints — create, list, revoke keys."""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import AdminAccount
from app.models.api_key import ApiKey
from app.models.audit import AuditLog
from app.api.deps import require_admin, get_current_admin
from app.core.security import generate_api_key, hash_api_key, get_api_key_prefix


router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# --- Schemas ---

class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human label for the key")
    scopes: str = Field(
        default="*",
        description="Comma-separated scopes, e.g. 'users:read,roles:read'. Use '*' for full access.",
    )
    expires_in_days: Optional[int] = Field(
        default=None,
        description="Days until expiry. Null = never expires.",
        ge=1,
        le=365,
    )


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    owner_username: str

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only on creation — includes the full plain-text key (shown once)."""
    plain_key: str = Field(
        ...,
        description="The full API key. Store it securely — it will NOT be shown again.",
    )


# --- Endpoints ---

@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    req: CreateApiKeyRequest,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Create a new API key. The full key is only returned once."""
    from datetime import timedelta

    plain_key = generate_api_key()
    hashed = hash_api_key(plain_key)
    prefix = get_api_key_prefix(plain_key)

    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

    api_key = ApiKey(
        name=req.name,
        key_prefix=prefix,
        key_hash=hashed,
        scopes=req.scopes,
        owner_id=current_admin.id,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Audit
    db.add(AuditLog(
        action="API_KEY_CREATED",
        entity_type="API_KEY",
        entity_id=str(api_key.id),
        changed_by=current_admin.id,
        description=f"API key '{req.name}' created (scopes: {req.scopes})",
    ))
    db.commit()

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        owner_username=current_admin.username,
        plain_key=plain_key,
    )


@router.get("", response_model=List[ApiKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """List all API keys (admin sees all, non-superadmin sees own)."""
    from app.models.admin import AccessLevel

    query = db.query(ApiKey)
    if current_admin.access_level != AccessLevel.SUPERADMIN:
        query = query.filter(ApiKey.owner_id == current_admin.id)

    keys = query.order_by(ApiKey.created_at.desc()).all()
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            is_active=k.is_active,
            created_at=k.created_at,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            owner_username=k.owner.username,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Revoke (soft-delete) an API key."""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Non-superadmins can only revoke their own keys
    from app.models.admin import AccessLevel
    if (
        current_admin.access_level != AccessLevel.SUPERADMIN
        and api_key.owner_id != current_admin.id
    ):
        raise HTTPException(status_code=403, detail="Cannot revoke another admin's key")

    api_key.is_active = False
    db.commit()

    # Audit
    db.add(AuditLog(
        action="API_KEY_REVOKED",
        entity_type="API_KEY",
        entity_id=str(api_key.id),
        changed_by=current_admin.id,
        description=f"API key '{api_key.name}' revoked",
    ))
    db.commit()

    return {"message": f"API key '{api_key.name}' revoked successfully"}
