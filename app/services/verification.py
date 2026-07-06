import re
import logging
from app.models.tenant import Tenant
from app.services.nomba import lookup_bank_account

logger = logging.getLogger("subflow.verification")

_NOISE_WORDS = {"LTD", "LIMITED", "PLC", "NIGERIA", "NIG", "ENTERPRISES", "COMPANY", "CO", "INC", "GROUP"}


def _significant_words(name: str) -> set:
    cleaned = re.sub(r"[^A-Z0-9 ]", "", name.upper())
    return set(cleaned.split()) - _NOISE_WORDS


def names_reasonably_match(claimed_name: str, actual_name: str) -> bool:
    """Loose match on significant words -- 'GymFlex Ltd' vs 'GYMFLEX NIG LIMITED'
    should count as the same business, so this isn't an exact string comparison."""
    claimed_words = _significant_words(claimed_name)
    actual_words = _significant_words(actual_name)
    if not claimed_words or not actual_words:
        return False
    overlap = claimed_words & actual_words
    return len(overlap) / min(len(claimed_words), len(actual_words)) >= 0.5


def verify_tenant_bank_account(tenant: Tenant) -> str:
    """
    Confirms the tenant's claimed bank_account_name matches Nomba's own record
    for that account number, to catch typos or impersonation before payouts
    start flowing automatically.

    Returns the new status; does not commit -- caller owns the transaction.

    A failed lookup (e.g. the Nomba sandbox geo-block) is deliberately NOT
    treated the same as a confirmed mismatch -- it just means "unknown," so
    it doesn't block payouts the way a real name mismatch does.
    """
    try:
        actual_name = lookup_bank_account(tenant.bank_account_number, tenant.bank_code)
    except Exception as e:
        logger.warning("Bank lookup failed for tenant %s: %s", tenant.id, e)
        return "lookup_failed"

    if names_reasonably_match(tenant.bank_account_name, actual_name):
        return "verified"

    logger.warning(
        "Bank name mismatch for tenant %s: claimed=%r actual=%r",
        tenant.id, tenant.bank_account_name, actual_name,
    )
    return "name_mismatch"
