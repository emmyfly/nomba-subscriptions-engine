import secrets
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.admin_auth import authorize_tenant_write, require_admin_token
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.services.verification import names_reasonably_match, verify_tenant_bank_account


router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=201)
@limiter.limit("5/hour")
def create_tenant(request: Request, data: TenantCreate, db: Session = Depends(get_db)):
    existing = db.query(Tenant).filter(Tenant.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="This email is already registered")

    api_key = f"nk_live_{secrets.token_hex(16)}"

    new_tenant = Tenant(
        name=data.name,
        email=data.email,
        api_key=api_key,
        contact_full_name=data.contact_full_name or "",
    )

    db.add(new_tenant)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This email is already registered")
    db.refresh(new_tenant)
    return new_tenant


@router.get("/", response_model=List[TenantResponse], dependencies=[Depends(require_admin_token)])
def get_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).all()


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    db: Session = Depends(get_db),
    x_admin_token: str = Header(default=""),
    authorization: str = Header(default=""),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    authorize_tenant_write(tenant, x_admin_token, authorization)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    bank_fields_touched = {"bank_account_number", "bank_code", "bank_account_name"} & update_data.keys()
    if bank_fields_touched and tenant.bank_account_number and tenant.bank_code:
        tenant.bank_verification_status = verify_tenant_bank_account(tenant)

    # Self-reported identity check: does the person's own name (given at signup)
    # match who they claim owns the bank account? Weaker than bank_verification_status
    # (both sides are self-reported, so it can't catch a consistent liar) but catches
    # honest data-entry mistakes -- e.g. typing a relative's name by accident.
    if "bank_account_name" in update_data and tenant.contact_full_name and tenant.bank_account_name:
        tenant.identity_match_status = (
            "match"
            if names_reasonably_match(tenant.contact_full_name, tenant.bank_account_name)
            else "mismatch"
        )

    db.commit()
    db.refresh(tenant)
    return tenant