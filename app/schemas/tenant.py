from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    email: str


class TenantUpdate(BaseModel):
    nomba_subaccount_id: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_code: Optional[str] = None
    bank_account_name: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


class TenantResponse(BaseModel):
    id: int
    name: str
    email: str
    api_key: str
    is_active: bool
    nomba_subaccount_id: str
    bank_account_number: str
    bank_code: str
    bank_account_name: str
    bank_verification_status: str
    webhook_url: str
    created_at: datetime

    model_config = {"from_attributes": True}