from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import accounts, analytics, auth, banks, cards, premium, transactions
from app.core.config import settings
from app.services.banking_api import close_banking_api_client, init_banking_api_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_banking_api_client(
        base_url=settings.BANKING_API_BASE_URL,
        client_id=settings.BANKING_API_CLIENT_ID,
        client_secret=settings.BANKING_API_CLIENT_SECRET,
    )
    print("Banking API client initialized")

    yield

    # Shutdown
    await close_banking_api_client()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # Static directory doesn't exist yet

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(accounts.router, prefix=settings.API_V1_STR)
app.include_router(cards.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(banks.router, prefix=settings.API_V1_STR)
app.include_router(premium.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Multibank Aggregator API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
