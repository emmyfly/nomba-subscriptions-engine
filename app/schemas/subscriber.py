from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SubscriberCreate(BaseModel):
    tenant_id: int
    name: str
    email: str
    phone: str = ""
    plan_id: int


class SubscriberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    plan_id: Optional[int] = None
    status: Optional[str] = None


class SubscriberResponse(BaseModel):
    tenant_id: int
    id: int
    name: str
    email: str
    phone: str
    plan_id: int
    status: str
    nomba_virtual_account_id: str
    nomba_account_number: str
    nomba_bank_name: str
    amount: float
    accumulated_balance: float
    next_billing_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}