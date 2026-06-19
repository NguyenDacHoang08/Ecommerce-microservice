"""
Products & Categories router.

Nginx mapping:
  /api/v1/products/**   → product-service:8001  /api/products/**
  /api/v1/categories/** → product-service:8001  /api/products/categories/**
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.PRODUCT_SERVICE_URL


@router.api_route(
    "/api/v1/products/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def products_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/products/{path}")


@router.api_route(
    "/api/v1/products",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def products_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/api/products/")


@router.api_route(
    "/api/v1/categories/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def categories_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/products/categories/{path}")


@router.api_route(
    "/api/v1/categories",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def categories_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/api/products/categories/")
