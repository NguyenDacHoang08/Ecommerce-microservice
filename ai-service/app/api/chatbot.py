"""
Chatbot API — POST /chatbot

Flow:
    Question → Embedding → FAISS Search → Top Products → Context → Answer
"""
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's question in Vietnamese or English",
        examples=["Laptop gaming dưới 20 triệu"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of products to retrieve for context",
    )


class ProductRef(BaseModel):
    id: str | None = None
    name: str | None = None
    price: float | None = None
    category: str | None = None
    score: float | None = None
    image_url: str | None = None


class ChatResponse(BaseModel):
    answer: str
    source: str  # "openai" | "template" | "no_index"
    products: list[ProductRef] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the AI product assistant",
    description="""
    AI-powered product chatbot using RAG (Retrieval-Augmented Generation).

    Flow:
    1. Embed the question using `all-MiniLM-L6-v2`
    2. Search FAISS index for semantically similar products
    3. Generate a contextual answer (OpenAI GPT if key configured, else template)

    **Supports Vietnamese and English questions.**
    """,
)
async def chat(body: ChatRequest) -> dict:
    """
    POST /chatbot

    Example request:
        {"question": "Laptop gaming dưới 20 triệu"}

    Example response:
        {
            "answer": "Bạn có thể tham khảo Dell G15...",
            "source": "template",
            "products": [{"name": "Dell G15", "price": 19000000, ...}]
        }
    """
    logger.info(f"[Chatbot] question='{body.question[:80]}'")

    try:
        result = await rag_service.answer(body.question)
    except Exception as exc:
        logger.error(f"Chatbot error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chatbot engine error: {str(exc)}",
        )

    # Format products for response
    products = []
    for p in result.get("products", []):
        raw_id = p.get("id") or p.get("product_id")
        products.append(
            ProductRef(
                id=str(raw_id) if raw_id is not None else None,
                name=p.get("name"),
                price=p.get("price"),
                category=p.get("category") or p.get("category_name"),
                score=p.get("score"),
                image_url=p.get("image_url"),
            )
        )

    return ChatResponse(
        answer=result["answer"],
        source=result.get("source", "template"),
        products=products,
    )


@router.post(
    "/search",
    summary="Semantic product search",
    description="Search for products by natural language query without generating a text answer.",
)
async def semantic_search(
    body: ChatRequest,
) -> list[dict]:
    """
    POST /chatbot/search

    Returns raw FAISS search results without LLM generation.
    Useful for frontend product search integration.
    """
    if not rag_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search index not available. POST /admin/build-index first.",
        )

    products = rag_service.search_products(body.question, top_k=body.top_k)
    return [
        {
            "product_id": str(p.get("id") or p.get("product_id")),
            "name": p.get("name", "Unknown"),
            "description": p.get("description", ""),
            "price": p.get("price", 0),
            "category": p.get("category", "") or p.get("category_name", ""),
            "image_url": p.get("image_url"),
            "score": round(p.get("score", 0.0), 4),
        }
        for p in products
    ]
