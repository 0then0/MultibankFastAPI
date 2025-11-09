# Multibank Aggregator

Мультибанковское финансовое приложение для агрегации счетов и карт из разных банков через Open Banking API.

## Возможности

- Агрегация счетов и карт из разных банков
- Единый просмотр балансов
- История транзакций с категоризацией
- Безопасное хранение токенов OAuth
- Аналитика расходов и доходов
- Система уведомлений
- Premium функции

## Технологический стек

- **Backend**: FastAPI, Python 3.13+
- **Database**: PostgreSQL с asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Authentication**: JWT (python-jose)
- **Package Manager**: uv
- **Linter/Formatter**: ruff

## Установка и запуск

### Требования

- Python 3.13+
- PostgreSQL 14+
- uv

### Настройка проекта

1. Клонируйте репозиторий:

```bash
git clone https://github.com/0then0/MultibankFastAPI
cd MultibankFastAPI
```

2. Создайте виртуальное окружение и установите зависимости:

```bash
uv sync
```

3. Скопируйте `.env.example` в `.env` и настройте переменные окружения:

```bash
cp .env.example .env
```

4. Отредактируйте `.env` файл:
   - Установите `SECRET_KEY` (минимум 32 символа)
   - Настройте параметры PostgreSQL
   - Добавьте `BANKING_API_CLIENT_ID` и `BANKING_API_CLIENT_SECRET`

### Настройка базы данных

1. Создайте базу данных PostgreSQL:

```bash
createdb multibank
```

2. Примените миграции:

```bash
uv run alembic upgrade head
```

### Запуск приложения

```bash
# Windows
run.bat

# Linux/macOS
./run.sh

# Или напрямую
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: http://localhost:8000

Документация API (Swagger): http://localhost:8000/docs

Frontend: http://localhost:8000/static/index.html

## Разработка

### Создание новой миграции

```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций

```bash
uv run alembic upgrade head
```

### Откат миграции

```bash
uv run alembic downgrade -1
```

### Форматирование кода

```bash
uv run ruff format .
```

### Проверка кода

```bash
uv run ruff check .
```

### Автоматическое исправление

```bash
uv run ruff check --fix .
```

### Запуск тестов

```bash
uv run pytest
```
