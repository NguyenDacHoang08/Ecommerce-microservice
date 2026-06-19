"""Internal service router — /api/v1/internal/**"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.USER_SERVICE_URL


@router.api_route(
    "/api/v1/internal/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def internal_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/v1/internal/{path}")
