"""Auth & User-service router — /api/v1/auth/**"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.USER_SERVICE_URL


@router.api_route(
    "/api/v1/auth/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def auth_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/v1/auth/{path}")
