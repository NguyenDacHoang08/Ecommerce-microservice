"""
AI Service router.

Proxies:
  /api/v1/recommend/** → ai-service:8006  /api/v1/recommend/**
  /api/v1/chatbot/**   → ai-service:8006  /api/v1/chatbot/**
  /api/v1/admin/**     → ai-service:8006  /api/v1/admin/**
"""

from fastapi import APIRouter, Request
from fastapi.responses import Response
from proxy import proxy_request
import config

router = APIRouter()
_BASE = config.AI_SERVICE_URL


@router.api_route(
    "/api/v1/recommend/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def recommend_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/v1/recommend/{path}")


@router.api_route(
    "/api/v1/chatbot/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def chatbot_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/v1/chatbot/{path}")


@router.api_route(
    "/api/v1/chatbot",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def chatbot_root_proxy(request: Request) -> Response:
    return await proxy_request(request, _BASE, "/api/v1/chatbot")


@router.api_route(
    "/api/v1/admin/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def admin_proxy(path: str, request: Request) -> Response:
    return await proxy_request(request, _BASE, f"/api/v1/admin/{path}")
