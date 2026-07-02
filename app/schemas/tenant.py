from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    email: str


class TenantUpdate(BaseModel):
    nomba_subaccount_id: Optional[str] = None


class TenantResponse(BaseModel):
    id: int
    name: str
    email: str
    api_key: str
    is_active: bool
    nomba_subaccount_id: str
    created_at: datetime

    model_config = {"from_attributes": True}