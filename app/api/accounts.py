from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.account import Account
from app.models.bank_connection import BankConnection
from app.models.user import User

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/aggregated")
async def get_aggregated_accounts(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get aggregated view of all user's accounts across all banks.
    Data is read from local database (synced via /banks/sync).
    """
    # Get all active accounts for user
    result = await db.execute(
        select(Account)
        .where(
            Account.user_id == current_user.id,
            Account.is_active,
        )
        .order_by(Account.created_at.desc())
    )
    accounts = result.scalars().all()

    # Calculate total balance across all banks
    total_balance = sum(acc.balance for acc in accounts if acc.balance)

    # Get bank names for each account
    accounts_with_banks = []
    for account in accounts:
        # Get bank connection details
        bank_result = await db.execute(
            select(BankConnection).where(BankConnection.id == account.bank_connection_id)
        )
        bank = bank_result.scalar_one_or_none()

        accounts_with_banks.append(
            {
                "id": account.id,
                "bank_name": bank.bank_name if bank else "Unknown Bank",
                "bank_identifier": bank.bank_identifier if bank else None,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "account_number": account.account_number,
                "external_account_id": account.external_account_id,
                "currency": account.currency,
                "balance": float(account.balance) if account.balance else 0.0,
                "available_balance": (
                    float(account.available_balance) if account.available_balance else 0.0
                ),
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat(),
            }
        )

    return {
        "total_balance": float(total_balance),
        "currency": "RUB",  # TODO: Handle multi-currency
        "accounts_count": len(accounts),
        "accounts": accounts_with_banks,
    }


@router.get("/by-bank")
async def get_accounts_by_bank(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get accounts grouped by bank.

    Useful for showing separate sections per bank in UI.
    """
    # Get all bank connections
    bank_result = await db.execute(
        select(BankConnection).where(
            BankConnection.user_id == current_user.id,
            BankConnection.is_active,
        )
    )
    banks = bank_result.scalars().all()

    banks_with_accounts = []
    for bank in banks:
        # Get accounts for this bank
        accounts_result = await db.execute(
            select(Account).where(
                Account.bank_connection_id == bank.id,
                Account.is_active,
            )
        )
        accounts = accounts_result.scalars().all()

        # Calculate total for this bank
        bank_total = sum(acc.balance for acc in accounts if acc.balance)

        banks_with_accounts.append(
            {
                "bank_id": bank.id,
                "bank_name": bank.bank_name,
                "bank_identifier": bank.bank_identifier,
                "total_balance": float(bank_total),
                "accounts_count": len(accounts),
                "last_synced": bank.last_synced_at.isoformat() if bank.last_synced_at else None,
                "accounts": [
                    {
                        "id": acc.id,
                        "account_name": acc.account_name,
                        "account_type": acc.account_type,
                        "currency": acc.currency,
                        "balance": float(acc.balance) if acc.balance else 0.0,
                        "external_account_id": acc.external_account_id,
                    }
                    for acc in accounts
                ],
            }
        )

    return {
        "banks": banks_with_accounts,
        "total_banks": len(banks_with_accounts),
    }


@router.get("/{account_id}")
async def get_account_details(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get detailed information about specific account.

    Returns account from local database, not from VTB API directly.
    For real-time data, trigger sync first: POST /banks/sync/{connection_id}
    """
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get bank connection details
    bank_result = await db.execute(
        select(BankConnection).where(BankConnection.id == account.bank_connection_id)
    )
    bank = bank_result.scalar_one_or_none()

    return {
        "id": account.id,
        "bank_name": bank.bank_name if bank else "Unknown",
        "bank_identifier": bank.bank_identifier if bank else None,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "account_number": account.account_number,
        "external_account_id": account.external_account_id,
        "currency": account.currency,
        "balance": float(account.balance) if account.balance else 0.0,
        "available_balance": (
            float(account.available_balance) if account.available_balance else 0.0
        ),
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
        "last_synced": bank.last_synced_at.isoformat() if bank and bank.last_synced_at else None,
    }


@router.get("/stats/summary")
async def get_accounts_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get summary statistics of user's accounts.

    Useful for dashboard widgets.
    """
    # Total accounts and balance
    result = await db.execute(
        select(
            func.count(Account.id).label("total_accounts"),
            func.sum(Account.balance).label("total_balance"),
        ).where(
            Account.user_id == current_user.id,
            Account.is_active,
        )
    )
    stats = result.one()

    # Count by account type
    type_result = await db.execute(
        select(
            Account.account_type,
            func.count(Account.id).label("count"),
            func.sum(Account.balance).label("total"),
        )
        .where(
            Account.user_id == current_user.id,
            Account.is_active,
        )
        .group_by(Account.account_type)
    )
    by_type = type_result.all()

    # Count by currency
    currency_result = await db.execute(
        select(
            Account.currency,
            func.count(Account.id).label("count"),
            func.sum(Account.balance).label("total"),
        )
        .where(
            Account.user_id == current_user.id,
            Account.is_active,
        )
        .group_by(Account.currency)
    )
    by_currency = currency_result.all()

    # Count by bank
    bank_result = await db.execute(
        select(
            BankConnection.bank_name,
            func.count(Account.id).label("count"),
            func.sum(Account.balance).label("total"),
        )
        .join(Account, Account.bank_connection_id == BankConnection.id)
        .where(
            Account.user_id == current_user.id,
            Account.is_active,
        )
        .group_by(BankConnection.bank_name)
    )
    by_bank = bank_result.all()

    return {
        "summary": {
            "total_accounts": stats.total_accounts or 0,
            "total_balance": float(stats.total_balance or 0),
        },
        "by_type": [
            {
                "type": row.account_type,
                "count": row.count,
                "total": float(row.total or 0),
            }
            for row in by_type
        ],
        "by_currency": [
            {
                "currency": row.currency,
                "count": row.count,
                "total": float(row.total or 0),
            }
            for row in by_currency
        ],
        "by_bank": [
            {
                "bank": row.bank_name,
                "count": row.count,
                "total": float(row.total or 0),
            }
            for row in by_bank
        ],
    }


@router.post("/{account_id}/refresh")
async def refresh_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Refresh specific account data from bank API.

    Triggers re-sync for the bank connection that owns this account.
    """
    # Get account
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get bank connection
    bank_result = await db.execute(
        select(BankConnection).where(BankConnection.id == account.bank_connection_id)
    )
    bank = bank_result.scalar_one_or_none()

    if not bank:
        raise HTTPException(status_code=404, detail="Bank connection not found")

    # Trigger sync
    from app.services.sync_service import sync_bank_connection

    sync_result = await sync_bank_connection(db, current_user.id, bank.id)

    if sync_result.get("status") == "success":
        return {
            "status": "success",
            "message": "Account refreshed successfully",
            "synced": sync_result.get("synced"),
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh account: {sync_result.get('message')}",
        )
