import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.dunning import (
    get_subscribers_overdue_for_first_notice,
    get_subscribers_due_for_retry,
    handle_failed_payment,
)

router = APIRouter()
logger = logging.getLogger("subflow.billing")


@router.post("/run-billing-check")
def run_billing_check(token: str, db: Session = Depends(get_db)):
    if not settings.CRON_TOKEN or token != settings.CRON_TOKEN:
        raise HTTPException(status_code=404)

    results = {"first_notices": 0, "retries_escalated": 0, "errors": []}

    for sub in get_subscribers_overdue_for_first_notice(db):
        try:
            logger.info(
                "[BILLING REMINDER] %s (subscriber %s) payment overdue -- "
                "reminder would be sent to %s",
                sub.name, sub.id, sub.email,
            )
            outcome = handle_failed_payment(sub, db)
            logger.info("[DUNNING] %s", outcome)
            results["first_notices"] += 1
        except Exception as e:
            logger.error("Billing check failed for subscriber %s: %s", sub.id, e)
            results["errors"].append({"subscriber_id": sub.id, "error": str(e)})

    for sub in get_subscribers_due_for_retry(db):
        try:
            logger.info(
                "[DUNNING RETRY] %s (subscriber %s) retry %s/%s -- "
                "reminder would be sent to %s",
                sub.name, sub.id, sub.retry_count, sub.max_retries, sub.email,
            )
            outcome = handle_failed_payment(sub, db)
            logger.info("[DUNNING] %s", outcome)
            results["retries_escalated"] += 1
        except Exception as e:
            logger.error("Retry escalation failed for subscriber %s: %s", sub.id, e)
            results["errors"].append({"subscriber_id": sub.id, "error": str(e)})

    db.commit()
    return results
