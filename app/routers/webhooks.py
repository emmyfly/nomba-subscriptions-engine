import logging

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.webhook_handler import process_payment_webhook
from app.services.nomba_webhook_security import verify_nomba_signature

logger = logging.getLogger("subflow.webhooks")

router = APIRouter()


@router.post("/nomba")
async def receive_nomba_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if settings.NOMBA_WEBHOOK_SECRET:
        signature = request.headers.get("nomba-signature", "")
        timestamp = request.headers.get("nomba-timestamp", "")
        if not verify_nomba_signature(payload, signature, timestamp, settings.NOMBA_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    else:
        logger.warning(
            "NOMBA_WEBHOOK_SECRET not configured -- processing webhook without "
            "signature verification"
        )

    result = process_payment_webhook(payload=payload, db=db)
    return {"status": "received", "detail": result}