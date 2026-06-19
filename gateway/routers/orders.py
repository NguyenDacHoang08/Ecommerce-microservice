"""
Orders router.

Nginx mapping:
  /api/v1/orders/** → order-service:8003  /orders/**
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.ORDER_SERVICE_URL


@router.api_route(
    "/api/v1/orders/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def orders_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/orders/{path}")


@router.api_route(
    "/api/v1/orders",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def orders_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/orders/")
