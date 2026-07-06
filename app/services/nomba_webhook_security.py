import base64
import hashlib
import hmac


def verify_nomba_signature(payload: dict, signature: str, timestamp: str, secret: str) -> bool:
    """Verifies the `nomba-signature` header per Nomba's documented scheme:
    HMAC-SHA256, base64-encoded, over a colon-joined string of specific
    payload fields plus the `nomba-timestamp` header -- NOT over the raw
    request body.
    """
    data = payload.get("data", {})
    merchant = data.get("merchant", {})
    transaction = data.get("transaction", {})

    hashing_payload = ":".join([
        str(payload.get("event_type", "")),
        str(payload.get("requestId", "")),
        str(merchant.get("userId", "")),
        str(merchant.get("walletId", "")),
        str(transaction.get("transactionId", "")),
        str(transaction.get("type", "")),
        str(transaction.get("time", "")),
        str(transaction.get("responseCode", "")),
        str(timestamp),
    ])

    computed = base64.b64encode(
        hmac.new(secret.encode(), hashing_payload.encode(), hashlib.sha256).digest()
    ).decode()

    return hmac.compare_digest(computed, signature or "")
