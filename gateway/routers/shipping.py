"""
Shipping router.

Nginx mapping:
  /api/v1/shipping/** → shipping-service:8005  /shipping/**
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.SHIPPING_SERVICE_URL


@router.api_route(
    "/api/v1/shipping/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def shipping_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/shipping/{path}")


@router.api_route(
    "/api/v1/shipping",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def shipping_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/shipping/")
