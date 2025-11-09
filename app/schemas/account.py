from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


class AccountBase(BaseModel):
    external_account_id: str
    account_type: str
    account_name: str | None = None
    currency: str = "RUB"


class AccountResponse(AccountBase):
    id: int
    balance: Decimal
    available_balance: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("balance", "available_balance")
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class AccountAggregated(BaseModel):
    total_balance: Decimal
    accounts: list[AccountResponse]
    currency: str = "RUB"

    @field_serializer("total_balance")
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)
