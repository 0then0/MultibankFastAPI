import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.bank_connection import BankConnection
from app.services.sync_service import sync_bank_connection


async def sync_all_connections():
    """Background task to sync all active connections."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BankConnection).where(
                BankConnection.is_active,
                (BankConnection.last_synced_at is None)
                | (BankConnection.last_synced_at < datetime.now(UTC) - timedelta(hours=1)),
            )
        )

        connections = result.scalars().all()

        for connection in connections:
            try:
                await sync_bank_connection(db, connection.user_id, connection.id)
                print(f"Synced connection {connection.id}")
            except Exception as e:
                print(f"Failed to sync {connection.id}: {e}")


async def start_scheduler():
    """Start background scheduler."""
    while True:
        await sync_all_connections()
        await asyncio.sleep(3600)
