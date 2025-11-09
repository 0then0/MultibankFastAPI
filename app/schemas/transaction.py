from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class TransactionBase(BaseModel):
    external_transaction_id: str
    transaction_date: datetime
    amount: Decimal
    currency: str = "RUB"
    transaction_type: str


class TransactionResponse(TransactionBase):
    id: int
    account_id: int
    description: str | None
    merchant_name: str | None
    merchant_category: str | None
    category: str | None
    balance_after: Decimal | None
    created_at: datetime

    @field_serializer("amount", "balance_after")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    transaction_type: str | None = None
    category: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
