import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    NOMBA_CLIENT_ID:str = os.getenv("NOMBA_CLIENT_ID","")
    NOMBA_CLIENT_SECRET: str = os.getenv("NOMBA_CLIENT_SECRET","")
    NOMBA_ACCOUNT_ID: str = os.getenv("NOMBA_ACCOUNT_ID", "")
    NOMBA_SUBACCOUNT_ID: str = os.getenv("NOMBA_SUBACCOUNT_ID", "")
    NOMBA_BASE_URL: str = os.getenv("NOMBA_BASE_URL","https://sandbox.nomba.com")

    # Signature key configured when setting up the webhook on Nomba's dashboard.
    # If unset, incoming webhooks are processed without signature verification
    # (logged loudly) -- needed since Nomba can't reach this deployment to send
    # a real, signed webhook while the sandbox IP block is unresolved.
    NOMBA_WEBHOOK_SECRET: str = os.getenv("NOMBA_WEBHOOK_SECRET", "")

    # Gates /api/admin/run-billing-check. Called by an external cron, not an in-process
    # scheduler, since Render's free tier can spin the process down between requests.
    CRON_TOKEN: str = os.getenv("CRON_TOKEN", "")

    DATABASE_URL:str = os.getenv("DATABASE_URL","sqlite:///./subscription.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY","dev-secret-change-me")

    PLATFORM_FEE_PERCENT: float = float(os.getenv("PLATFORM_FEE_PERCENT", "3.0"))

settings = Settings()