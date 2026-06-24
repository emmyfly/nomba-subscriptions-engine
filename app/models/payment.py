from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)

    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    event_type = Column(String, default="")

    nomba_transaction_ref = Column(String, default="")
    nomba_session_id = Column(String, default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))