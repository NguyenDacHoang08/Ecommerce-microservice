"""
GraphService — Neo4j Knowledge Graph operations.

Graph schema:
    Nodes      : User, Product, Category
    Relationships:
        (User)-[:VIEW]      -> (Product)
        (User)-[:BUY]       -> (Product)
        (Product)-[:SIMILAR]-> (Product)
        (Product)-[:BELONG_TO]->(Category)
"""
import logging
from typing import Any, Optional

from neo4j import AsyncDriver

from app.config import get_settings
from app.database.neo4j_db import get_driver

logger = logging.getLogger(__name__)
settings = get_settings()

ProductId = int
Score = float


class GraphService:
    """
    All Neo4j read/write operations for the recommendation knowledge graph.
    """

    def __init__(self, driver: Optional[AsyncDriver] = None) -> None:
        self._driver = driver  # injected or fetched lazily

    async def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            self._driver = await get_driver()
        return self._driver

    # ─── Node creation ────────────────────────────────────────────────────────

    async def create_user(self, user_id: int) -> None:
        """Create (or merge) a User node."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                "MERGE (u:User {id: $user_id})",
                user_id=user_id,
            )

    async def create_product(
        self,
        product_id: int,
        name: str = "",
        price: float = 0.0,
        category: str = "",
    ) -> None:
        """Create (or merge) a Product node and link it to its Category."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (p:Product {id: $product_id})
                SET p.name = $name, p.price = $price
                WITH p
                MERGE (c:Category {name: $category})
                MERGE (p)-[:BELONG_TO]->(c)
                """,
                product_id=product_id,
                name=name,
                price=price,
                category=category,
            )

    async def create_category(self, name: str) -> None:
        """Create (or merge) a Category node."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                "MERGE (c:Category {name: $name})", name=name
            )

    # ─── Relationship creation ────────────────────────────────────────────────

    async def create_relationship(
        self,
        user_id: int,
        product_id: int,
        rel_type: str,  # "VIEW" | "BUY"
    ) -> None:
        """
        Create a relationship between User and Product.

        Args:
            rel_type: "VIEW" or "BUY"
        """
        if rel_type not in ("VIEW", "BUY", "ADD_TO_CART"):
            raise ValueError(f"Invalid relationship type: {rel_type}")

        # Map ADD_TO_CART to VIEW for graph simplicity
        graph_rel = "BUY" if rel_type == "PURCHASE" else "VIEW"
        if rel_type == "BUY":
            graph_rel = "BUY"

        driver = await self._get_driver()
        async with driver.session() as session:
            query = f"""
                MERGE (u:User {{id: $user_id}})
                MERGE (p:Product {{id: $product_id}})
                MERGE (u)-[r:{graph_rel}]->(p)
                ON CREATE SET r.count = 1
                ON MATCH  SET r.count = r.count + 1
            """
            await session.run(query, user_id=user_id, product_id=product_id)

    async def create_similarity(
        self, product_id_a: int, product_id_b: int, score: float = 1.0
    ) -> None:
        """Create a bidirectional SIMILAR relationship between two products."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (a:Product {id: $id_a})
                MERGE (b:Product {id: $id_b})
                MERGE (a)-[r:SIMILAR]->(b)
                SET r.score = $score
                MERGE (b)-[r2:SIMILAR]->(a)
                SET r2.score = $score
                """,
                id_a=product_id_a,
                id_b=product_id_b,
                score=score,
            )

    # ─── Queries ──────────────────────────────────────────────────────────────

    async def get_similar_products(
        self, product_id: int, limit: int = 10
    ) -> list[tuple[ProductId, Score]]:
        """
        Return products similar to the given product.

        Cypher:
            MATCH (p:Product {id: $product_id})-[r:SIMILAR]->(rec)
            RETURN rec.id, r.score ORDER BY r.score DESC LIMIT $limit
        """
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Product {id: $product_id})-[r:SIMILAR]->(rec:Product)
                RETURN rec.id AS product_id, r.score AS score
                ORDER BY score DESC
                LIMIT $limit
                """,
                product_id=product_id,
                limit=limit,
            )
            records = await result.data()
            return [(r["product_id"], float(r["score"])) for r in records]

    async def recommend_from_graph(
        self, user_id: int, limit: int = 10
    ) -> list[tuple[ProductId, Score]]:
        """
        Recommend products via collaborative filtering through the graph.

        Cypher pattern:
            MATCH (u:User {id: $user_id})-[:BUY]->(p)-[:SIMILAR]->(rec)
            WHERE NOT (u)-[:BUY]->(rec)
            RETURN rec.id, COUNT(*) AS score
            ORDER BY score DESC LIMIT $limit

        Also falls back to VIEW-based similarity if no BUY relationships exist.
        """
        driver = await self._get_driver()
        async with driver.session() as session:
            # Primary: BUY-based
            result = await session.run(
                """
                MATCH (u:User {id: $user_id})-[:BUY]->(p:Product)-[:SIMILAR]->(rec:Product)
                WHERE NOT (u)-[:BUY]->(rec)
                RETURN rec.id AS product_id, COUNT(*) AS score
                ORDER BY score DESC
                LIMIT $limit
                """,
                user_id=user_id,
                limit=limit,
            )
            records = await result.data()

            if not records:
                # Fallback: VIEW-based
                result = await session.run(
                    """
                    MATCH (u:User {id: $user_id})-[:VIEW]->(p:Product)-[:SIMILAR]->(rec:Product)
                    WHERE NOT (u)-[:VIEW]->(rec)
                    RETURN rec.id AS product_id, COUNT(*) AS score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    user_id=user_id,
                    limit=limit,
                )
                records = await result.data()

            if not records:
                # Cold-start fallback: popular products in same categories
                result = await session.run(
                    """
                    MATCH (p:Product)<-[:BUY]-(:User)
                    WHERE NOT (:User {id: $user_id})-[:BUY]->(p)
                    RETURN p.id AS product_id, COUNT(*) AS score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    user_id=user_id,
                    limit=limit,
                )
                records = await result.data()

            return [(r["product_id"], float(r["score"])) for r in records]

    async def get_user_history(self, user_id: int) -> list[ProductId]:
        """Return product_ids the user has viewed or bought."""
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (u:User {id: $user_id})-[:VIEW|BUY]->(p:Product)
                RETURN DISTINCT p.id AS product_id
                """,
                user_id=user_id,
            )
            records = await result.data()
            return [r["product_id"] for r in records]

    async def sync_behavior(
        self, user_id: int, product_id: int, action_type: str
    ) -> None:
        """
        High-level method to sync a behavior event to the graph.
        Maps action_type to graph relationship type.
        """
        await self.create_user(user_id)
        rel_type = "BUY" if action_type == "PURCHASE" else "VIEW"
        await self.create_relationship(user_id, product_id, rel_type)

    async def get_stats(self) -> dict[str, Any]:
        """Return basic graph statistics."""
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (u:User) WITH COUNT(u) AS users
                MATCH (p:Product) WITH users, COUNT(p) AS products
                MATCH (c:Category) WITH users, products, COUNT(c) AS categories
                RETURN users, products, categories
                """
            )
            record = await result.single()
            if record:
                return dict(record)
            return {"users": 0, "products": 0, "categories": 0}

    async def import_from_csv(self, csv_path: str) -> dict[str, Any]:
        """
        Read user behaviors from a CSV file and populate Neo4j Knowledge Graph.
        """
        import csv
        import os
        from app.vectorstore.build_index import fetch_products

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV behavior file not found at: {csv_path}")

        # Fetch product metadata to populate product names, categories, and prices
        try:
            products_list = fetch_products()
            product_map = {p.get("id"): p for p in products_list if p.get("id") is not None}
        except Exception as exc:
            logger.warning(f"Could not fetch product catalog: {exc}. Using IDs only.")
            product_map = {}

        imported_rows = 0
        users_created = set()
        products_created = set()
        categories_created = set()

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    user_id_str = row.get("user_id")
                    product_id_str = row.get("product_id")
                    action_type = row.get("action_type") or row.get("action")

                    if not user_id_str or not product_id_str or not action_type:
                        continue

                    user_id = int(user_id_str)
                    product_id = int(product_id_str)

                    # Create Product (with details if available)
                    p_info = product_map.get(product_id, {})
                    p_name = p_info.get("name") or f"Product {product_id}"
                    p_price = float(p_info.get("price") or 0.0)
                    p_category = p_info.get("category") or p_info.get("category_name") or "Uncategorized"

                    await self.create_product(
                        product_id=product_id,
                        name=p_name,
                        price=p_price,
                        category=p_category
                    )
                    products_created.add(product_id)
                    categories_created.add(p_category)

                    # Create User and link relationship via sync_behavior
                    await self.sync_behavior(user_id, product_id, action_type)
                    users_created.add(user_id)

                    imported_rows += 1
                except Exception as row_exc:
                    logger.error(f"Error importing CSV row {row}: {row_exc}")
                    continue

        return {
            "status": "success",
            "imported_rows": imported_rows,
            "users_created_count": len(users_created),
            "products_created_count": len(products_created),
            "categories_created_count": len(categories_created),
        }


# ── Module-level singleton ────────────────────────────────────────────────────
graph_service = GraphService()
