import json
import secrets
import httpx
from app.core.config import settings

# ── DIAGNOSTIC HELPERS (remove before production) ─────────────────────────────

def _redact(headers: dict) -> dict:
    """Return headers with sensitive values partially redacted for safe logging."""
    out = {}
    for k, v in headers.items():
        if k.lower() == "authorization":
            out[k] = v[:15] + "..." if len(v) > 15 else v
        elif k.lower() in ("client_secret",):
            out[k] = v[:4] + "..." if len(v) > 4 else v
        else:
            out[k] = v
    return out

def _log_req(label: str, method: str, url: str, headers: dict, body: dict) -> None:
    print(f"[NOMBA DIAG] ── {label} ──────────────────────────────────")
    print(f"[NOMBA DIAG]   {method} {url}")
    print(f"[NOMBA DIAG]   Request headers: {json.dumps(_redact(headers), indent=4)}")
    safe_body = {**body}
    if "client_secret" in safe_body:
        safe_body["client_secret"] = safe_body["client_secret"][:4] + "..."
    print(f"[NOMBA DIAG]   Request body:    {json.dumps(safe_body, indent=4)}")

def _log_resp(label: str, response: httpx.Response) -> None:
    print(f"[NOMBA DIAG]   {label} status:  {response.status_code}")
    print(f"[NOMBA DIAG]   {label} headers: {json.dumps(dict(response.headers), indent=4)}")
    print(f"[NOMBA DIAG]   {label} body:    {response.text[:1000]}")
    print(f"[NOMBA DIAG] ────────────────────────────────────────────────────")

# ─────────────────────────────────────────────────────────────────────────────


def get_nomba_token() -> str:
    url = f"{settings.NOMBA_BASE_URL}/v1/auth/token/issue"
    # DIAG: mimic curl's User-Agent to rule out WAF UA-filtering (#hypothesis 2)
    headers = {
        "Content-Type": "application/json",
        "accountId": settings.NOMBA_ACCOUNT_ID,
        "User-Agent": "curl/8.5.0",
    }
    body = {
        "grant_type": "client_credentials",
        "client_id": settings.NOMBA_CLIENT_ID,
        "client_secret": settings.NOMBA_CLIENT_SECRET,
    }

    _log_req("AUTH REQUEST", "POST", url, headers, body)

    # DIAG: follow_redirects=True in case sandbox geo-gates via redirect (#hypothesis 5)
    response = httpx.post(url, json=body, headers=headers, follow_redirects=True)

    _log_resp("AUTH RESPONSE", response)

    if response.status_code != 200:
        raise Exception(
            f"Nomba auth failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    return data["data"]["access_token"]


def create_virtual_account(account_name: str, email: str) -> dict:
    token = get_nomba_token()
    account_ref = f"subflow_{secrets.token_hex(12)}"

    url = f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual"
    # DIAG: mimic curl's User-Agent (#hypothesis 2)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accountId": settings.NOMBA_ACCOUNT_ID,
        "User-Agent": "curl/8.5.0",
    }
    body = {
        "accountRef": account_ref,
        "accountName": account_name,
    }

    _log_req("VIRTUAL ACCOUNT REQUEST", "POST", url, headers, body)

    response = httpx.post(url, json=body, headers=headers, follow_redirects=True)

    _log_resp("VIRTUAL ACCOUNT RESPONSE", response)

    # DIAG: surface Nomba's error body instead of letting raise_for_status() eat it
    if not response.is_success:
        raise Exception(
            f"Nomba virtual account creation failed ({response.status_code}): "
            f"{response.text}"
        )

    data = response.json()
    return {
        "account_id": data["data"]["accountHolderId"],
        "account_number": data["data"]["bankAccountNumber"],
        "bank_name": data["data"]["bankName"],
    }
