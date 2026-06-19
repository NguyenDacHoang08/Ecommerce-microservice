"""
RAGService — Retrieval-Augmented Generation for product search and chatbot.

Flow:
    Question → Embedding → FAISS Search → Top Products → Context → LLM/Template → Answer

Supports:
    - Template-based generation (no API key needed)
    - OpenAI GPT (when OPENAI_API_KEY is set)
"""
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGService:
    """
    RAG pipeline:
        1. search_products()  — embed query + FAISS nearest-neighbor search
        2. generate_context() — format products into readable context
        3. answer()           — full pipeline: search → context → LLM/template
    """

    def __init__(self) -> None:
        self._index = None  # faiss.Index
        self._products: list[dict] = []
        self._encoder = None  # SentenceTransformer
        self._loaded = False

    # ── Model / Index loading ─────────────────────────────────────────────────

    def load(self) -> None:
        """
        Load FAISS index and sentence encoder.
        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._loaded:
            return

        index_path = Path(settings.FAISS_INDEX_PATH)
        products_path = Path(settings.PRODUCTS_JSON_PATH)

        if not index_path.exists() or not products_path.exists():
            logger.warning(
                "FAISS index not found. "
                "Call POST /admin/build-index to create it first."
            )
            return

        try:
            import faiss
            from sentence_transformers import SentenceTransformer

            self._index = faiss.read_index(str(index_path))
            with open(products_path, encoding="utf-8") as f:
                self._products = json.load(f)
            self._encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._loaded = True
            logger.info(
                f"RAG loaded | products={len(self._products)} | "
                f"index_vectors={self._index.ntotal}"
            )
        except Exception as exc:
            logger.error(f"Failed to load RAG components: {exc}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._index is not None

    # ── Core functions ────────────────────────────────────────────────────────

    def search_products(
        self, query: str, top_k: Optional[int] = None
    ) -> list[dict]:
        """
        Search for products semantically similar to the query.

        Args:
            query : natural language query (e.g. "laptop gaming dưới 20 triệu")
            top_k : number of results (default from config)

        Returns:
            List of product dicts with an added 'score' field (cosine similarity).
        """
        if not self.is_loaded:
            logger.warning("RAG not loaded. Returning empty results.")
            return []

        k = top_k or settings.RAG_TOP_K
        embedding = self._encoder.encode(
            [query], normalize_embeddings=True
        ).astype("float32")

        distances, indices = self._index.search(embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self._products):
                product = dict(self._products[idx])
                product["score"] = float(dist)
                results.append(product)

        return results

    def generate_context(self, products: list[dict]) -> str:
        """
        Format a list of products into a readable text context for LLM prompting.

        Args:
            products: list of product dicts (with name, description, price, category)

        Returns:
            Formatted context string.
        """
        if not products:
            return "Không tìm thấy sản phẩm phù hợp."

        lines = ["Dưới đây là các sản phẩm phù hợp:\n"]
        for i, p in enumerate(products, 1):
            name = p.get("name", "Unknown")
            desc = p.get("description", "")
            price = p.get("price", 0) or 0
            category = p.get("category", "") or p.get("category_name", "")
            price_fmt = f"{int(float(price)):,}".replace(",", ".") + " VND"
            lines.append(
                f"{i}. **{name}** ({category})\n"
                f"   Giá: {price_fmt}\n"
                f"   Mô tả: {desc}\n"
            )

        return "\n".join(lines)

    def _build_prompt(self, question: str, context: str) -> str:
        return (
            "Bạn là trợ lý tư vấn mua sắm thông minh cho cửa hàng thương mại điện tử.\n"
            "Hãy trả lời câu hỏi của khách hàng dựa trên thông tin sản phẩm dưới đây.\n"
            "Trả lời bằng tiếng Việt, ngắn gọn, thân thiện và có ích.\n\n"
            f"Thông tin sản phẩm:\n{context}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Câu trả lời:"
        )

    def _template_answer(self, question: str, products: list[dict]) -> str:
        """
        Generate a response without calling any external LLM.
        Uses a structured template with retrieved product information.
        """
        if not products:
            return (
                "Xin lỗi, tôi không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn. "
                "Vui lòng thử tìm kiếm với từ khóa khác hoặc liên hệ nhân viên hỗ trợ."
            )

        top = products[0]
        name = top.get("name", "sản phẩm")
        price = top.get("price", 0) or 0
        price_fmt = f"{int(float(price)):,}".replace(",", ".") + " VND"
        desc = top.get("description", "")
        category = top.get("category", "") or top.get("category_name", "")

        response = f"Bạn có thể tham khảo **{name}** với giá {price_fmt}. {desc}"

        if len(products) > 1:
            response += "\n\nNgoài ra, bạn cũng có thể xem thêm:\n"
            for p in products[1:4]:
                p_name = p.get("name", "")
                p_price = p.get("price", 0) or 0
                p_price_fmt = f"{int(float(p_price)):,}".replace(",", ".") + " VND"
                response += f"- **{p_name}** — {p_price_fmt}\n"

        return response.strip()

    async def _openai_answer(self, question: str, context: str) -> str:
        """Generate answer using OpenAI GPT (async)."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = self._build_prompt(question, context)
            completion = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.7,
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"OpenAI call failed: {exc}. Falling back to template.")
            return None

    async def answer(self, question: str) -> dict:
        """
        Full RAG pipeline:
            question → search → context → generate answer

        Returns:
            {
                "answer": str,
                "products": list[dict],
                "source": "openai" | "template" | "no_index"
            }
        """
        if not self.is_loaded:
            # Build index with sample data on-the-fly
            logger.warning("RAG index not loaded. Attempting to build with sample data.")
            try:
                from app.vectorstore.build_index import build_index
                build_index()
                self._loaded = False  # force reload
                self.load()
            except Exception as exc:
                logger.error(f"Failed to build index: {exc}")
                return {
                    "answer": "Hệ thống AI đang khởi động. Vui lòng thử lại sau.",
                    "products": [],
                    "source": "no_index",
                }

        products = self.search_products(question)
        context = self.generate_context(products)

        # Try OpenAI if key is configured
        if settings.OPENAI_API_KEY:
            answer = await self._openai_answer(question, context)
            if answer:
                return {"answer": answer, "products": products, "source": "openai"}

        # Template-based fallback
        answer = self._template_answer(question, products)
        return {"answer": answer, "products": products, "source": "template"}

    async def build_index(self) -> dict:
        """Rebuild the FAISS index (can be called from admin endpoint)."""
        try:
            from app.vectorstore.build_index import build_index as _build

            n, path = _build()
            # Reload after rebuilding
            self._loaded = False
            self.load()
            return {"status": "success", "indexed": n, "path": path}
        except Exception as exc:
            logger.error(f"build_index failed: {exc}")
            return {"status": "error", "message": str(exc)}

    def get_product_scores(
        self, product_ids: list[str], query: str
    ) -> dict[str, float]:
        """
        Return RAG relevance scores for a specific set of product_ids.
        Used by HybridService for score fusion.
        """
        if not self.is_loaded or not product_ids:
            return {pid: 0.0 for pid in product_ids}

        results = self.search_products(query, top_k=50)
        score_map = {
            str(r.get("id") or r.get("product_id")): r["score"]
            for r in results
            if r.get("id") is not None or r.get("product_id") is not None
        }
        return {str(pid): score_map.get(str(pid), 0.0) for pid in product_ids}


# ── Module-level singleton ────────────────────────────────────────────────────
rag_service = RAGService()
