"""Division management API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.division import Division
from app.models.admin import AdminAccount
from app.api.deps import require_viewer, require_superadmin

router = APIRouter(prefix="/divisions", tags=["Divisions"])


class DivisionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class DivisionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[DivisionResponse])
def list_divisions(
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """List all active divisions."""
    query = db.query(Division)
    
    if deleted_only:
        query = query.filter(Division.deleted_at != None)
    elif not include_deleted:
        query = query.filter(Division.deleted_at == None, Division.is_active == True)
        
    divisions = query.order_by(Division.name).all()
    return [DivisionResponse.model_validate(d) for d in divisions]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DivisionResponse)
def create_division(
    request: DivisionCreate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Create a new division (Superadmin only)."""
    existing = db.query(Division).filter(Division.name == request.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Division name already exists")

    division = Division(name=request.name, description=request.description)
    db.add(division)
    db.commit()
    db.refresh(division)
    db.refresh(division)
    return DivisionResponse.model_validate(division)


class DivisionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/{division_id}", response_model=DivisionResponse)
def update_division(
    division_id: int,
    request: DivisionUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Update a division (Superadmin only)."""
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")

    if request.name is not None and request.name != division.name:
        existing = db.query(Division).filter(Division.name == request.name).first()
        if existing:
            raise HTTPException(status_code=409, detail="Division name already exists")
        division.name = request.name

    if request.description is not None:
        division.description = request.description

    if request.is_active is not None:
        division.is_active = request.is_active

    db.commit()
    db.refresh(division)
    return DivisionResponse.model_validate(division)


@router.delete("/{division_id}")
def delete_division(
    division_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Soft-delete a division (Superadmin only)."""
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")

    division.deleted_at = datetime.utcnow()
    division.is_active = False
    db.commit()
    return {"message": f"Division '{division.name}' soft-deleted"}


@router.post("/{division_id}/restore")
def restore_division(
    division_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Restore a soft-deleted division (Superadmin only)."""
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")

    division.deleted_at = None
    division.is_active = True
    db.commit()
    return {"message": f"Division '{division.name}' restored"}


@router.delete("/{division_id}/permanent")
def permanent_delete_division(
    division_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Permanently delete a division (Superadmin only)."""
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")

    db.delete(division)
    db.commit()
    return {"message": f"Division permanently deleted"}
