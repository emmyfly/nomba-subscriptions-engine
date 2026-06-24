from datetime import datetime
from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str
    email: str


class TenantResponse(BaseModel):
    id: int
    name: str
    email: str
    api_key: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}