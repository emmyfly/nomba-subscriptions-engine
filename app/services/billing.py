from datetime import datetime, timezone, timedelta


def calculate_next_billing_date(billing_cycle: str) -> datetime:
    now = datetime.now(timezone.utc)

    cycle_days = {
        "weekly": timedelta(weeks=1),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "annual": timedelta(days=365),
    }

    delta = cycle_days.get(billing_cycle)
    if delta is None:
        raise ValueError(f"Unknown billing cycle: {billing_cycle}")

    return now + delta


def is_payment_overdue(next_billing_date: datetime) -> bool:
    if next_billing_date is None:
        return False
    now = datetime.now(timezone.utc)
    return now > next_billing_date


def advance_billing_date(current_date: datetime, billing_cycle: str) -> datetime:
    cycle_days = {
        "weekly": timedelta(weeks=1),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "annual": timedelta(days=365),
    }

    delta = cycle_days.get(billing_cycle)
    if delta is None:
        raise ValueError(f"Unknown billing cycle: {billing_cycle}")

    return current_date + delta