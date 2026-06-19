"""
build_index.py — Build FAISS vector index from product data.

Run:
    python -m app.vectorstore.build_index

Flow:
    1. Fetch products from product-service API (or use sample data)
    2. Encode product descriptions with sentence-transformers
    3. Build FAISS IndexFlatL2
    4. Save index → vectorstore/product.index
    5. Save product metadata → vectorstore/products.json
"""
import json
import logging
import sys
from pathlib import Path

import httpx
import numpy as np

# ── Allow running as script ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

INDEX_PATH = Path(settings.FAISS_INDEX_PATH)
PRODUCTS_PATH = Path(settings.PRODUCTS_JSON_PATH)
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Sample product data (fallback when product-service unreachable) ───────────
SAMPLE_PRODUCTS: list[dict] = [
    {
        "id": 101,
        "name": "Dell G15 Gaming Laptop",
        "description": "Gaming laptop with RTX 4050, Intel Core i7, 16GB RAM, 512GB SSD. Perfect for gaming and heavy workloads.",
        "price": 19000000,
        "category": "Laptop",
    },
    {
        "id": 102,
        "name": "ASUS ROG Strix G15",
        "description": "ROG gaming laptop with RTX 4060, AMD Ryzen 7, 16GB RAM, 1TB SSD. 165Hz display for competitive gaming.",
        "price": 22000000,
        "category": "Laptop",
    },
    {
        "id": 103,
        "name": "Lenovo IdeaPad Gaming 3",
        "description": "Budget gaming laptop RTX 3050, Intel Core i5, 8GB RAM, 512GB SSD. Great entry-level gaming.",
        "price": 15000000,
        "category": "Laptop",
    },
    {
        "id": 104,
        "name": "MSI Katana GF66",
        "description": "MSI gaming laptop RTX 3060, Intel Core i7, 16GB RAM. Thin and light design for on-the-go gaming.",
        "price": 20000000,
        "category": "Laptop",
    },
    {
        "id": 105,
        "name": "HP Omen 16",
        "description": "HP Omen gaming laptop RTX 4070, Intel Core i9. Premium build quality with excellent cooling system.",
        "price": 28000000,
        "category": "Laptop",
    },
    {
        "id": 201,
        "name": "iPhone 15 Pro Max",
        "description": "Apple iPhone 15 Pro Max with A17 Pro chip, 256GB storage. Titanium design with ProMotion display.",
        "price": 34000000,
        "category": "Smartphone",
    },
    {
        "id": 202,
        "name": "Samsung Galaxy S24 Ultra",
        "description": "Samsung flagship with S-Pen, 200MP camera, Snapdragon 8 Gen 3. Best Android smartphone 2024.",
        "price": 32000000,
        "category": "Smartphone",
    },
    {
        "id": 203,
        "name": "Xiaomi 14 Ultra",
        "description": "Xiaomi flagship with Leica camera system, Snapdragon 8 Gen 3, 90W fast charging.",
        "price": 25000000,
        "category": "Smartphone",
    },
    {
        "id": 301,
        "name": "Sony WH-1000XM5",
        "description": "Industry-leading noise cancelling headphones. 30 hours battery life, multipoint connection.",
        "price": 8000000,
        "category": "Audio",
    },
    {
        "id": 302,
        "name": "AirPods Pro 2nd Gen",
        "description": "Apple AirPods Pro with Adaptive Audio, Active Noise Cancellation, H2 chip.",
        "price": 6500000,
        "category": "Audio",
    },
    {
        "id": 401,
        "name": "LG 27GP850-B Monitor",
        "description": "27-inch QHD gaming monitor, 165Hz, 1ms response time, Nano IPS panel. G-Sync and FreeSync compatible.",
        "price": 9000000,
        "category": "Monitor",
    },
    {
        "id": 402,
        "name": "ASUS ROG Swift PG279QM",
        "description": "27-inch QHD gaming monitor, 240Hz, G-Sync Ultimate. Professional gaming display.",
        "price": 14000000,
        "category": "Monitor",
    },
    {
        "id": 501,
        "name": "Logitech MX Master 3S",
        "description": "Premium wireless mouse with MagSpeed scroll, 8K DPI sensor. Silent clicks, ergonomic design.",
        "price": 2500000,
        "category": "Peripheral",
    },
    {
        "id": 502,
        "name": "Keychron Q1 Pro",
        "description": "75% wireless mechanical keyboard with QMK/VIA support, aluminum body, hot-swappable switches.",
        "price": 4000000,
        "category": "Peripheral",
    },
]


def fetch_products() -> list[dict]:
    """Fetch products from product-service. Falls back to sample data."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{settings.PRODUCT_SERVICE_URL}/api/products/?limit=1000")
            response.raise_for_status()
            data = response.json()
            # Handle both paginated and flat responses
            if isinstance(data, dict) and "results" in data:
                products = data["results"]
            elif isinstance(data, list):
                products = data
            else:
                products = []
            if products:
                logger.info(f"Fetched {len(products)} products from product-service.")
                return products
    except Exception as exc:
        logger.warning(f"Could not fetch from product-service: {exc}. Using sample data.")

    logger.info(f"Using {len(SAMPLE_PRODUCTS)} sample products.")
    return SAMPLE_PRODUCTS


def build_text(product: dict) -> str:
    """Create a rich text representation of a product for embedding."""
    name = product.get("name", "")
    desc = product.get("description", "")
    category = product.get("category", "") or product.get("category_name", "")
    price = product.get("price", "")
    return f"{name}. {desc}. Category: {category}. Price: {price} VND."


def build_index(products: list[dict] | None = None) -> tuple[int, str]:
    """
    Build and persist FAISS index.

    Returns:
        (n_products, index_path)
    """
    import faiss
    from sentence_transformers import SentenceTransformer

    if products is None:
        products = fetch_products()

    print(f"Encoding {len(products)} products with {settings.EMBEDDING_MODEL}...")
    model = SentenceTransformer(settings.EMBEDDING_MODEL)

    texts = [build_text(p) for p in products]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    # Build flat L2 index (suitable for up to ~100K products)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product (cosine sim with normalized vecs)
    index.add(embeddings)

    # Save
    faiss.write_index(index, str(INDEX_PATH))
    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"FAISS index saved → {INDEX_PATH} ({index.ntotal} vectors, dim={dim})")
    print(f"Product metadata saved → {PRODUCTS_PATH}")
    return index.ntotal, str(INDEX_PATH)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    n, path = build_index()
    print(f"Done. Indexed {n} products at {path}")
