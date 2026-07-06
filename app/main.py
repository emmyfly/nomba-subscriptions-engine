from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
from app.models.plan import Plan
from app.models.subscriber import Subscriber
from app.models.payment import Payment

from app.routers import plans
from app.routers import plans, subscribers, payments, webhooks

from app.models.tenant import Tenant
from app.models.payout_log import PayoutLog
from app.models.webhook_delivery_log import WebhookDeliveryLog
from app.routers import plans, subscribers, payments, webhooks, tenants, payouts, admin, webhook_logs


app = FastAPI(
     title="Nomba subscription Engine",
     description="Managed subscrition on Nomba payment infratsructure",
     version="0.1.0",

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(plans.router, prefix="/api/plans", tags=["Plans"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["Tenants"])

app.include_router(subscribers.router, prefix="/api/subscribers", tags=["Subscribers"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(payouts.router, prefix="/api/payouts", tags=["Payouts"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(webhook_logs.router, prefix="/api/webhook-deliveries", tags=["Webhook Deliveries"])

@app.get("/")
def root():
    return{
        "name":"Nomba Subscrition Engine",
        "status":"running",
        "docs": "Go to /docs to see all endpoints",
    }


