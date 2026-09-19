import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.exceptions import register_exception_handlers
from app.core.security import get_password_hash
from app.models.user import User
from app.services.storage import storage_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Initializing database tables...")
    await init_db()

    # Ensure storage directory exists
    storage_service.base_dir.mkdir(parents=True, exist_ok=True)

    # Seed demo user if database is empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalar_one_or_none()
        if not existing_user:
            logger.info("Seeding default demo user (demo@pragatibharati.edu)...")
            demo_user = User(
                email="demo@pragatibharati.edu",
                hashed_password=get_password_hash("Pragati@123"),
                full_name="Pragati Bharati Evaluator",
                role="admin",
                is_active=True,
            )
            session.add(demo_user)
            await session.commit()
            logger.info("Demo user seeded successfully.")

    yield

    # Shutdown tasks
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


import os
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Mount static assets
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/dashboard", response_class=FileResponse, tags=["Web UI"])
async def dashboard():
    """Serves the Pragati Bharati Document Intelligence Web Dashboard."""
    return FileResponse("app/static/index.html")


@app.get("/", tags=["Root"])
async def root(request: Request):
    """
    Root endpoint: serves the interactive Web Dashboard for browser clients,
    or JSON discovery metadata for API clients.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists("app/static/index.html"):
        return FileResponse("app/static/index.html")

    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "dashboard": "/dashboard",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.API_V1_STR}/health",
        "endpoints": {
            "upload_document": f"{settings.API_V1_STR}/documents/upload",
            "list_documents": f"{settings.API_V1_STR}/documents",
            "global_review_queue": f"{settings.API_V1_STR}/questions/review-queue",
            "token": f"{settings.API_V1_STR}/auth/token",
        },
    }

