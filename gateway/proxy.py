"""
Shared reverse-proxy helper used by all routers.

Each router calls `proxy_request()` with:
  - request  : the incoming FastAPI/Starlette Request
  - base_url : upstream root (e.g. "http://user-service:8000")
  - upstream_path : the path to forward to on the upstream (e.g. "/api/v1/auth/login/")
"""

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
import config

# One shared async client – reused across requests for connection pooling
_client = httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT)

# Headers we must NOT forward upstream (hop-by-hop)
_HOP_BY_HOP = frozenset(
    [
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",
    ]
)

# Headers we must NOT copy from the upstream response to the client
# (CORS headers are set by our CORSMiddleware instead)
_STRIP_RESPONSE = frozenset(
    [
        "access-control-allow-origin",
        "access-control-allow-methods",
        "access-control-allow-headers",
        "access-control-allow-credentials",
        "access-control-max-age",
        "transfer-encoding",
    ]
)


async def proxy_request(request: Request, base_url: str, upstream_path: str) -> Response:
    """
    Forward *request* to *base_url + upstream_path*, preserving method,
    headers (minus hop-by-hop), query string, and body.
    Returns the upstream response as a FastAPI Response.
    """
    # Build query string
    qs = request.url.query
    url = f"{base_url.rstrip('/')}{upstream_path}"
    if qs:
        url = f"{url}?{qs}"

    # Filter request headers
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    # Inject forwarding metadata
    headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
    headers["X-Forwarded-Proto"] = request.url.scheme
    headers["X-Real-IP"] = request.client.host if request.client else "unknown"

    # Stream body
    body = await request.body()

    upstream_resp = await _client.request(
        method=request.method,
        url=url,
        headers=headers,
        content=body,
    )

    # Filter response headers
    resp_headers = {
        k: v
        for k, v in upstream_resp.headers.items()
        if k.lower() not in _STRIP_RESPONSE
    }

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )
