from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ActiveUser, SuperUser
from app.db.session import get_db
from app.models.account import Account
from app.models.card import Card
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserWithStats

router = APIRouter()


@router.get("/me/stats", response_model=UserWithStats)
async def get_my_stats(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current user statistics."""
    # Get total accounts
    accounts_result = await db.execute(
        select(func.count(Account.id)).where(
            Account.user_id == current_user.id,
            Account.is_active == True,  # noqa: E712
        )
    )
    total_accounts = accounts_result.scalar() or 0

    # Get total cards
    cards_result = await db.execute(
        select(func.count(Card.id)).where(
            Card.user_id == current_user.id,
            Card.is_active == True,  # noqa: E712
        )
    )
    total_cards = cards_result.scalar() or 0

    # Get total balance
    balance_result = await db.execute(
        select(func.sum(Account.balance)).where(
            Account.user_id == current_user.id,
            Account.is_active == True,  # noqa: E712
        )
    )
    total_balance = float(balance_result.scalar() or 0)

    return UserWithStats(
        **current_user.__dict__,
        total_accounts=total_accounts,
        total_cards=total_cards,
        total_balance=total_balance,
    )


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user profile."""
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        result = await db.execute(select(User).where(User.email == user_update.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = user_update.email

    # Update other fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete current user account (soft delete)."""
    current_user.is_active = False
    await db.commit()


# Admin endpoints (superuser only)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    current_user: SuperUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    """List all users (superuser only)."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: SuperUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user by ID (superuser only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: SuperUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update user by ID (superuser only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.is_premium is not None:
        user.is_premium = user_update.is_premium

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: SuperUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete user by ID (superuser only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()
