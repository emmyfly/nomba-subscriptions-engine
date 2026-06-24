from sqlalchemy.orm import Session
from app.models.subscriber import Subscriber
from app.models.payment import Payment
from app.models.plan import Plan
from app.services.billing import advance_billing_date
from app.services.dunning import handle_failed_payment, handle_successful_payment


def process_payment_webhook(payload: dict, db: Session) -> str:
    event_type = payload.get("event", "unknown")
    data = payload.get("data", {})

    account_number = data.get("accountNumber", "")
    amount = data.get("amount", 0)
    transaction_ref = data.get("transactionReference", "")
    session_id = data.get("sessionId", "")

    subscriber = db.query(Subscriber).filter(
        Subscriber.nomba_account_number == account_number
    ).first()

    if not subscriber:
        return f"No subscriber found for account {account_number}"

    payment = Payment(
        subscriber_id=subscriber.id,
        tenant_id=subscriber.tenant_id,
        amount=amount,
        status="success" if event_type == "payment_success" else "failed",
        event_type=event_type,
        nomba_transaction_ref=transaction_ref,
        nomba_session_id=session_id,
    )
    db.add(payment)

    if event_type == "payment_success":
        result = handle_successful_payment(subscriber, db)
        plan = db.query(Plan).filter(Plan.id == subscriber.plan_id).first()
        if plan and subscriber.next_billing_date:
            subscriber.next_billing_date = advance_billing_date(
                current_date=subscriber.next_billing_date,
                billing_cycle=plan.billing_cycle,
            )
    elif event_type == "payment_failed":
        result = handle_failed_payment(subscriber, db)
    else:
        result = f"Unknown event type: {event_type}"

    db.commit()
    return result