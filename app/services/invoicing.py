import re


def generate_invoice_number(tenant_name: str, sequence: int) -> str:
    """A friendly, tenant-scoped invoice reference (e.g. 'GYM-0001'), restarting
    per tenant rather than using the global Payment.id -- matches how real
    invoicing systems number transactions per-merchant, for the business's own
    bookkeeping. Payment.id remains the actual unique internal identifier;
    this is purely a human-facing label.
    """
    prefix = re.sub(r"[^A-Za-z]", "", tenant_name).upper()[:3] or "GEN"
    return f"{prefix}-{sequence:04d}"
