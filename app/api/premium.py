from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/premium", tags=["premium"])


def require_premium(current_user: User = Depends(get_current_active_user)):
    """Dependency to check if user has premium."""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires premium subscription",
        )
    return current_user


@router.get("/analytics/detailed")
async def get_detailed_analytics(
    current_user: Annotated[User, Depends(require_premium)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get detailed analytics (Premium feature)."""
    from sqlalchemy import func, select

    from app.models.transaction import Transaction

    result = await db.execute(
        select(
            func.date_trunc("month", Transaction.transaction_date).label("month"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(Transaction.user_id == current_user.id)
        .group_by("month")
        .order_by("month")
    )

    monthly_data = []
    for row in result:
        monthly_data.append(
            {
                "month": row.month.isoformat(),
                "total": float(row.total),
                "count": row.count,
            }
        )

    return {
        "type": "detailed_analytics",
        "premium": True,
        "data": monthly_data,
    }


@router.post("/export/pdf")
async def export_to_pdf(
    current_user: Annotated[User, Depends(require_premium)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Export data to PDF (Premium feature)."""
    return {
        "message": "PDF export functionality",
        "premium": True,
        "status": "Feature available for premium users",
    }


@router.get("/forecasts")
async def get_spending_forecast(
    current_user: Annotated[User, Depends(require_premium)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get spending forecast (Premium feature)."""
    from sqlalchemy import func, select

    from app.models.transaction import Transaction

    result = await db.execute(
        select(func.avg(Transaction.amount)).where(
            Transaction.user_id == current_user.id,
            Transaction.amount < 0,
        )
    )

    avg_spending = result.scalar() or 0

    return {
        "type": "forecast",
        "premium": True,
        "average_monthly_spending": abs(float(avg_spending)) * 30,
        "projected_annual": abs(float(avg_spending)) * 365,
    }
