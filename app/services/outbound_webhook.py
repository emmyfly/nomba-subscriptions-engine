import hashlib
import hmac
import json
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.webhook_delivery_log import WebhookDeliveryLog

logger = logging.getLogger("subflow.outbound_webhook")


def send_tenant_webhook(tenant: Tenant, event_type: str, data: dict, db: Session) -> Optional[WebhookDeliveryLog]:
    """Notifies a tenant's own software of an event (e.g. a subscriber's payment
    succeeded), mirroring the same pattern Nomba uses to notify SubFlow.

    Signed with HMAC-SHA256 (X-SubFlow-Signature header) if the tenant has a
    webhook_secret set, so they can verify the request actually came from
    SubFlow. A delivery failure never raises -- it's logged and the caller's
    transaction proceeds regardless, since a tenant's downed server shouldn't
    block SubFlow's own payment processing.
    """
    if not tenant.webhook_url:
        return None

    body = json.dumps({"event_type": event_type, "data": data}, default=str)

    headers = {"Content-Type": "application/json"}
    if tenant.webhook_secret:
        signature = hmac.new(
            tenant.webhook_secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()
        headers["X-SubFlow-Signature"] = signature

    log = WebhookDeliveryLog(tenant_id=tenant.id, event_type=event_type, url=tenant.webhook_url)

    try:
        response = httpx.post(tenant.webhook_url, content=body, headers=headers, timeout=10.0)
        log.status_code = response.status_code
        log.success = response.is_success
        if not response.is_success:
            log.error_detail = response.text[:300]
        logger.info(
            "Outbound webhook to tenant %s (%s): HTTP %s",
            tenant.id, event_type, response.status_code,
        )
    except Exception as e:
        log.success = False
        log.error_detail = str(e)[:300]
        logger.warning(
            "Outbound webhook to tenant %s (%s) failed: %s", tenant.id, event_type, e
        )

    db.add(log)
    return log
