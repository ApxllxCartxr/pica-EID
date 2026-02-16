"""Role management API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.role import Role, UserRole
from app.models.user import User
from app.models.admin import AdminAccount
from app.models.audit import AuditLog
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse, RoleListResponse
from app.api.deps import require_viewer, require_superadmin

router = APIRouter(prefix="/roles", tags=["Roles"])


def _build_role_response(role: Role, db: Session) -> RoleResponse:
    """Build a RoleResponse with assigned user count."""
    count = db.query(UserRole).filter(
        UserRole.role_id == role.id,
        UserRole.removed_at == None,
    ).count()
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        clearance_level=role.clearance_level,
        is_active=role.is_active,
        assigned_users_count=count,
        created_at=role.created_at,
    )


@router.get("", response_model=RoleListResponse)
def list_roles(
    include_inactive: bool = Query(False),
    deleted_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """List all roles (Viewer+ access)."""
    query = db.query(Role)
    if deleted_only:
        query = query.filter(Role.deleted_at != None)
    elif not include_inactive:
        # "Active" means not deleted AND is_active=True
        query = query.filter(Role.deleted_at == None, Role.is_active == True)
    else:
        # Include inactive means all non-deleted (maybe? or all?)
        # Let's say "include_inactive" means include disabled roles, but NOT soft-deleted ones?
        # Standard pattern: soft-deleted are hidden unless specifically asked.
        # If I want inactive (disabled) roles, I pass include_inactive=True.
        # But deleted roles are "trashed".
        # So filter(Role.deleted_at == None) always unless deleted_only?
        # Or add include_deleted param?
        # Let's assume list_roles generally lists non-deleted roles.
        query = query.filter(Role.deleted_at == None) # Always exclude trash unless deleted_only
        # If include_inactive is False (default), we only want is_active=True
        # If include_inactive is True, we want both.
        # Wait, if deleted_only is set, we ignore include_inactive.
        pass # query already filtered for deleted_only above if set.
    
    if not deleted_only and not include_inactive:
         query = query.filter(Role.is_active == True)

    roles = query.order_by(Role.clearance_level.desc(), Role.name).all()
    return RoleListResponse(
        roles=[_build_role_response(r, db) for r in roles],
        total=len(roles),
    )


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """Get a single role by ID (Viewer+ access)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return _build_role_response(role, db)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RoleResponse)
def create_role(
    request: RoleCreate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Create a new role (Superadmin only)."""
    existing = db.query(Role).filter(Role.name == request.name, Role.is_active == True).first()
    if existing:
        raise HTTPException(status_code=409, detail="Role name already exists")

    role = Role(
        name=request.name,
        description=request.description,
        clearance_level=request.clearance_level,
    )
    db.add(role)

    db.add(AuditLog(
        action="ROLE_CREATED",
        entity_type="role",
        entity_id=request.name,
        changed_by=current_admin.id,
        new_value={"name": request.name, "clearance_level": request.clearance_level},
    ))

    db.commit()
    db.refresh(role)
    return _build_role_response(role, db)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Update a role (Superadmin only). Supports optimistic locking."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Optimistic locking check
    if request.version is not None and request.version != role.version:
        raise HTTPException(
            status_code=409,
            detail="Role was modified by another request. Please reload and try again.",
        )

    previous = {
        "name": role.name,
        "description": role.description,
        "clearance_level": role.clearance_level,
        "is_active": role.is_active,
    }

    if request.name is not None:
        dup = db.query(Role).filter(Role.name == request.name, Role.id != role_id, Role.is_active == True).first()
        if dup:
            raise HTTPException(status_code=409, detail="Role name already exists")
        role.name = request.name
    if request.description is not None:
        role.description = request.description
    if request.clearance_level is not None:
        role.clearance_level = request.clearance_level
    if request.is_active is not None:
        role.is_active = request.is_active

    role.updated_at = datetime.utcnow()
    role.version = (role.version or 1) + 1

    db.add(AuditLog(
        action="ROLE_UPDATED",
        entity_type="role",
        entity_id=str(role_id),
        changed_by=current_admin.id,
        previous_value=previous,
        new_value={
            "name": role.name,
            "description": role.description,
            "clearance_level": role.clearance_level,
            "is_active": role.is_active,
        },
    ))

    db.commit()
    db.refresh(role)
    return _build_role_response(role, db)


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Soft-delete a role (Superadmin only)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if assigned to active users
    active_assignments = db.query(UserRole).join(User).filter(
        UserRole.role_id == role_id,
        UserRole.removed_at == None,
        User.deleted_at == None,
    ).count()

    if active_assignments > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role assigned to {active_assignments} active user(s). "
                   "Remove assignments first.",
        )

    role.deleted_at = datetime.utcnow()
    role.is_active = False
    role.updated_at = datetime.utcnow()

    db.add(AuditLog(
        action="ROLE_DELETED",
        entity_type="role",
        entity_id=str(role_id),
        changed_by=current_admin.id,
        previous_value={"name": role.name, "is_active": True},
        new_value={"is_active": False, "deleted_at": str(role.deleted_at)},
    ))

    db.commit()
    return {"message": f"Role '{role.name}' soft-deleted"}


@router.post("/{role_id}/restore")
def restore_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Restore a soft-deleted role (Superadmin only)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.deleted_at = None
    role.is_active = True
    role.updated_at = datetime.utcnow()

    db.add(AuditLog(
        action="ROLE_RESTORED",
        entity_type="role",
        entity_id=str(role_id),
        changed_by=current_admin.id,
        description=f"Role {role.name} restored",
    ))

    db.commit()
    return {"message": f"Role '{role.name}' restored"}


@router.delete("/{role_id}/permanent")
def permanent_delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Permanently delete a role (Superadmin only)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Verify no assignments exist (even soft ones, mostly)
    # Actually, permanent delete should cascade or fail?
    # UserRole has foreign key to Role. If we delete Role, we must cascade.
    # But SqlAlchemy relationship usually handles cascade if defined.
    # Let's check model. UserRole links to Role.
    # We should probably force manual removal or allow cascade if configured database-side.
    # For safety, let's reject if assignments exist.
    
    assignments = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if assignments > 0:
        # If we really want "permanent delete", we should probably cascade delete assignments?
        # User requested "same permanent delete function".
        # For users, we deleted User and Internship.
        # For Roles, removing role means removing valid permission from users.
        # I will cascade delete assignments.
        db.query(UserRole).filter(UserRole.role_id == role_id).delete()
    
    name = role.name
    db.delete(role)
    
    db.add(AuditLog(
        action="ROLE_PERMANENTLY_DELETED",
        entity_type="role",
        entity_id=name, # Name as ID since ID is gone
        changed_by=current_admin.id,
        description=f"Role {name} permanently deleted",
    ))

    db.commit()
    return {"message": f"Role permanently deleted"}
