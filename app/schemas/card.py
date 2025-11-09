from datetime import datetime

from pydantic import BaseModel


class CardBase(BaseModel):
    external_card_id: str
    card_number_masked: str
    card_type: str | None = None
    card_brand: str | None = None


class CardResponse(CardBase):
    id: int
    account_id: int
    card_holder_name: str | None
    expiry_date: str | None
    is_active: bool
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True
