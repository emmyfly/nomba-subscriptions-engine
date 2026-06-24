from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.webhook_handler import process_payment_webhook


router = APIRouter()


@router.post("/nomba")
async def receive_nomba_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    result = process_payment_webhook(payload=payload, db=db)
    return {"status": "received", "detail": result}