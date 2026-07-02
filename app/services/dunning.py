from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.subscriber import Subscriber
from app.models.plan import Plan


RETRY_INTERVALS = {
    1: timedelta(days=1),
    2: timedelta(days=3),
    3: timedelta(days=7),
}


def handle_failed_payment(subscriber: Subscriber, db: Session) -> str:
    subscriber.retry_count += 1
    subscriber.last_retry_at = datetime.utcnow()

    if subscriber.retry_count >= subscriber.max_retries:
        subscriber.status = "suspended"
        return f"{subscriber.name} suspended after {subscriber.max_retries} failed attempts"
    else:
        subscriber.status = "past_due"
        next_retry = RETRY_INTERVALS.get(subscriber.retry_count, timedelta(days=7))
        return f"{subscriber.name} marked past_due. Retry {subscriber.retry_count}/{subscriber.max_retries} in {next_retry.days} days"


def handle_successful_payment(subscriber: Subscriber, db: Session) -> str:
    old_status = subscriber.status
    subscriber.status = "active"
    subscriber.retry_count = 0
    subscriber.last_retry_at = None

    if old_status == "suspended":
        return f"{subscriber.name} reactivated from suspended"
    elif old_status == "past_due":
        return f"{subscriber.name} recovered from past_due"
    else:
        return f"{subscriber.name} payment confirmed"


def get_subscribers_due_for_retry(db: Session) -> list:
    now = datetime.utcnow()

    past_due = db.query(Subscriber).filter(
        Subscriber.status == "past_due",
        Subscriber.retry_count < Subscriber.max_retries,
    ).all()

    due_for_retry = []
    for sub in past_due:
        if sub.last_retry_at is None:
            due_for_retry.append(sub)
            continue

        interval = RETRY_INTERVALS.get(sub.retry_count, timedelta(days=7))
        if now >= sub.last_retry_at + interval:
            due_for_retry.append(sub)

    return due_for_retry