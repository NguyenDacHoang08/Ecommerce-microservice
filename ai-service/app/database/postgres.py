"""
Async PostgreSQL connection using SQLAlchemy with asyncpg driver.
"""
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Base for ORM models ───────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency injection ──────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables on startup (idempotent)."""
    from app.models import behavior  # noqa: F401 – ensure model is registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Older local AI databases used BIGINT IDs. Product/user services use UUIDs,
        # so keep the behavior table compatible with both numeric IDs and UUIDs.
        await conn.execute(
            text(
                "ALTER TABLE user_behavior "
                "ALTER COLUMN user_id TYPE VARCHAR(128) USING user_id::text"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE user_behavior "
                "ALTER COLUMN product_id TYPE VARCHAR(128) USING product_id::text"
            )
        )


async def close_db() -> None:
    """Dispose engine on shutdown."""
    await engine.dispose()
