from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.webhook_delivery_log import WebhookDeliveryLog
from app.schemas.payment import WebhookDeliveryLogResponse


router = APIRouter()


@router.get("/", response_model=List[WebhookDeliveryLogResponse])
def get_webhook_deliveries(tenant_id: int = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(WebhookDeliveryLog)
    if tenant_id:
        query = query.filter(WebhookDeliveryLog.tenant_id == tenant_id)
    logs = query.order_by(WebhookDeliveryLog.created_at.desc()).limit(limit).all()
    return logs
