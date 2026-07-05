from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.core.database import Base


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, default="")

    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    status = Column(String, default="active")

    nomba_virtual_account_id = Column(String, default="")
    nomba_account_number = Column(String, default="")
    nomba_bank_name = Column(String, default="")

    amount = Column(Float, default=0.0)
    accumulated_balance = Column(Float, default=0.0)
    next_billing_date = Column(DateTime, nullable=True)

    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(),
                        onupdate=lambda: datetime.utcnow())