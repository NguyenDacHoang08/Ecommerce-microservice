"""
SQLAlchemy ORM model for user behavior tracking.

Schema:
    CREATE TABLE user_behavior(
        id          SERIAL PRIMARY KEY,
        user_id     VARCHAR(128),
        product_id  VARCHAR(128),
        action_type VARCHAR(50),   -- VIEW | ADD_TO_CART | PURCHASE
        created_at  TIMESTAMP DEFAULT NOW()
    );
"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.postgres import Base


class ActionType(str, enum.Enum):
    VIEW = "VIEW"
    ADD_TO_CART = "ADD_TO_CART"
    PURCHASE = "PURCHASE"


class UserBehavior(Base):
    __tablename__ = "user_behavior"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(
        Enum(ActionType, name="action_type_enum"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<UserBehavior user={self.user_id} "
            f"product={self.product_id} action={self.action_type}>"
        )
