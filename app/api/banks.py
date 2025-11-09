from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.bank_connection import BankConnection
from app.models.user import User
from app.utils.encryption import encrypt_token

router = APIRouter(prefix="/banks", tags=["banks"])


@router.post("/connect")
async def connect_bank(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Connect to a bank via OAuth 2.0."""
    try:
        from app.core.config import settings

        access_token = settings.BANKING_API_TOKEN

        bank_connection = BankConnection(
            user_id=current_user.id,
            bank_name="VTB Bank",
            bank_identifier="vtb_sandbox",
            access_token=encrypt_token(access_token),
            refresh_token="",
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(days=365),
            is_active=True,
        )

        db.add(bank_connection)
        await db.commit()
        await db.refresh(bank_connection)

        return {
            "status": "connected",
            "bank_connection_id": bank_connection.id,
            "bank_name": bank_connection.bank_name,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}") from e


@router.get("/connections")
async def get_connections(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user's bank connections."""
    from sqlalchemy import select

    result = await db.execute(
        select(BankConnection).where(BankConnection.user_id == current_user.id)
    )
    connections = result.scalars().all()

    return {
        "connections": [
            {
                "id": conn.id,
                "bank_name": conn.bank_name,
                "bank_identifier": conn.bank_identifier,
                "is_active": conn.is_active,
                "last_synced": conn.last_synced_at.isoformat() if conn.last_synced_at else None,
                "expires_at": conn.expires_at.isoformat() if conn.expires_at else None,
            }
            for conn in connections
        ]
    }


@router.post("/sync/{connection_id}")
async def sync_bank_data(
    connection_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually trigger sync for a bank connection."""
    from app.services.sync_service import sync_bank_connection

    result = await sync_bank_connection(db, current_user.id, connection_id)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Sync failed"))

    return result
