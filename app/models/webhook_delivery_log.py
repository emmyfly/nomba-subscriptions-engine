from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    event_type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    success = Column(Boolean, default=False)
    status_code = Column(Integer, nullable=True)
    error_detail = Column(String, default="")

    created_at = Column(DateTime, default=lambda: datetime.utcnow())
