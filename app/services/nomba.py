import secrets
import httpx
from app.core.config import settings


def get_nomba_token() -> str:
    url = f"{settings.NOMBA_BASE_URL}/v1/auth/token/issue"
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

    response = httpx.post(url, json=body, headers=headers, follow_redirects=True, timeout=30.0)

    if response.status_code != 200:
        raise Exception(
            f"Nomba auth failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    return data["data"]["access_token"]


def create_virtual_account(account_name: str, email: str, subaccount_id: str = "") -> dict:
    token = get_nomba_token()
    account_ref = f"subflow_{secrets.token_hex(12)}"

    subaccount_id = subaccount_id or settings.NOMBA_SUBACCOUNT_ID
    url = (
        f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual/{subaccount_id}"
        if subaccount_id
        else f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual"
    )
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

    response = httpx.post(url, json=body, headers=headers, follow_redirects=True, timeout=30.0)

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


def transfer_to_bank(
    subaccount_id: str,
    amount: float,
    account_number: str,
    account_name: str,
    bank_code: str,
    merchant_tx_ref: str,
) -> dict:
    token = get_nomba_token()

    subaccount_id = subaccount_id or settings.NOMBA_SUBACCOUNT_ID
    url = f"{settings.NOMBA_BASE_URL}/v2/transfers/bank/{subaccount_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accountId": settings.NOMBA_ACCOUNT_ID,
        "User-Agent": "curl/8.5.0",
    }
    body = {
        "amount": amount,
        "accountNumber": account_number,
        "accountName": account_name,
        "bankCode": bank_code,
        "merchantTxRef": merchant_tx_ref,
    }

    response = httpx.post(url, json=body, headers=headers, follow_redirects=True, timeout=30.0)

    if not response.is_success:
        raise Exception(
            f"Nomba bank transfer failed ({response.status_code}): {response.text}"
        )

    return response.json()
