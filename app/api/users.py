"""User management API endpoints."""

import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional, List

from app.database import get_db
from app.models.user import User, UserCategory, UserStatus, InternshipTracking, InternshipStatus
from app.models.role import Role, UserRole
from app.models.admin import AdminAccount, AccessLevel
from app.models.audit import AuditLog, ConversionHistory
from app.models.division import Division
from app.models.domain import Domain
from app.core.id_generator import generate_ulid, ulid_to_display_id, display_id_to_ulid_suffix, is_display_id_format
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserSearchResponse,
    InternConvertRequest, InternExtendRequest,
)
from app.api.deps import require_viewer, require_admin, require_superadmin, get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])


def _build_user_response(user: User) -> UserResponse:
    """Build a UserResponse from a User model instance."""
    roles = [ur.role.name for ur in user.user_roles if ur.removed_at is None and ur.role.is_active]
    return UserResponse(
        id=user.id,
        ulid=user.ulid,
        display_id=ulid_to_display_id(user.ulid, user.category.value),
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        category=user.category,
        status=user.status,
        domain_name=user.domain.name if user.domain else None,
        division_name=user.division.name if user.division else None,
        roles=roles,
        conversion_date=user.conversion_date,
        date_of_joining=user.date_of_joining,
        start_date=user.internship.start_date if user.internship else None,
        end_date=user.internship.end_date if user.internship else None,
        created_at=user.created_at,
    )


