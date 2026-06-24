from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.payment import Payment
from app.schemas.payment import PaymentResponse


router = APIRouter()


@router.get("/", response_model=List[PaymentResponse])
def get_payments(subscriber_id: int = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Payment)
    if subscriber_id:
        query = query.filter(Payment.subscriber_id == subscriber_id)
    payments = query.order_by(Payment.created_at.desc()).limit(limit).all()
    return payments