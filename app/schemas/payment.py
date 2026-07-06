from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: int
    subscriber_id: int
    amount: float
    status: str
    event_type: str
    nomba_transaction_ref: str
    nomba_session_id: str
    payout_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PayoutLogResponse(BaseModel):
    id: int
    tenant_id: int
    payment_id: int
    gross_amount: float
    platform_fee: float
    net_amount: float
    status: str
    nomba_transfer_ref: str
    error_detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryLogResponse(BaseModel):
    id: int
    tenant_id: int
    event_type: str
    url: str
    success: bool
    status_code: Optional[int]
    error_detail: str
    created_at: datetime

    model_config = {"from_attributes": True}