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
def calculate_proration(old_price: float, new_price: float, days_remaining: int, total_days: int) -> dict:
    if total_days <= 0:
        return {"credit": 0, "charge": 0, "net": 0}

    daily_old = old_price / total_days
    daily_new = new_price / total_days

    credit = round(daily_old * days_remaining, 2)
    charge = round(daily_new * days_remaining, 2)
    net = round(charge - credit, 2)

    return {
        "credit": credit,
        "charge": charge,
        "net": net,
        "days_remaining": days_remaining,
        "daily_old_rate": round(daily_old, 2),
        "daily_new_rate": round(daily_new, 2),
    }


def get_days_remaining(next_billing_date: datetime, billing_cycle: str) -> tuple:
    now = datetime.now(timezone.utc)

    cycle_total = {
        "weekly": 7,
        "monthly": 30,
        "quarterly": 90,
        "annual": 365,
    }

    total_days = cycle_total.get(billing_cycle, 30)
    remaining = (next_billing_date - now).days
    remaining = max(0, remaining)

    return remaining, total_days