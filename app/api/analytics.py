from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/spending-by-category")
async def get_spending_by_category(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get spending grouped by category."""
    result = await db.execute(
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.amount < 0,  # Only expenses
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount))
    )

    categories = []
    for row in result:
        categories.append({
            "category": row.category or "Uncategorized",
            "total": abs(float(row.total)) if row.total else 0,
            "count": row.count,
        })

    return {"categories": categories}


@router.get("/monthly-summary")
async def get_monthly_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get monthly income and expenses summary."""
    # Get expenses
    expenses_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.amount < 0,
        )
    )
    total_expenses = expenses_result.scalar() or Decimal("0")

    # Get income
    income_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.amount > 0,
        )
    )
    total_income = income_result.scalar() or Decimal("0")

    return {
        "income": float(total_income),
        "expenses": abs(float(total_expenses)),
        "net": float(total_income + total_expenses),
    }
