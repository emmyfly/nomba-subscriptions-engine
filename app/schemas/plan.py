from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PlanCreate(BaseModel):
    tenant_id: int
    name: str
    description: str = ""
    price: float
    billing_cycle: str


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    billing_cycle: Optional[str] = None
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    tenant_id: int
    id: int
    name: str
    description: str
    price: float
    billing_cycle: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}