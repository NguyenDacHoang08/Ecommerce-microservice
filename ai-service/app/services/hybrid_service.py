"""
HybridService — Score fusion from LSTM + Graph + RAG engines.

Formula:
    final_score = 0.4 * lstm_score + 0.3 * graph_score + 0.3 * rag_score

All individual scores are min-max normalized to [0, 1] before fusion.
Returns top-N products sorted by final_score descending.
"""
import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.services.graph_service import GraphService, graph_service
from app.services.lstm_service import LSTMService, lstm_service
from app.services.rag_service import RAGService, rag_service

logger = logging.getLogger(__name__)
settings = get_settings()

ProductId = str


def _product_id(product: dict) -> ProductId:
    raw_id = product.get("id") or product.get("product_id")
    return str(raw_id) if raw_id is not None else ""


def _category(product: dict) -> str:
    return str(product.get("category") or product.get("category_name") or "")


def _image_url(product: dict) -> str | None:
    if product.get("image_url"):
        return product["image_url"]
    images = product.get("images") or []
    if not isinstance(images, list) or not images:
        return None
    primary = next((img for img in images if img.get("is_primary")), images[0])
    return primary.get("url")


def _recommendation_payload(
    product: dict,
    score: float,
    source: str | None = None,
) -> dict:
    payload = {
        "product_id": _product_id(product),
        "name": product.get("name", "Unknown"),
        "description": product.get("description", ""),
        "score": round(score, 4),
        "price": product.get("effective_price") or product.get("price", 0),
        "category": _category(product),
        "image_url": _image_url(product),
        "status": product.get("status", "active"),
        "quantity": product.get("quantity"),
    }
    if source:
        payload["source"] = source
    return payload


def _normalize(scores: dict[ProductId, float]) -> dict[ProductId, float]:
    """Min-max normalize a score dictionary to [0, 1]."""
    if not scores:
        return {}
    values = list(scores.values())
    min_v, max_v = min(values), max(values)
    if max_v == min_v:
        return {k: 1.0 for k in scores}
    return {k: (v - min_v) / (max_v - min_v) for k, v in scores.items()}


