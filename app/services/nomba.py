import random
import httpx
from app.core.config import settings


def get_nomba_token() -> str:
    return "mock_access_token_replace_me"


def create_virtual_account(account_name: str, email: str) -> dict:
    mock_account_number = "".join([str(random.randint(0, 9)) for _ in range(10)])
    return {
        "account_id": f"mock_va_{mock_account_number}",
        "account_number": mock_account_number,
        "bank_name": "Wema Bank (Sandbox)",
    }