def _resolve_user_by_uid(db: Session, uid: str) -> User:
    """
    Resolve a user by ULID or display ID.

    If uid is 26 chars, treat as full ULID.
    If uid matches display ID format, extract suffix and search.
    Otherwise, try exact ULID match.
    """
    query = db.query(User).options(
        joinedload(User.domain),
        joinedload(User.division),
        joinedload(User.user_roles).joinedload(UserRole.role),
        joinedload(User.internship),
    ).filter(User.deleted_at == None)

    # Full ULID (26 chars)
    if len(uid) == 26:
        return query.filter(User.ulid == uid.upper()).first()

    # Display ID format (e.g., INT-T6V4-B1C9-D0 or T6V4-B1C9-D0)
    if is_display_id_format(uid):
        try:
            suffix = display_id_to_ulid_suffix(uid)
            return query.filter(User.ulid.endswith(suffix)).first()
        except ValueError:
            return None

    # Try as-is (could be partial or old format)
    return query.filter(User.ulid == uid.upper()).first()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Create a new user and generate their unique ULID (Superadmin only)."""
    # Validate intern fields
    if request.category == UserCategory.INTERN:
        if not request.start_date or not request.end_date:
            raise HTTPException(
                status_code=400,
                detail="Interns require start_date and end_date",
            )
        if request.end_date <= request.start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date",
            )

    # Check email uniqueness
    if db.query(User).filter(User.email == request.email, User.deleted_at == None).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Generate ULID
    ulid_value = generate_ulid(db)

    # Create user
    user = User(
        ulid=ulid_value,
        name=request.name,
        email=request.email,
        phone_number=request.phone_number,
        category=request.category,
        domain_id=request.domain_id,
        division_id=request.division_id,
        date_of_joining=request.date_of_joining or datetime.utcnow().date(),
    )
    db.add(user)
    db.flush()  # Get user.id

    # Create internship tracking if intern
    if request.category == UserCategory.INTERN:
        internship = InternshipTracking(
            user_id=user.id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        db.add(internship)

    # Assign roles if provided
    for role_id in (request.role_ids or []):
        role = db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
        if role:
            db.add(UserRole(user_id=user.id, role_id=role_id, assigned_by=current_admin.id))

    # Audit log
    db.add(AuditLog(
        action="USER_CREATED",
        entity_type="user",
        entity_id=ulid_value,
        changed_by=current_admin.id,
        new_value={
            "name": request.name,
            "category": request.category.value,
            "email": request.email,
            "phone_number": request.phone_number,
            "domain_id": request.domain_id,
            "division_id": request.division_id,
            "date_of_joining": str(user.date_of_joining),
        },
    ))

    db.commit()
    db.refresh(user)
    return _build_user_response(user)


from sqlalchemy import or_

@router.get("", response_model=UserSearchResponse)
def search_users(
    q: Optional[str] = Query(None, description="Generic search (Name, ULID, Display ID, Email)"),
    name: Optional[str] = Query(None),
    ulid: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    category: Optional[UserCategory] = Query(None),
    status_filter: Optional[List[UserStatus]] = Query(None, alias="status"),
    domain_id: Optional[int] = Query(None),
    division_id: Optional[int] = Query(None),
    include_deleted: bool = Query(False, description="Include soft-deleted users"),
    deleted_only: bool = Query(False, description="Only return soft-deleted users"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """Search users with filtering (Viewer+ access)."""
    query = db.query(User).options(
        joinedload(User.domain),
        joinedload(User.division),
        joinedload(User.user_roles).joinedload(UserRole.role),
        joinedload(User.internship),
    )

    if deleted_only:
        query = query.filter(User.deleted_at != None)
    elif not include_deleted:
        query = query.filter(User.deleted_at == None)

    # Generic search (OR logic)
    if q:
        search_term = f"%{q}%"
        search_filters = [
            User.name.ilike(search_term),
            User.email.ilike(search_term),
            User.ulid == q.upper(),
        ]
        # Also check if it's a display ID format
        if is_display_id_format(q):
            try:
                suffix = display_id_to_ulid_suffix(q)
                search_filters.append(User.ulid.endswith(suffix))
            except ValueError:
                pass
        query = query.filter(or_(*search_filters))

    # Specific filters (AND logic)
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if ulid:
        query = query.filter(User.ulid == ulid.upper())
    if category:
        query = query.filter(User.category == category)
    if status_filter:
        query = query.filter(User.status.in_(status_filter))
    if domain_id:
        query = query.filter(User.domain_id == domain_id)
    if division_id:
        query = query.filter(User.division_id == division_id)
    if role:
        query = query.join(User.user_roles).join(UserRole.role).filter(
            Role.name.ilike(f"%{role}%"),
            UserRole.removed_at == None,
        )

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return UserSearchResponse(
        users=[_build_user_response(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.get("/{uid}", response_model=UserResponse)
def get_user(
    uid: str,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """Get a single user by their ULID or display ID (Viewer+ access)."""
    # Allow fetching deleted users if accessed directly by ID
    query = db.query(User).options(
        joinedload(User.domain),
        joinedload(User.division),
        joinedload(User.user_roles).joinedload(UserRole.role),
        joinedload(User.internship),
    )

    if len(uid) == 26:
        user = query.filter(User.ulid == uid.upper()).first()
    elif is_display_id_format(uid):
        try:
            suffix = display_id_to_ulid_suffix(uid)
            user = query.filter(User.ulid.endswith(suffix)).first()
        except ValueError:
            user = None
    else:
        user = query.filter(User.ulid == uid.upper()).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _build_user_response(user)


@router.put("/{uid}", response_model=UserResponse)
def update_user(
    uid: str,
    request: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Update user details (Admin+ access). Supports optimistic locking via version field."""
    user = db.query(User).filter(User.ulid == uid.upper(), User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Optimistic locking check
    if request.version is not None and request.version != user.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User was modified by another request. Please reload and try again.",
        )

    previous = {
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "status": user.status.value,
        "division_id": user.division_id,
        "domain_id": user.domain_id,
        "date_of_joining": str(user.date_of_joining),
    }

    if request.name is not None:
        user.name = request.name
    if request.email is not None:
        user.email = request.email
    if request.phone_number is not None:
        user.phone_number = request.phone_number
    if request.domain_id is not None:
        user.domain_id = request.domain_id
    if request.division_id is not None:
        user.division_id = request.division_id
    if request.date_of_joining is not None:
        user.date_of_joining = request.date_of_joining
    if request.status is not None:
        user.status = request.status

    user.updated_at = datetime.utcnow()
    user.version = (user.version or 1) + 1

    db.add(AuditLog(
        action="USER_UPDATED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        previous_value=previous,
        new_value={
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "status": user.status.value,
            "date_of_joining": str(user.date_of_joining),
        },
    ))

    db.commit()
    db.refresh(user)
    return _build_user_response(user)


