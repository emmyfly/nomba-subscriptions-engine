from datetime import datetime
from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: int
    subscriber_id: int
    amount: float
    status: str
    event_type: str
    nomba_transaction_ref: str
    nomba_session_id: str
    created_at: datetime

    model_config = {"from_attributes": True}