from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Account(Base, TimestampMixin):
    """Bank account model."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bank_connection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bank_connections.id"), nullable=False
    )

    # Account details from API
    external_account_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    account_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_type: Mapped[str] = mapped_column(String(100), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")

    # Balance
    balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    bank_connection: Mapped["BankConnection"] = relationship(
        "BankConnection", back_populates="accounts"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )
    cards: Mapped[list["Card"]] = relationship(
        "Card", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, external_id={self.external_account_id}, balance={self.balance})>"
