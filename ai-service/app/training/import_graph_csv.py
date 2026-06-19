"""
import_graph_csv.py — Standalone script to import user behavior CSV to Neo4j.

Run:
    python -m app.training.import_graph_csv
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# ── Allow running as script from project root ─────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

from app.config import get_settings
from app.services.graph_service import graph_service

settings = get_settings()


async def main():
    logger.info("=" * 60)
    logger.info("  Neo4j Knowledge Graph — Import from CSV")
    logger.info("=" * 60)

    # Resolve CSV file path
    possible_paths = [
        Path("data/user_behavior.csv"),
        Path("ai-service/data/user_behavior.csv"),
        Path(__file__).resolve().parents[2] / "data" / "user_behavior.csv"
    ]

    csv_path = None
    for path in possible_paths:
        if path.exists():
            csv_path = path
            break

    if not csv_path:
        logger.error(
            f"Could not find user_behavior.csv in any of the search paths:\n"
            f"  - {os.path.abspath('data/user_behavior.csv')}\n"
            f"  - {os.path.abspath('ai-service/data/user_behavior.csv')}\n"
            f"  - {possible_paths[2]}"
        )
        sys.exit(1)

    logger.info(f"Using CSV file: {csv_path.resolve()}")

    try:
        # Check driver connection
        driver = await graph_service._get_driver()
        await driver.verify_connectivity()
        logger.info("✓ Neo4j driver connected successfully.")
    except Exception as exc:
        logger.error(f"✗ Failed to connect to Neo4j database: {exc}")
        sys.exit(1)

    logger.info("Starting import...")
    try:
        stats = await graph_service.import_from_csv(str(csv_path))
        logger.info("=" * 60)
        logger.info("✓ Import Completed Successfully!")
        logger.info(f"  Imported CSV Rows : {stats['imported_rows']}")
        logger.info(f"  Users Created     : {stats['users_created_count']}")
        logger.info(f"  Products Created  : {stats['products_created_count']}")
        logger.info(f"  Categories Created: {stats['categories_created_count']}")
        logger.info("=" * 60)
    except Exception as exc:
        logger.error(f"✗ Import failed with error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
