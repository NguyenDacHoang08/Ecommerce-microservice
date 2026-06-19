"""
AI Service — FastAPI Application Entry Point

Engines:
    ├── LSTM Recommendation (PyTorch)
    ├── Neo4j Knowledge Graph
    ├── RAG Chatbot (FAISS + SentenceTransformers)
    └── Hybrid Recommendation Engine

Startup sequence:
    1. Connect to PostgreSQL → create tables
    2. Connect to Neo4j
    3. Load LSTM model
    4. Load FAISS index
"""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api import chatbot, recommendation

settings = get_settings()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all resources on startup, clean up on shutdown."""
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION} — Starting up")
    logger.info("=" * 60)

    # ── PostgreSQL ────────────────────────────────────────────
    try:
        from app.database.postgres import init_db
        await init_db()
        logger.info("✓ PostgreSQL connected — tables created")
    except Exception as exc:
        logger.error(f"✗ PostgreSQL init failed: {exc}")

    # ── Neo4j ─────────────────────────────────────────────────
    try:
        from app.database.neo4j_db import get_driver
        driver = await get_driver()
        await driver.verify_connectivity()
        logger.info("✓ Neo4j connected")
    except Exception as exc:
        logger.warning(f"⚠ Neo4j not available (will retry on use): {exc}")

    # ── LSTM model ────────────────────────────────────────────
    try:
        from app.services.lstm_service import lstm_service
        lstm_service.load_model()
        status = "✓ loaded" if lstm_service.is_loaded else "⚠ not found (train first)"
        logger.info(f"LSTM model — {status}")
    except Exception as exc:
        logger.warning(f"⚠ LSTM load failed: {exc}")

    # ── RAG / FAISS ───────────────────────────────────────────
    try:
        from app.services.rag_service import rag_service
        rag_service.load()
        if not rag_service.is_loaded:
            logger.info("FAISS index not found — building with sample data...")
            await rag_service.build_index()
        status = "✓ loaded" if rag_service.is_loaded else "⚠ failed"
        logger.info(f"RAG / FAISS — {status}")
    except Exception as exc:
        logger.warning(f"⚠ RAG load failed: {exc}")

    logger.info("=" * 60)
    logger.info("  AI Service is ready")
    logger.info("=" * 60)

    yield  # ← application runs here

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("Shutting down AI Service...")
    try:
        from app.database.postgres import close_db
        await close_db()
    except Exception:
        pass
    try:
        from app.database.neo4j_db import close_driver
        await close_driver()
    except Exception:
        pass
    logger.info("AI Service stopped.")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🤖 AI Service — Ecommerce Intelligence Engine

A standalone AI microservice powering personalized product recommendations
and an AI chatbot for the ecommerce platform.

### Engines
| Engine | Technology | Purpose |
|--------|-----------|---------|
| **LSTM** | PyTorch | Next-product sequence prediction |
| **Neo4j Graph** | Knowledge Graph | Collaborative filtering |
| **RAG** | FAISS + SentenceTransformers | Semantic search & chatbot |
| **Hybrid** | Score Fusion | Combined recommendations |

### Key Endpoints
- `GET /recommend/{user_id}` — Personalized product recommendations
- `POST /chatbot` — AI product assistant
- `POST /chatbot/search` — Semantic product search
- `POST /admin/train-lstm` — Trigger LSTM training
- `POST /admin/build-index` — Rebuild FAISS index
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(recommendation.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")


# ── Admin router ──────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@admin_router.post("/train-lstm", summary="Trigger LSTM model training")
async def train_lstm() -> dict:
    """
    Trains the LSTM model on user_behavior data from PostgreSQL.
    Runs as a background subprocess. Returns when training completes.
    """
    from app.services.lstm_service import lstm_service
    result = await lstm_service.train()
    return result


@admin_router.post("/build-index", summary="Rebuild FAISS vector index")
async def build_index() -> dict:
    """
    Fetches products from product-service and rebuilds the FAISS index.
    Also reloads the RAG service after building.
    """
    from app.services.rag_service import rag_service
    result = await rag_service.build_index()
    return result


@admin_router.post("/sync-behavior", summary="Sync behavior to Neo4j")
async def sync_behavior(user_id: int, product_id: int, action_type: str) -> dict:
    """Manually sync a user behavior event to the Neo4j knowledge graph."""
    from app.services.graph_service import graph_service
    await graph_service.sync_behavior(user_id, product_id, action_type)
    return {"status": "synced", "user_id": user_id, "product_id": product_id}


@admin_router.post("/import-graph-csv", summary="Import behavior data from CSV to Neo4j")
async def import_graph_csv(csv_path: str = "/app/data/user_behavior.csv") -> dict:
    """Import user behaviors from a CSV file into the Neo4j Knowledge Graph."""
    from app.services.graph_service import graph_service
    result = await graph_service.import_from_csv(csv_path)
    return result


@admin_router.get("/graph-stats", summary="Neo4j graph statistics")
async def graph_stats() -> dict:
    """Return node and relationship counts in the Neo4j graph."""
    from app.services.graph_service import graph_service
    return await graph_service.get_stats()


app.include_router(admin_router)


# ── Health & Root ─────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"], summary="Service health check")
async def health() -> dict:
    """Returns the health status of all AI engines."""
    from app.services.lstm_service import lstm_service
    from app.services.rag_service import rag_service

    neo4j_ok = False
    try:
        from app.database.neo4j_db import get_driver
        driver = await get_driver()
        await driver.verify_connectivity()
        neo4j_ok = True
    except Exception:
        pass

    return JSONResponse(
        content={
            "status": "healthy",
            "version": settings.APP_VERSION,
            "engines": {
                "lstm": lstm_service.is_loaded,
                "neo4j": neo4j_ok,
                "rag": rag_service.is_loaded,
                "hybrid": lstm_service.is_loaded or rag_service.is_loaded,
            },
        }
    )