@router.delete("/{uid}")
def soft_delete_user(
    uid: str,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Soft-delete a user (Superadmin only)."""
    user = db.query(User).filter(User.ulid == uid.upper(), User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.deleted_at = datetime.utcnow()
    user.status = UserStatus.INACTIVE

    db.add(AuditLog(
        action="USER_DELETED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        description=f"User {user.name} soft-deleted",
    ))

    db.commit()
    return {"message": f"User {user.ulid} deleted", "ulid": user.ulid}


@router.post("/{uid}/restore")
def restore_user(
    uid: str,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Restore a soft-deleted user (Superadmin only)."""
    # Find deleted user
    user = db.query(User).filter(User.ulid == uid.upper()).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.deleted_at is None:
        raise HTTPException(status_code=400, detail="User is already active")

    user.deleted_at = None
    user.status = UserStatus.ACTIVE
    user.updated_at = datetime.utcnow()

    db.add(AuditLog(
        action="USER_RESTORED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        description=f"User {user.name} restored from trash",
    ))

    db.commit()
    return {"message": f"User {user.ulid} restored", "ulid": user.ulid}


@router.delete("/{uid}/permanent")
def permanent_delete_user(
    uid: str,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Permanently delete a user (Superadmin only). Cannot be undone."""
    user = db.query(User).options(
        joinedload(User.internship),
    ).filter(User.ulid == uid.upper()).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Capture details for audit before deletion
    user_details = {
        "ulid": user.ulid,
        "name": user.name,
        "email": user.email
    }

    # Delete internship record explicitly if cascade doesn't cover it (it should if configured, but safe to be explicit)
    if user.internship:
        db.delete(user.internship)

    # Delete user (UserRoles should cascade)
    db.delete(user)

    db.add(AuditLog(
        action="USER_PERMANENTLY_DELETED",
        entity_type="user",
        entity_id=user_details["ulid"], # Note: Entity will no longer exist
        changed_by=current_admin.id,
        description=f"User {user_details['name']} ({user_details['email']}) permanently deleted",
    ))

    db.commit()
    return {"message": f"User {uid} permanently deleted"}


# --- Role assignment endpoints ---

@router.post("/{uid}/roles", status_code=status.HTTP_201_CREATED)
def assign_role(
    uid: str,
    role_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Assign a role to a user (Admin+ access)."""
    user = db.query(User).filter(User.ulid == uid.upper(), User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found or inactive")

    # Check if already assigned
    existing = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == role_id,
        UserRole.removed_at == None,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Role already assigned")

    db.add(UserRole(user_id=user.id, role_id=role_id, assigned_by=current_admin.id))

    db.add(AuditLog(
        action="ROLE_ASSIGNED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        new_value={"role": role.name},
    ))

    db.commit()
    return {"message": f"Role '{role.name}' assigned to user '{user.name}'"}


@router.delete("/{uid}/roles/{role_id}")
def remove_role(
    uid: str,
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Remove a role from a user (Admin+ access)."""
    user = db.query(User).filter(User.ulid == uid.upper(), User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == role_id,
        UserRole.removed_at == None,
    ).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="Role assignment not found")

    user_role.removed_at = datetime.utcnow()

    db.add(AuditLog(
        action="ROLE_REMOVED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        previous_value={"role": user_role.role.name},
    ))

    db.commit()
    return {"message": "Role removed successfully"}


# --- Intern lifecycle endpoints ---

@router.post("/{uid}/convert", response_model=UserResponse)
def convert_intern(
    uid: str,
    request: InternConvertRequest,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """
    Convert an intern to a permanent employee (Superadmin only).

    ULID is immutable — only the category changes.
    Display ID prefix updates automatically from INT- to EMP-.
    """
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role),
        joinedload(User.internship),
        joinedload(User.division),
    ).filter(User.ulid == uid.upper(), User.deleted_at == None).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.category != UserCategory.INTERN:
        raise HTTPException(status_code=400, detail="User is not an intern")
    if user.status == UserStatus.CONVERTED:
        raise HTTPException(status_code=400, detail="User already converted")

    # Collect current active roles
    active_roles = [ur.role.name for ur in user.user_roles if ur.removed_at is None]

    # Update user record — ULID stays the same!
    previous_category = user.category.value
    user.category = UserCategory.EMPLOYEE
    user.status = UserStatus.ACTIVE
    user.conversion_date = datetime.utcnow()
    user.updated_at = datetime.utcnow()

    # Update internship tracking
    if user.internship:
        user.internship.status = InternshipStatus.CONVERTED
        user.internship.updated_at = datetime.utcnow()

    # Record conversion history
    db.add(ConversionHistory(
        user_id=user.id,
        user_ulid=user.ulid,
        previous_category=previous_category,
        new_category=UserCategory.EMPLOYEE.value,
        converted_by=current_admin.id,
        roles_migrated=active_roles,
    ))

    # Audit log
    db.add(AuditLog(
        action="INTERN_CONVERTED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        previous_value={"category": previous_category},
        new_value={
            "category": "EMPLOYEE",
            "roles_migrated": active_roles,
            "display_id": ulid_to_display_id(user.ulid, "EMPLOYEE"),
        },
    ))

    db.commit()
    db.refresh(user)
    return _build_user_response(user)


@router.post("/{uid}/extend", response_model=UserResponse)
def extend_internship(
    uid: str,
    request: InternExtendRequest,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Extend an intern's end date (Superadmin only)."""
    user = db.query(User).options(
        joinedload(User.internship),
        joinedload(User.division),
        joinedload(User.user_roles).joinedload(UserRole.role),
    ).filter(User.ulid == uid.upper(), User.deleted_at == None).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.category != UserCategory.INTERN:
        raise HTTPException(status_code=400, detail="User is not an intern")
    if not user.internship:
        raise HTTPException(status_code=400, detail="No internship record found")

    old_end_date = user.internship.end_date

    if request.new_end_date <= old_end_date:
        raise HTTPException(status_code=400, detail="New end date must be after current end date")

    user.internship.end_date = request.new_end_date
    user.internship.extended_count += 1
    user.internship.override_reason = request.reason
    user.internship.status = InternshipStatus.EXTENDED
    user.internship.updated_at = datetime.utcnow()

    # Reactivate if expired
    if user.status == UserStatus.EXPIRED:
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.utcnow()

    db.add(AuditLog(
        action="INTERNSHIP_EXTENDED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        previous_value={"end_date": str(old_end_date)},
        new_value={"end_date": str(request.new_end_date), "reason": request.reason},
    ))

    db.commit()
    db.refresh(user)
    return _build_user_response(user)


@router.post("/{uid}/end-internship", response_model=UserResponse)
def end_internship(
    uid: str,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """End an internship early (Admin+ access)."""
    user = db.query(User).options(
        joinedload(User.internship),
        joinedload(User.division),
        joinedload(User.user_roles).joinedload(UserRole.role),
    ).filter(User.ulid == uid.upper(), User.deleted_at == None).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.category != UserCategory.INTERN:
        raise HTTPException(status_code=400, detail="User is not an intern")
    if not user.internship:
        raise HTTPException(status_code=400, detail="No internship record found")
    if user.status in [UserStatus.EXPIRED, UserStatus.CONVERTED, UserStatus.INACTIVE]:
        raise HTTPException(status_code=400, detail=f"Internship already ended (Status: {user.status.value})")

    # Update internship status
    user.internship.status = InternshipStatus.EXPIRED
    user.internship.end_date = datetime.utcnow().date() # Set end date to today
    user.internship.updated_at = datetime.utcnow()

    # Update user status
    user.status = UserStatus.EXPIRED
    user.updated_at = datetime.utcnow()

    # Log
    db.add(AuditLog(
        action="INTERNSHIP_ENDED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        description=f"Internship for {user.name} ended early by admin",
    ))

    db.commit()
    db.refresh(user)
    return _build_user_response(user)


@router.post("/{uid}/retire", response_model=UserResponse)
def retire_employee(
    uid: str,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Retire an employee (mark as INACTIVE) (Admin+ access)."""
    user = db.query(User).options(
        joinedload(User.internship),
        joinedload(User.division),
        joinedload(User.user_roles).joinedload(UserRole.role),
    ).filter(User.ulid == uid.upper(), User.deleted_at == None).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.category != UserCategory.EMPLOYEE:
        raise HTTPException(status_code=400, detail="User is not an employee")
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(status_code=400, detail="User is already inactive")

    # Update user status
    previous_status = user.status.value
    user.status = UserStatus.INACTIVE
    user.updated_at = datetime.utcnow()

    # Log
    db.add(AuditLog(
        action="USER_RETIRED",
        entity_type="user",
        entity_id=user.ulid,
        changed_by=current_admin.id,
        previous_value={"status": previous_status},
        new_value={"status": "INACTIVE"},
        description=f"Employee {user.name} retired/deactivated",
    ))

    db.commit()
    db.refresh(user)
    return _build_user_response(user)