async def _fetch_product_names(product_ids: list[ProductId]) -> dict[ProductId, dict]:
    """
    Fetch product details from product-service.
    Returns mapping: product_id → {name, price, category, ...}
    """
    product_map: dict[ProductId, dict] = {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for pid in product_ids:
                normalized_pid = str(pid)
                resp = await client.get(
                    f"{settings.PRODUCT_SERVICE_URL}/api/products/{normalized_pid}/"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    product_map[normalized_pid] = data
    except Exception as exc:
        logger.warning(f"Could not fetch product details: {exc}")

    # Fill missing with defaults (use RAG product store as fallback)
    if rag_service.is_loaded:
        for pid in product_ids:
            normalized_pid = str(pid)
            if normalized_pid not in product_map:
                for p in rag_service._products:
                    if _product_id(p) == normalized_pid:
                        product_map[normalized_pid] = p
                        break

    return product_map


class HybridService:
    """
    Combines LSTM, Graph, and RAG recommendations using weighted score fusion.
    """

    def __init__(
        self,
        lstm: LSTMService,
        graph: GraphService,
        rag: RAGService,
    ) -> None:
        self._lstm = lstm
        self._graph = graph
        self._rag = rag

    async def recommend(
        self,
        user_id: str,
        product_history: Optional[list[ProductId]] = None,
        query: str = "",
        top_n: Optional[int] = None,
    ) -> list[dict]:
        """
        Generate hybrid recommendations for a user.

        Args:
            user_id        : target user
            product_history: ordered list of product_ids (for LSTM)
            query          : free-text query for RAG scoring (optional)
            top_n          : number of results (default from config)

        Returns:
            List of dicts:
            [{"product_id": 101, "name": "Dell G15", "score": 0.92, ...}]
        """
        n = top_n or settings.TOP_N_RESULTS
        history = [str(pid) for pid in (product_history or [])]

        # ── Step 1: Collect candidate scores from each engine ────────────────

        # LSTM scores
        lstm_raw: dict[ProductId, float] = {}
        if self._lstm.is_loaded and history:
            lstm_results = self._lstm.predict(history, top_k=20)
            lstm_raw = {pid: score for pid, score in lstm_results}

        # Graph scores
        graph_raw: dict[ProductId, float] = {}
        try:
            graph_results = await self._graph.recommend_from_graph(user_id, limit=20)
            graph_raw = {str(pid): score for pid, score in graph_results}
        except Exception as exc:
            logger.warning(f"Graph recommendation failed: {exc}")

        # Gather all candidate product IDs
        all_candidates = set(lstm_raw.keys()) | set(graph_raw.keys())

        if not all_candidates:
            # Cold-start: use top RAG results
            logger.info(f"Cold-start for user {user_id}, using RAG only.")
            if self._rag.is_loaded:
                fallback_query = query or "sản phẩm phổ biến"
                rag_products = self._rag.search_products(fallback_query, top_k=n)
                return [
                    _recommendation_payload(
                        p,
                        score=float(p.get("score", 0.0)),
                        source="rag_cold_start",
                    )
                    for p in rag_products
                    if _product_id(p)
                ]
            return []

        # RAG scores for candidates
        rag_raw: dict[ProductId, float] = {}
        if self._rag.is_loaded:
            rag_query = query or "sản phẩm tốt"
            rag_raw = self._rag.get_product_scores(list(all_candidates), rag_query)

        # ── Step 2: Normalize each score set ────────────────────────────────
        lstm_norm = _normalize(lstm_raw)
        graph_norm = _normalize(graph_raw)
        rag_norm = _normalize(rag_raw)

        w_lstm = settings.WEIGHT_LSTM
        w_graph = settings.WEIGHT_GRAPH
        w_rag = settings.WEIGHT_RAG

        # ── Step 3: Compute final fusion scores ──────────────────────────────
        fusion: dict[ProductId, float] = {}
        for pid in all_candidates:
            fusion[pid] = (
                w_lstm * lstm_norm.get(pid, 0.0)
                + w_graph * graph_norm.get(pid, 0.0)
                + w_rag * rag_norm.get(pid, 0.0)
            )

        # Sort and take top-N
        top_ids = sorted(fusion, key=fusion.__getitem__, reverse=True)[:n]

        # ── Step 4: Enrich with product metadata ─────────────────────────────
        product_details = await _fetch_product_names(top_ids)

        results = []
        for pid in top_ids:
            details = product_details.get(pid, {})

            # Skip products that couldn't be fetched from product-service.
            # This filters out stale / mock integer IDs stored in the graph
            # that no longer match real UUID-based products.
            if not details:
                logger.debug(
                    f"[Recommend] Skipping product_id={pid}: not found in product-service"
                )
                continue

            results.append(
                {
                    "product_id": pid,
                    "name": details.get("name", f"Product {pid}"),
                    "description": details.get("description", ""),
                    "score": round(fusion[pid], 4),
                    "price": details.get("effective_price") or details.get("price", 0),
                    "category": _category(details),
                    "image_url": _image_url(details),
                    "status": details.get("status", "active"),
                    "quantity": details.get("quantity"),
                    "lstm_score": round(lstm_norm.get(pid, 0.0), 4),
                    "graph_score": round(graph_norm.get(pid, 0.0), 4),
                    "rag_score": round(rag_norm.get(pid, 0.0), 4),
                }
            )

        # If all candidate IDs were stale/invalid, fall back to RAG cold-start
        # so the user always sees real products.
        if not results and self._rag.is_loaded:
            logger.info(
                f"[Recommend] All graph/LSTM candidates were invalid for user={user_id}. "
                "Falling back to RAG cold-start."
            )
            fallback_query = query or "sản phẩm phổ biến"
            rag_products = self._rag.search_products(fallback_query, top_k=n)
            return [
                _recommendation_payload(
                    p,
                    score=float(p.get("score", 0.0)),
                    source="rag_cold_start",
                )
                for p in rag_products
                if _product_id(p)
            ]

        return results


# ── Module-level singleton ────────────────────────────────────────────────────
hybrid_service = HybridService(
    lstm=lstm_service,
    graph=graph_service,
    rag=rag_service,
)
