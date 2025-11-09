from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.card import Card
from app.models.user import User
from app.schemas.card import CardResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=list[CardResponse])
async def get_cards(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all user cards."""
    result = await db.execute(
        select(Card).where(Card.user_id == current_user.id)
    )
    cards = result.scalars().all()
    return cards


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get specific card details."""
    result = await db.execute(
        select(Card).where(
            Card.id == card_id,
            Card.user_id == current_user.id,
        )
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    return card
