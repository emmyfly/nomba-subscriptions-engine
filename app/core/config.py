import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    NOMBA_CLIENT_ID:str = os.getenv("NOMBA_CLIENT_ID","")
    NOMBA_CLIENT_SECRET: str = os.getenv("NOMBA_CLIENT_SECRET","")
    NOMBA_ACCOUNT_ID: str = os.getenv("NOMBA_ACCOUNT_ID", "")
    NOMBA_SUBACCOUNT_ID: str = os.getenv("NOMBA_SUBACCOUNT_ID", "")
    NOMBA_BASE_URL: str = os.getenv("NOMBA_BASE_URL","https://sandbox.nomba.com")

    # TEMP: gates /debug-nomba-geo. Remove alongside that endpoint once the geo test is done.
    DEBUG_TOKEN: str = os.getenv("DEBUG_TOKEN", "")

    DATABASE_URL:str = os.getenv("DATABASE_URL","sqlite:///./subscription.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY","dev-secret-change-me")

    PLATFORM_FEE_PERCENT: float = float(os.getenv("PLATFORM_FEE_PERCENT", "3.0"))

settings = Settings()