import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse


router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=201)
def create_tenant(data: TenantCreate, db: Session = Depends(get_db)):
    api_key = f"nk_live_{secrets.token_hex(16)}"

    new_tenant = Tenant(
        name=data.name,
        email=data.email,
        api_key=api_key,
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return new_tenant


@router.get("/", response_model=List[TenantResponse])
def get_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(tenant_id: int, data: TenantUpdate, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return tenant