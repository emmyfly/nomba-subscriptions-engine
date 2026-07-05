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
        plan = db.query(Plan).filter(Plan.id == subscriber.plan_id).first()
        subscriber.accumulated_balance += amount

        # Deposits don't have to cover a full cycle in one go -- they accumulate
        # (Save-to-Subscribe) until there's enough to cover subscriber.amount,
        # at which point the cycle completes and any overflow carries forward.
        cycle_messages = []
        while (
            plan
            and subscriber.amount > 0
            and subscriber.accumulated_balance >= subscriber.amount
        ):
            subscriber.accumulated_balance -= subscriber.amount
            cycle_messages.append(handle_successful_payment(subscriber, db))
            if subscriber.next_billing_date:
                subscriber.next_billing_date = advance_billing_date(
                    current_date=subscriber.next_billing_date,
                    billing_cycle=plan.billing_cycle,
                )

        if cycle_messages:
            result = "; ".join(cycle_messages)
        else:
            still_owed = round(subscriber.amount - subscriber.accumulated_balance, 2)
            result = (
                f"{subscriber.name} deposited {amount}: "
                f"{subscriber.accumulated_balance:.2f} saved toward {subscriber.amount:.2f} "
                f"({still_owed:.2f} still needed)"
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