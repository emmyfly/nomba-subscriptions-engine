import secrets
import httpx
from app.core.config import settings


def get_nomba_token() -> str:
    response = httpx.post(
        f"{settings.NOMBA_BASE_URL}/v1/auth/token/issue",
        json={
            "grant_type": "client_credentials",
            "client_id": settings.NOMBA_CLIENT_ID,
            "client_secret": settings.NOMBA_CLIENT_SECRET,
        },
        headers={
            "Content-Type": "application/json",
            "accountId": settings.NOMBA_ACCOUNT_ID,
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["data"]["access_token"]


def create_virtual_account(account_name: str, email: str) -> dict:
    token = get_nomba_token()
    account_ref = f"subflow_{secrets.token_hex(12)}"

    response = httpx.post(
        f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual",
        json={
            "accountRef": account_ref,
            "accountName": account_name,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "accountId": settings.NOMBA_ACCOUNT_ID,
        },
    )
    response.raise_for_status()
    data = response.json()

    return {
        "account_id": data["data"]["accountHolderId"],
        "account_number": data["data"]["bankAccountNumber"],
        "bank_name": data["data"]["bankName"],
    }