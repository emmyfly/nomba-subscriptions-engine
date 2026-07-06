from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_real_client_ip(request: Request) -> str:
    """Render (and virtually every PaaS/reverse proxy) sits in front of this
    app, so request.client.host reflects the proxy's own address, not the
    real caller, unless X-Forwarded-For is read explicitly. Reading the
    header directly works regardless of uvicorn's --proxy-headers setting,
    which only affects how Starlette populates request.client itself.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_real_client_ip, default_limits=["100/minute"])
