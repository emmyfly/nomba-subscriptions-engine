from sqlalchemy.orm import Session
from app.models.subscriber import Subscriber
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.services.billing import advance_billing_date
from app.services.dunning import handle_failed_payment, handle_successful_payment
from app.services.payout import process_instant_payout
from app.services.outbound_webhook import send_tenant_webhook
from app.services.invoicing import generate_invoice_number


def process_payment_webhook(payload: dict, db: Session) -> str:
    event_type = payload.get("event_type", "unknown")
    data = payload.get("data", {})

    transaction = data.get("transaction", {})

    # Nomba's real webhook payload puts the virtual account that received the
    # transfer at data.transaction.aliasAccountNumber, and the session at
    # data.transaction.sessionId -- there is no top-level accountNumber or
    # order object, despite what earlier code (and manually-crafted test
    # payloads all session) assumed.
    account_number = transaction.get("aliasAccountNumber", "")
    amount = transaction.get("transactionAmount", 0)
    transaction_ref = transaction.get("transactionId", "")
    session_id = transaction.get("sessionId", "")
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

    tenant = db.query(Tenant).filter(Tenant.id == subscriber.tenant_id).first()

    prior_payments = db.query(Payment).filter(Payment.tenant_id == subscriber.tenant_id).count()
    invoice_number = generate_invoice_number(
        tenant.name if tenant else "GEN", prior_payments + 1
    )

    payment = Payment(
        subscriber_id=subscriber.id,
        tenant_id=subscriber.tenant_id,
        amount=amount,
        status="success" if event_type == "payment_success" else "failed",
        event_type=event_type,
        nomba_transaction_ref=transaction_ref,
        nomba_session_id=session_id,
        invoice_number=invoice_number,
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
        if tenant:
            process_instant_payout(payment, tenant, db)
            send_tenant_webhook(tenant, "subscription.payment_succeeded", {
                "subscriber_id": subscriber.id,
                "subscriber_name": subscriber.name,
                "amount": amount,
                "status": subscriber.status,
                "accumulated_balance": subscriber.accumulated_balance,
                "next_billing_date": subscriber.next_billing_date,
            }, db)
    elif event_type == "payment_failed":
        result = handle_failed_payment(subscriber, db)
        if tenant:
            send_tenant_webhook(tenant, "subscription.payment_failed", {
                "subscriber_id": subscriber.id,
                "subscriber_name": subscriber.name,
                "status": subscriber.status,
                "retry_count": subscriber.retry_count,
            }, db)
    else:
        result = f"Unknown event type: {event_type}"

    db.commit()
    return result