import os
from dotenv import load_dotenv

load_dotenv()

# ── Upstream service URLs ─────────────────────────────────────────────
USER_SERVICE_URL     = os.getenv("USER_SERVICE_URL",     "http://user-service:8000")
PRODUCT_SERVICE_URL  = os.getenv("PRODUCT_SERVICE_URL",  "http://product-service:8001")
CART_SERVICE_URL     = os.getenv("CART_SERVICE_URL",     "http://cart-service:8002")
ORDER_SERVICE_URL    = os.getenv("ORDER_SERVICE_URL",    "http://order-service:8003")
PAYMENT_SERVICE_URL  = os.getenv("PAYMENT_SERVICE_URL",  "http://payment-service:8004")
SHIPPING_SERVICE_URL = os.getenv("SHIPPING_SERVICE_URL", "http://shipping-service:8005")
AI_SERVICE_URL       = os.getenv("AI_SERVICE_URL",       "http://ai-service:8006")
FRONTEND_URL         = os.getenv("FRONTEND_URL",         "http://frontend:3000")

# ── CORS ──────────────────────────────────────────────────────────────
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost,http://127.0.0.1:3000,http://127.0.0.1",
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ── Gateway settings ──────────────────────────────────────────────────
GATEWAY_PORT    = int(os.getenv("GATEWAY_PORT", "8080"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))   # seconds
