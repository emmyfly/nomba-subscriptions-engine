from sqlalchemy.orm import Session
from app.models.subscriber import Subscriber
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.services.billing import advance_billing_date
from app.services.dunning import handle_failed_payment, handle_successful_payment
from app.services.payout import process_instant_payout


def process_payment_webhook(payload: dict, db: Session) -> str:
    event_type = payload.get("event_type", "unknown")
    data = payload.get("data", {})

    transaction = data.get("transaction", {})
    order = data.get("order", {})

    account_number = data.get("accountNumber", "")
    amount = transaction.get("transactionAmount", 0)
    transaction_ref = transaction.get("transactionId", "")
    session_id = order.get("orderReference", "")
    subscriber = db.query(Subscriber).filter(
        Subscriber.nomba_account_number == account_number
    ).first()

    if not subscriber:
        return f"No subscriber found for account {account_number}"

    if transaction_ref:
        existing = db.query(Payment).filter(
            Payment.nomba_transaction_ref == transaction_ref
        ).first()
        if existing:
            return f"Duplicate webhook ignored (transaction {transaction_ref} already processed)"

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

        db.flush()  # assigns payment.id, needed before logging the payout against it
        tenant = db.query(Tenant).filter(Tenant.id == subscriber.tenant_id).first()
        if tenant:
            process_instant_payout(payment, tenant, db)
    elif event_type == "payment_failed":
        result = handle_failed_payment(subscriber, db)
    else:
        result = f"Unknown event type: {event_type}"

    db.commit()
    return result