from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.core.database import Base


class PayoutLog(Base):
    __tablename__ = "payout_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)

    gross_amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)

    status = Column(String, nullable=False)
    nomba_transfer_ref = Column(String, default="")
    error_detail = Column(String, default="")

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
