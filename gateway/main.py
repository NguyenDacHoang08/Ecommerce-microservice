"""
API Gateway — FastAPI-based reverse proxy replacing Nginx.

Routing table (mirrors nginx.conf):
  /health                   → health check (gateway itself)
  /api/v1/auth/**           → user-service:8000
  /api/v1/users/**          → user-service:8000
  /api/v1/internal/**       → user-service:8000
  /api/v1/products/**       → product-service:8001  (path: /api/products/**)
  /api/v1/categories/**     → product-service:8001  (path: /api/products/categories/**)
  /api/v1/cart/**           → cart-service:8002     (path: /cart/**)
  /api/v1/orders/**         → order-service:8003    (path: /orders/**)
  /api/v1/payment/**        → payment-service:8004  (path: /payment/**)
  /api/v1/payments/**       → payment-service:8004  (path: /payment/**)
  /api/v1/shipping/**       → shipping-service:8005 (path: /shipping/**)
  /**                       → frontend:3000 (React SPA catch-all)
"""

import logging
import sys

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from middleware.logging import LoggingMiddleware
from routers import auth, users, internal, products, cart, orders, payment, shipping, ai, frontend

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("api_gateway")


# ── Lifespan: manage shared httpx client ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Gateway starting up…")
    logger.info("Allowed CORS origins: %s", config.ALLOWED_ORIGINS)
    yield
    # Close shared httpx client on shutdown
    import proxy
    await proxy._client.aclose()
    logger.info("API Gateway shut down.")


# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="E-Commerce API Gateway",
    description="Custom FastAPI reverse proxy — routes requests to microservices",
    version="1.0.0",
    lifespan=lifespan,
    # Hide docs in production by setting docs_url=None
    docs_url="/gateway/docs",
    redoc_url="/gateway/redoc",
    openapi_url="/gateway/openapi.json",
)

# ── Middlewares (order matters: outermost first) ──────────────────────

# 1. Logging (wrap everything)
app.add_middleware(LoggingMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check ──────────────────────────────────────────────────────
@app.get("/health", tags=["Gateway"])
async def health():
    return {"status": "ok", "service": "api-gateway"}


# ── Routers — specific API routes BEFORE the catch-all ───────────────
app.include_router(auth.router,     tags=["Auth"])
app.include_router(users.router,    tags=["Users"])
app.include_router(internal.router, tags=["Internal"])
app.include_router(products.router, tags=["Products"])
app.include_router(cart.router,     tags=["Cart"])
app.include_router(orders.router,   tags=["Orders"])
app.include_router(payment.router,  tags=["Payment"])
app.include_router(shipping.router, tags=["Shipping"])
app.include_router(ai.router,       tags=["AI Service"])

from fastapi import Request
from fastapi.responses import Response

@app.api_route(
    "/media/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    tags=["Media"]
)
async def media_proxy(path: str, request: Request) -> Response:
    import proxy
    return await proxy.proxy_request(request, config.PRODUCT_SERVICE_URL, f"/media/{path}")

# ── Frontend catch-all MUST be last ──────────────────────────────────
app.include_router(frontend.router, tags=["Frontend"])
