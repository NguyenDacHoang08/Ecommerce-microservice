"""
Application configuration using pydantic-settings.
All values are loaded from environment variables.
"""
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────
    APP_NAME: str = "AI Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "info", "warn", "warning", "error", ""}:
                return False
        return value

    # ── PostgreSQL (AI dedicated DB) ─────────────────────────
    POSTGRES_HOST: str = "postgres-ai"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "ai_user"
    POSTGRES_PASSWORD: str = "ai_password"
    POSTGRES_DB: str = "ai_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Neo4j ────────────────────────────────────────────────
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"

    # ── LSTM ─────────────────────────────────────────────────
    LSTM_MODEL_PATH: str = "models/lstm_model.pth"
    LSTM_VOCAB_PATH: str = "models/product_vocab.json"
    LSTM_EMBED_DIM: int = 64
    LSTM_HIDDEN_DIM: int = 128
    LSTM_NUM_LAYERS: int = 2
    LSTM_SEQ_LEN: int = 10
    BEHAVIOR_CSV_PATH: str = "data/user_behavior.csv"

    # ── RAG / FAISS ──────────────────────────────────────────
    FAISS_INDEX_PATH: str = "vectorstore/product.index"
    PRODUCTS_JSON_PATH: str = "vectorstore/products.json"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5

    # ── Product Service (for syncing product data) ───────────
    PRODUCT_SERVICE_URL: str = "http://product-service:8001"

    # ── OpenAI (optional – fallback to template if not set) ──
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # ── Hybrid weights ───────────────────────────────────────
    WEIGHT_LSTM: float = 0.4
    WEIGHT_GRAPH: float = 0.3
    WEIGHT_RAG: float = 0.3
    TOP_N_RESULTS: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
