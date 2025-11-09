from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.bank_connection import BankConnection
from app.models.transaction import Transaction
from app.services.banking_api import get_banking_api_client
from app.utils.encryption import decrypt_token

TEST_CLIENT_ID = "team073-1"


async def sync_bank_connection(db: AsyncSession, user_id: int, connection_id: int) -> dict:
    """
    Sync data from Virtual Bank API to local database.
    """
    # Get bank connection
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.user_id == user_id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return {"error": "Connection not found"}

    access_token = decrypt_token(connection.access_token)
    banking_api = get_banking_api_client()

    synced_counts = {
        "accounts": 0,
        "cards": 0,
        "transactions": 0,
    }

    try:
        # STEP 1: Create consent
        print(f"Creating consent for client_id={TEST_CLIENT_ID}...")
        consent_response = await banking_api.create_consent(
            access_token=access_token,
            client_id=TEST_CLIENT_ID,
            permissions=["ReadAccountsDetail", "ReadBalances", "ReadTransactionsDetail"],
        )

        consent_id = (
            consent_response.get("consent_id")
            or consent_response.get("consentId")
            or consent_response.get("data", {}).get("consent_id")
        )
        if not consent_id:
            return {
                "status": "error",
                "message": f"Failed to create consent: {consent_response}",
            }
        print(f"✅ Consent created: {consent_id}")

        # STEP 2: Fetch accounts
        print(f"Fetching accounts with consent_id={consent_id}...")
        accounts_response = await banking_api.get_accounts(
            access_token=access_token,
            client_id=TEST_CLIENT_ID,
            consent_id=consent_id,
        )

        accounts_data = accounts_response.get("data", {}).get("account", [])
        print(f"✅ Found {len(accounts_data)} accounts")

        for acc_data in accounts_data[:10]:  # Limit for demo
            account_id = acc_data.get("accountId")
            if not account_id:
                print(f"⚠️ Skipping account without accountId: {acc_data}")
                continue

            # Check if account already exists
            existing = await db.execute(
                select(Account).where(Account.external_account_id == account_id)
            )

            if existing.scalar_one_or_none():
                print(f"ℹ️ Account {account_id} already exists, skipping")
                continue

            # STEP 3: Get balance for this account
            balance = Decimal("0.00")
            try:
                balance_response = await banking_api.get_balances(
                    access_token=access_token,
                    account_id=account_id,
                    client_id=TEST_CLIENT_ID,
                    consent_id=consent_id,
                )

                balances = balance_response.get("data", {}).get("balance", [])
                if balances:
                    balance_data = balances[0]
                    amount = balance_data.get("amount", {})
                    balance = Decimal(str(amount.get("amount", "0")))
                    print(f"✅ Balance for {account_id}: {balance}")

            except Exception as e:
                print(f"⚠️ Failed to get balance for {account_id}: {e}")

            new_account = Account(
                user_id=user_id,
                bank_connection_id=connection.id,
                external_account_id=account_id,
                account_type=acc_data.get("accountType", "Personal"),
                account_name=acc_data.get("nickname"),
                account_number=None,
                currency=acc_data.get("currency", "RUB"),
                balance=balance,
                is_active=acc_data.get("status") == "Enabled",
            )
            db.add(new_account)

            await db.flush()

            synced_counts["accounts"] += 1
            print(f"✅ Created account: {account_id} with id={new_account.id}")

            # STEP 4: Fetch transactions for this account
            try:
                transactions_response = await banking_api.get_transactions(
                    access_token=access_token,
                    account_id=account_id,
                    client_id=TEST_CLIENT_ID,
                    consent_id=consent_id,
                )

                transactions_data = transactions_response.get("data", {}).get("transaction", [])
                print(f"✅ Found {len(transactions_data)} transactions for {account_id}")

                for tx_data in transactions_data[:50]:  # Limit per account
                    tx_id = tx_data.get("transactionId")
                    if not tx_id:
                        continue

                    # Check if transaction already exists
                    existing_tx = await db.execute(
                        select(Transaction).where(Transaction.external_transaction_id == tx_id)
                    )
                    if existing_tx.scalar_one_or_none():
                        continue

                    # Parse transaction data
                    amount_data = tx_data.get("amount", {})
                    amount = Decimal(str(amount_data.get("amount", "0")))
                    currency = amount_data.get("currency", "RUB")

                    # Parse date with specific exception types
                    tx_date_str = tx_data.get("bookingDateTime") or tx_data.get("valueDateTime")
                    try:
                        tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        tx_date = datetime.now(UTC)

                    # Determine transaction type
                    credit_debit = tx_data.get("creditDebitIndicator", "Debit")
                    tx_type = "income" if credit_debit == "Credit" else "expense"

                    new_transaction = Transaction(
                        account_id=new_account.id,
                        external_transaction_id=tx_id,
                        amount=amount,
                        currency=currency,
                        transaction_type=tx_type,
                        description=tx_data.get("transactionInformation", ""),
                        category=_categorize_transaction(tx_data.get("transactionInformation", "")),
                        transaction_date=tx_date,
                        status=tx_data.get("status", "Booked"),
                    )
                    db.add(new_transaction)
                    synced_counts["transactions"] += 1

            except Exception as e:
                print(f"⚠️ Failed to get transactions for {account_id}: {e}")

        # Update connection's last_synced_at
        connection.last_synced_at = datetime.now(UTC)

        await db.commit()
        print(f"✅ Sync complete: {synced_counts}")

        return {
            "status": "success",
            "synced": synced_counts,
            "consent_id": consent_id,
            "client_id": TEST_CLIENT_ID,
        }

    except Exception as e:
        await db.rollback()
        print(f"❌ Sync failed: {e}")
        import traceback

        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "synced": synced_counts,
        }


def _categorize_transaction(description: str) -> str:
    """Simple transaction categorization based on description."""
    if not description:
        return "other"

    description_lower = description.lower()

    if any(word in description_lower for word in ["супермаркет", "продукты", "магазин"]):
        return "groceries"
    if any(word in description_lower for word in ["ресторан", "кафе", "бар"]):
        return "dining"
    if any(word in description_lower for word in ["транспорт", "такси", "метро"]):
        return "transport"
    if any(word in description_lower for word in ["аптека", "врач", "клиника"]):
        return "healthcare"
    if any(word in description_lower for word in ["кино", "театр", "развлечения"]):
        return "entertainment"

    return "other"
