from fastapi import FastAPI
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

@app.get("/debug-env")
def debug_env():
    from app.core.config import settings
    return {
        "client_id_repr": repr(settings.NOMBA_CLIENT_ID),
        "client_id_len": len(settings.NOMBA_CLIENT_ID),
        "secret_repr": repr(settings.NOMBA_CLIENT_SECRET),
        "secret_len": len(settings.NOMBA_CLIENT_SECRET),
        "account_id_repr": repr(settings.NOMBA_ACCOUNT_ID),
        "account_id_len": len(settings.NOMBA_ACCOUNT_ID),
        "base_url": settings.NOMBA_BASE_URL,
    }


# DIAG: step-by-step Nomba connectivity probe — remove before production
@app.get("/debug-nomba")
def debug_nomba():
    """
    Tests each Nomba API step independently and returns full diagnostic data.
    Also reveals the outbound IP Render is using (via ipinfo.io).
    Check Render logs for the [NOMBA DIAG] lines after hitting this endpoint.
    """
    import httpx
    from app.core.config import settings

    result = {}

    # Step 0: discover outbound IP (confirms geo/IP hypothesis)
    try:
        ip_resp = httpx.get("https://ipinfo.io/json", timeout=5)
        result["outbound_ip_info"] = ip_resp.json()
    except Exception as e:
        result["outbound_ip_info"] = {"error": str(e)}

    # Step 1: test auth only
    try:
        url = f"{settings.NOMBA_BASE_URL}/v1/auth/token/issue"
        headers = {
            "Content-Type": "application/json",
            "accountId": settings.NOMBA_ACCOUNT_ID,
            "User-Agent": "curl/8.5.0",
        }
        body = {
            "grant_type": "client_credentials",
            "client_id": settings.NOMBA_CLIENT_ID,
            "client_secret": settings.NOMBA_CLIENT_SECRET,
        }
        auth_resp = httpx.post(url, json=body, headers=headers, follow_redirects=True, timeout=10)
        result["auth_step"] = {
            "status": auth_resp.status_code,
            "response_headers": dict(auth_resp.headers),
            "body": auth_resp.text[:500],
            "success": auth_resp.status_code == 200,
        }
        token = auth_resp.json().get("data", {}).get("access_token") if auth_resp.status_code == 200 else None
    except Exception as e:
        result["auth_step"] = {"error": str(e)}
        token = None

    # Step 2: test virtual account creation (only if auth worked)
    if token:
        import secrets as _secrets
        try:
            url2 = f"{settings.NOMBA_BASE_URL}/v1/accounts/virtual"
            headers2 = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "accountId": settings.NOMBA_ACCOUNT_ID,
                "User-Agent": "curl/8.5.0",
            }
            body2 = {
                "accountRef": f"diagtest_{_secrets.token_hex(6)}",
                "accountName": "Diagnostic Test Account",
            }
            va_resp = httpx.post(url2, json=body2, headers=headers2, follow_redirects=True, timeout=10)
            result["virtual_account_step"] = {
                "status": va_resp.status_code,
                "response_headers": dict(va_resp.headers),
                "body": va_resp.text[:500],
                "success": va_resp.is_success,
            }
        except Exception as e:
            result["virtual_account_step"] = {"error": str(e)}
    else:
        result["virtual_account_step"] = {"skipped": "auth step did not produce a token"}

    return result
