"""
Recommendation API — GET /recommend/{user_id}

Flow:
    1. Fetch user behavior history from PostgreSQL
    2. LSTM → predict next products
    3. Neo4j → graph-based recommendations
    4. RAG → semantic scoring
    5. Hybrid score fusion → top-5 results
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.models.behavior import ActionType, UserBehavior
from app.services.hybrid_service import hybrid_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommend", tags=["Recommendation"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductScore(BaseModel):
    product_id: str
    name: str
    score: float
    price: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    quantity: Optional[int] = None
    source: Optional[str] = None
    lstm_score: Optional[float] = None
    graph_score: Optional[float] = None
    rag_score: Optional[float] = None


class BehaviorIn(BaseModel):
    user_id: str
    product_id: str
    action_type: ActionType


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/{user_id}",
    response_model=list[ProductScore],
    summary="Get hybrid recommendations for a user",
    description="""
    Returns top-N product recommendations using hybrid engine:
    - **LSTM** (40%): Sequence-based next-product prediction
    - **Neo4j Graph** (30%): Collaborative filtering via knowledge graph
    - **RAG** (30%): Semantic similarity scoring

    Results are sorted by final hybrid score (descending).
    """,
)
async def get_recommendations(
    user_id: str,
    limit: int = Query(default=5, ge=1, le=20, description="Number of results"),
    query: str = Query(default="", description="Optional text query for RAG scoring"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    GET /recommend/{user_id}

    Args:
        user_id: target user ID
        limit  : max results (default 5)
        query  : optional context query for RAG (e.g. "laptop gaming")
    """
    # Fetch user's product interaction history (ordered by time)
    stmt = (
        select(UserBehavior.product_id)
        .where(UserBehavior.user_id == user_id)
        .order_by(UserBehavior.created_at.asc())
        .limit(50)
    )
    result = await db.execute(stmt)
    history = [row[0] for row in result.fetchall()]

    logger.info(f"[Recommend] user={user_id} history_len={len(history)}")

    try:
        recommendations = await hybrid_service.recommend(
            user_id=user_id,
            product_history=history,
            query=query,
            top_n=limit,
        )
    except Exception as exc:
        logger.error(f"Recommendation error for user {user_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Recommendation engine error: {str(exc)}",
        )

    return recommendations


@router.post(
    "/behavior",
    status_code=status.HTTP_201_CREATED,
    summary="Record a user behavior event",
    description="Logs a user interaction (VIEW, ADD_TO_CART, PURCHASE) for training data and graph sync.",
)
async def record_behavior(
    body: BehaviorIn,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    POST /recommend/behavior

    Records a user behavior and syncs it to the Neo4j graph.
    """
    # Save to PostgreSQL
    behavior = UserBehavior(
        user_id=str(body.user_id),
        product_id=str(body.product_id),
        action_type=body.action_type.value,
    )
    db.add(behavior)
    await db.flush()

    # Sync to Neo4j graph
    try:
        from app.services.graph_service import graph_service

        await graph_service.sync_behavior(
            user_id=str(body.user_id),
            product_id=str(body.product_id),
            action_type=body.action_type.value,
        )
    except Exception as exc:
        logger.warning(f"Graph sync failed (non-critical): {exc}")

    return {
        "status": "recorded",
        "user_id": body.user_id,
        "product_id": body.product_id,
        "action_type": body.action_type.value,
    }


@router.get(
    "/history/{user_id}",
    summary="Get user interaction history",
)
async def get_history(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return the raw behavior history for a user."""
    stmt = (
        select(UserBehavior)
        .where(UserBehavior.user_id == user_id)
        .order_by(UserBehavior.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "product_id": r.product_id,
            "action_type": r.action_type,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
