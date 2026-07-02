from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base
from app.models.plan import Plan
from app.models.subscriber import Subscriber
from app.models.payment import Payment

from app.routers import plans
from app.routers import plans, subscribers, payments, webhooks

from app.models.tenant import Tenant
from app.routers import plans, subscribers, payments, webhooks, tenants


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
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

@app.get("/")
def root():
    return{
        "name":"Nomba Subscrition Engine",
        "status":"running",
        "docs": "Go to /docs to see all endpoints",
    }


# TEMP: one-off check for whether Nomba sandbox blocks requests from Render's IP,
# and whether virtual-account creation needs to be scoped to a sub-account.
# Delete this endpoint (and settings.DEBUG_TOKEN / NOMBA_SUBACCOUNT_ID if unused
# elsewhere) once the geo/scoping question is answered.
@app.get("/debug-nomba-geo")
def debug_nomba_geo(token: str):
    import secrets
    import httpx
    from app.core.config import settings

    if not settings.DEBUG_TOKEN or token != settings.DEBUG_TOKEN:
        raise HTTPException(status_code=404)

    result = {}

    auth_resp = httpx.post(
        f"{settings.NOMBA_BASE_URL}/v1/auth/token/issue",
        json={
            "grant_type": "client_credentials",
            "client_id": settings.NOMBA_CLIENT_ID,
            "client_secret": settings.NOMBA_CLIENT_SECRET,
        },
        headers={
            "Content-Type": "application/json",
            "accountId": settings.NOMBA_ACCOUNT_ID,
        },
        timeout=15,
    )
    result["auth"] = {"status": auth_resp.status_code, "body": auth_resp.text[:300]}

    access_token = (
        auth_resp.json().get("data", {}).get("access_token")
        if auth_resp.status_code == 200
        else None
    )

    if not access_token:
        result["virtual_direct"] = {"skipped": "auth did not return a token"}
        result["virtual_subaccount"] = {"skipped": "auth did not return a token"}
        return result

    va_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "accountId": settings.NOMBA_ACCOUNT_ID,
    }

    direct_resp = httpx.post(
        f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual",
        json={"accountRef": f"geotest_direct_{secrets.token_hex(4)}", "accountName": "Geo Test"},
        headers=va_headers,
        timeout=15,
    )
    result["virtual_direct"] = {"status": direct_resp.status_code, "body": direct_resp.text[:300]}

    if settings.NOMBA_SUBACCOUNT_ID:
        sub_resp = httpx.post(
            f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual/{settings.NOMBA_SUBACCOUNT_ID}",
            json={"accountRef": f"geotest_sub_{secrets.token_hex(4)}", "accountName": "Geo Test"},
            headers=va_headers,
            timeout=15,
        )
        result["virtual_subaccount"] = {"status": sub_resp.status_code, "body": sub_resp.text[:300]}
    else:
        result["virtual_subaccount"] = {"skipped": "NOMBA_SUBACCOUNT_ID not set"}

    return result

