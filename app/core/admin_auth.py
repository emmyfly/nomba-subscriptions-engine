from fastapi import Header, HTTPException

from app.core.config import settings


def require_admin_token(x_admin_token: str = Header(default="")) -> None:
    """Gates dashboard-only read endpoints (tenant list, subscribers, payments,
    payouts, webhook deliveries). Inactive until ADMIN_TOKEN is configured, so
    shipping this code can never break anything on its own -- only setting the
    env var on Render activates enforcement.
    """
    if not settings.ADMIN_TOKEN:
        return
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Missing or invalid admin token")


def authorize_tenant_write(tenant, x_admin_token: str, authorization: str) -> None:
    """Allows either the admin token, or the tenant's own API key as a Bearer
    token, to modify a specific tenant. Without this, any caller could edit
    any tenant's bank/payout details just by guessing a numeric ID -- this is
    what the signup page's bank-details step authenticates with, using the
    api_key it just received from tenant creation.
    """
    if not settings.ADMIN_TOKEN:
        return  # not yet activated -- matches prior (unauthenticated) behavior

    if x_admin_token and x_admin_token == settings.ADMIN_TOKEN:
        return

    if authorization and authorization.removeprefix("Bearer ").strip() == tenant.api_key:
        return

    raise HTTPException(status_code=403, detail="Not authorized to modify this tenant")
