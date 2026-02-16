"""Authentication API endpoints: login, refresh, register, logout, password reset."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.admin import AdminAccount, AccessLevel
from app.models.audit import AuditLog
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    decode_token, revoke_token,
)
from app.api.deps import require_superadmin, get_current_admin
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    access_level: AccessLevel
    username: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    access_level: AccessLevel = AccessLevel.VIEWER


class PasswordResetRequest(BaseModel):
    admin_id: int
    new_password: str = Field(..., min_length=8)


# --- Helpers ---

def _log_auth_event(db: Session, action: str, admin: AdminAccount = None, ip: str = None, description: str = None):
    """Log authentication events to audit trail."""
    log = AuditLog(
        action=action,
        entity_type="ADMIN",
        entity_id=str(admin.id) if admin else None,
        changed_by=admin.id if admin else None,
        description=description,
        ip_address=ip,
    )
    db.add(log)
    db.commit()


# --- Endpoints ---

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, login_req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate admin and return JWT tokens."""
    client_ip = request.client.host if request.client else None

    admin = db.query(AdminAccount).filter(
        AdminAccount.username == login_req.username,
        AdminAccount.is_active == True,
    ).first()

    if not admin or not verify_password(login_req.password, admin.password_hash):
        # Log failed login attempt
        if admin:
            _log_auth_event(db, "LOGIN_FAILED", admin, client_ip, f"Failed login attempt for {login_req.username}")
        else:
            # Log without admin reference for unknown usernames
            log = AuditLog(
                action="LOGIN_FAILED",
                entity_type="ADMIN",
                description=f"Failed login attempt for unknown user: {login_req.username}",
                ip_address=client_ip,
            )
            db.add(log)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()

    # Generate tokens
    token_data = {
        "sub": str(admin.id),
        "level": admin.access_level.value,
        "username": admin.username,
    }

    # Log successful login
    _log_auth_event(db, "LOGIN_SUCCESS", admin, client_ip, f"Admin {admin.username} logged in")

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        access_level=admin.access_level,
        username=admin.username,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    admin_id = payload.get("sub")
    admin = db.query(AdminAccount).filter(
        AdminAccount.id == int(admin_id),
        AdminAccount.is_active == True,
    ).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive",
        )

    # Revoke old refresh token
    old_jti = payload.get("jti")
    if old_jti:
        revoke_token(old_jti)

    token_data = {
        "sub": str(admin.id),
        "level": admin.access_level.value,
        "username": admin.username,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        access_level=admin.access_level,
        username=admin.username,
    )


@router.post("/logout")
def logout(request: Request, current_admin: AdminAccount = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Logout: revoke the current access token on the server side."""
    # Extract JTI from the current token
    from fastapi.security import HTTPAuthorizationCredentials
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if payload and payload.get("jti"):
            revoke_token(payload["jti"])

    client_ip = request.client.host if request.client else None
    _log_auth_event(db, "LOGOUT", current_admin, client_ip, f"Admin {current_admin.username} logged out")

    return {"message": "Logged out successfully"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_admin(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Register a new admin account (Superadmin only)."""
    existing = db.query(AdminAccount).filter(AdminAccount.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    admin = AdminAccount(
        username=req.username,
        password_hash=hash_password(req.password),
        access_level=req.access_level,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    # Audit log
    log = AuditLog(
        action="ADMIN_CREATED",
        entity_type="ADMIN",
        entity_id=str(admin.id),
        changed_by=current_admin.id,
        description=f"Admin {req.username} created with {req.access_level.value} access",
    )
    db.add(log)
    db.commit()

    return {"id": admin.id, "username": admin.username, "access_level": admin.access_level}


@router.post("/password-reset")
def reset_password(
    req: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Reset another admin's password (Superadmin only)."""
    target_admin = db.query(AdminAccount).filter(AdminAccount.id == req.admin_id).first()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    target_admin.password_hash = hash_password(req.new_password)
    db.commit()

    client_ip = request.client.host if request.client else None
    _log_auth_event(
        db, "PASSWORD_RESET", current_admin, client_ip,
        f"Password reset for {target_admin.username} by {current_admin.username}",
    )

    return {"message": f"Password reset for {target_admin.username}"}
    return {"message": f"Password reset for {target_admin.username}"}


@router.get("/me", response_model=TokenResponse)
def get_current_admin_info(current_admin: AdminAccount = Depends(get_current_admin)):
    """Get current logged-in admin details."""
    # We can reuse TokenResponse structure or create a specific ProfileResponse
    # Reusing TokenResponse but with dummy tokens is a bit hacky, but works if frontend handles it.
    # Better to just return the user details.
    # Let's use a new schema inline or simple dict for now, or reuse TokenResponse without tokens if possible.
    # Actually, the frontend might expect the same structure as login for consistency.
    # But TokenResponse requires tokens.
    # I'll create a simple ProfileResponse schema at top or just return dict.
    return {
        "access_token": "", # Dummy
        "refresh_token": "", # Dummy
        "access_level": current_admin.access_level,
        "username": current_admin.username,
        "id": current_admin.id
    }

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(get_current_admin),
):
    """Change current admin's password."""
    if not verify_password(req.current_password, current_admin.password_hash):
        _log_auth_event(db, "PASSWORD_CHANGE_FAILED", current_admin, request.client.host, "Incorrect current password")
        raise HTTPException(status_code=400, detail="Incorrect current password")

    current_admin.password_hash = hash_password(req.new_password)
    db.commit()

    _log_auth_event(db, "PASSWORD_CHANGED", current_admin, request.client.host, "User changed their own password")
    
    return {"message": "Password changed successfully"}
