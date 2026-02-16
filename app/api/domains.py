"""Division management API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.domain import Domain
from app.models.admin import AdminAccount
from app.api.deps import require_viewer, require_superadmin

router = APIRouter(prefix="/domains", tags=["Domains"])


class DomainCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class DomainResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[DomainResponse])
def list_domains(
    include_deleted: bool = Query(False),
    deleted_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """List all active domains."""
    query = db.query(Domain)
    
    if deleted_only:
        query = query.filter(Domain.deleted_at != None)
    elif not include_deleted:
        query = query.filter(Domain.deleted_at == None, Domain.is_active == True)
        
    domains = query.order_by(Domain.name).all()
    return [DomainResponse.model_validate(d) for d in domains]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DomainResponse)
def create_domain(
    request: DomainCreate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Create a new domain (Superadmin only)."""
    existing = db.query(Domain).filter(Domain.name == request.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Domain name already exists")

    domain = Domain(name=request.name, description=request.description)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    db.refresh(domain)
    return DomainResponse.model_validate(domain)


class DomainUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/{domain_id}", response_model=DomainResponse)
def update_domain(
    domain_id: int,
    request: DomainUpdate,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Update a domain (Superadmin only)."""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if request.name is not None and request.name != domain.name:
        existing = db.query(Domain).filter(Domain.name == request.name).first()
        if existing:
            raise HTTPException(status_code=409, detail="Domain name already exists")
        domain.name = request.name

    if request.description is not None:
        domain.description = request.description

    if request.is_active is not None:
        domain.is_active = request.is_active

    db.commit()
    db.refresh(domain)
    return DomainResponse.model_validate(domain)


@router.delete("/{domain_id}")
def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Soft-delete a domain (Superadmin only)."""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain.deleted_at = datetime.utcnow()
    domain.is_active = False
    db.commit()
    return {"message": f"Domain '{domain.name}' soft-deleted"}


@router.post("/{domain_id}/restore")
def restore_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Restore a soft-deleted domain (Superadmin only)."""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain.deleted_at = None
    domain.is_active = True
    db.commit()
    return {"message": f"Domain '{domain.name}' restored"}


@router.delete("/{domain_id}/permanent")
def permanent_delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_superadmin),
):
    """Permanently delete a domain (Superadmin only)."""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    db.delete(domain)
    db.commit()
    return {"message": f"Domain permanently deleted"}
