from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Card(Base, TimestampMixin):
    """Bank card model."""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Card details from API
    external_card_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    card_number_masked: Mapped[str] = mapped_column(String(50), nullable=False)
    card_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    card_brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    card_holder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cards")
    account: Mapped["Account"] = relationship("Account", back_populates="cards")

    def __repr__(self) -> str:
        return f"<Card(id={self.id}, masked_number={self.card_number_masked})>"
