"""
Скрипт для заполнения БД тестовыми данными.
Запуск: uv run python seed_data.py
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.account import Account
from app.models.bank_connection import BankConnection
from app.models.card import Card
from app.models.transaction import Transaction
from app.models.user import User
from app.utils.encryption import encrypt_token


async def seed_database():
    """Заполнить БД тестовыми данными."""
    async with AsyncSessionLocal() as db:
        # Создать тестового пользователя
        user = User(
            email="demo@multibank.ru",
            hashed_password=get_password_hash("demo123"),
            full_name="Демо Пользователь",
            is_active=True,
            is_premium=False,
        )
        db.add(user)
        await db.flush()

        # Создать подключение к банку
        bank_conn = BankConnection(
            user_id=user.id,
            bank_name="Test Bank",
            bank_identifier="vtb_test",
            access_token=encrypt_token("test_access_token"),
            refresh_token=encrypt_token("test_refresh_token"),
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            is_active=True,
        )
        db.add(bank_conn)
        await db.flush()

        # Создать счета
        account1 = Account(
            user_id=user.id,
            bank_connection_id=bank_conn.id,
            external_account_id="ACC001",
            account_number="40817810123456789012",
            account_type="Текущий счет",
            account_name="Основной счет",
            currency="RUB",
            balance=Decimal("150000.00"),
            available_balance=Decimal("150000.00"),
            is_active=True,
        )
        db.add(account1)

        account2 = Account(
            user_id=user.id,
            bank_connection_id=bank_conn.id,
            external_account_id="ACC002",
            account_number="40817810987654321098",
            account_type="Сберегательный счет",
            account_name="Накопительный счет",
            currency="RUB",
            balance=Decimal("500000.00"),
            available_balance=Decimal("500000.00"),
            is_active=True,
        )
        db.add(account2)
        await db.flush()

        # Создать карты
        card1 = Card(
            user_id=user.id,
            account_id=account1.id,
            external_card_id="CARD001",
            card_number_masked="•••• 4242",
            card_type="Debit",
            card_brand="Visa",
            card_holder_name="DEMO USER",
            expiry_date="12/2027",
            is_active=True,
            is_blocked=False,
        )
        db.add(card1)

        card2 = Card(
            user_id=user.id,
            account_id=account2.id,
            external_card_id="CARD002",
            card_number_masked="•••• 5555",
            card_type="Credit",
            card_brand="Mastercard",
            card_holder_name="DEMO USER",
            expiry_date="06/2026",
            is_active=True,
            is_blocked=False,
        )
        db.add(card2)
        await db.flush()

        # Создать транзакции
        transactions = [
            # Расходы
            Transaction(
                user_id=user.id,
                account_id=account1.id,
                external_transaction_id="TX001",
                transaction_date=datetime.now(UTC) - timedelta(days=1),
                amount=Decimal("-1500.00"),
                currency="RUB",
                transaction_type="purchase",
                description="Покупка продуктов",
                merchant_name="Пятёрочка",
                merchant_category="Супермаркеты",
                category="Продукты",
                balance_after=Decimal("148500.00"),
            ),
            Transaction(
                user_id=user.id,
                account_id=account1.id,
                external_transaction_id="TX002",
                transaction_date=datetime.now(UTC) - timedelta(days=2),
                amount=Decimal("-5000.00"),
                currency="RUB",
                transaction_type="purchase",
                description="Оплата интернета",
                merchant_name="Ростелеком",
                merchant_category="Связь",
                category="Коммунальные услуги",
                balance_after=Decimal("143500.00"),
            ),
            Transaction(
                user_id=user.id,
                account_id=account1.id,
                external_transaction_id="TX003",
                transaction_date=datetime.now(UTC) - timedelta(days=3),
                amount=Decimal("-3000.00"),
                currency="RUB",
                transaction_type="purchase",
                description="Такси",
                merchant_name="Яндекс.Такси",
                merchant_category="Транспорт",
                category="Транспорт",
                balance_after=Decimal("140500.00"),
            ),
            # Доходы
            Transaction(
                user_id=user.id,
                account_id=account1.id,
                external_transaction_id="TX004",
                transaction_date=datetime.now(UTC) - timedelta(days=5),
                amount=Decimal("100000.00"),
                currency="RUB",
                transaction_type="transfer",
                description="Зарплата",
                merchant_name="ООО Компания",
                category="Зарплата",
                balance_after=Decimal("240500.00"),
            ),
            Transaction(
                user_id=user.id,
                account_id=account2.id,
                external_transaction_id="TX005",
                transaction_date=datetime.now(UTC) - timedelta(days=10),
                amount=Decimal("500000.00"),
                currency="RUB",
                transaction_type="transfer",
                description="Перевод на накопительный счет",
                category="Сбережения",
                balance_after=Decimal("500000.00"),
            ),
        ]

        for tx in transactions:
            db.add(tx)

        await db.commit()
        print("✓ База данных успешно заполнена тестовыми данными!")
        print("✓ Демо-пользователь: demo@multibank.ru / demo123")
        print("✓ Создано счетов: 2")
        print("✓ Создано карт: 2")
        print(f"✓ Создано транзакций: {len(transactions)}")


if __name__ == "__main__":
    asyncio.run(seed_database())
