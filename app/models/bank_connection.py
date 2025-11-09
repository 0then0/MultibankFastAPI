from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class BankConnection(Base, TimestampMixin):
    """Bank connection model for storing OAuth tokens and bank connection info."""

    __tablename__ = "bank_connections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_identifier: Mapped[str] = mapped_column(String(255), nullable=False)

    # OAuth tokens (encrypted)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Connection status
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bank_connections")
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="bank_connection", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<BankConnection(id={self.id}, user_id={self.user_id}, bank_name={self.bank_name})>"
