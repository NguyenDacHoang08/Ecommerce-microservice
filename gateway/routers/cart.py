"""
Cart router.

Nginx mapping:
  /api/v1/cart/** → cart-service:8002  /cart/**
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.CART_SERVICE_URL


@router.api_route(
    "/api/v1/cart/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def cart_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/cart/{path}")


@router.api_route(
    "/api/v1/cart",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def cart_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/cart/")
