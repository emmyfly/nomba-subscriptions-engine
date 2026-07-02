from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.payout_log import PayoutLog
from app.schemas.payment import PayoutLogResponse


router = APIRouter()


@router.get("/", response_model=List[PayoutLogResponse])
def get_payout_logs(tenant_id: int = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(PayoutLog)
    if tenant_id:
        query = query.filter(PayoutLog.tenant_id == tenant_id)
    logs = query.order_by(PayoutLog.created_at.desc()).limit(limit).all()
    return logs
