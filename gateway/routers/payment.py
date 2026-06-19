"""
Payment router.

Nginx mapping:
  /api/v1/payment/**  → payment-service:8004  /payment/**
  /api/v1/payments/** → payment-service:8004  /payment/**
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.PAYMENT_SERVICE_URL


@router.api_route(
    "/api/v1/payment/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def payment_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/payment/{path}")


@router.api_route(
    "/api/v1/payment",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def payment_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/payment/")


# Alias: /api/v1/payments/** → same upstream
@router.api_route(
    "/api/v1/payments/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def payments_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/payment/{path}")


@router.api_route(
    "/api/v1/payments",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def payments_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/payment/")
