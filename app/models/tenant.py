from datetime import datetime
from sqlalchemy import Column, Integer, String,Boolean, DateTime
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    api_key = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    nomba_subaccount_id = Column(String, default="")

    contact_full_name = Column(String, default="")
    identity_match_status = Column(String, default="not_checked")

    bank_account_number = Column(String, default="")
    bank_code = Column(String, default="")
    bank_account_name = Column(String, default="")
    bank_verification_status = Column(String, default="unverified")

    webhook_url = Column(String, default="")
    webhook_secret = Column(String, default="")

    created_at = Column(DateTime, default=lambda: datetime.utcnow())