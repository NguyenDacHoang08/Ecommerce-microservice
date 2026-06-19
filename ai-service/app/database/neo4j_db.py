"""
Neo4j async driver singleton.
"""
from typing import AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import get_settings

settings = get_settings()

_driver: AsyncDriver | None = None


async def get_driver() -> AsyncDriver:
    """Return the shared Neo4j async driver (lazy init)."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


async def close_driver() -> None:
    """Close the Neo4j driver on shutdown."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def neo4j_dependency() -> AsyncGenerator[AsyncDriver, None]:
    """FastAPI dependency that yields the Neo4j driver."""
    driver = await get_driver()
    yield driver
