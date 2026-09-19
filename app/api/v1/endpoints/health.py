from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.services.extraction.gemini_extractor import GeminiExtractor
from app.services.storage import storage_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive service health check covering database, storage, Redis, and AI engine status."""
    health_data = {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "HEALTHY",
        "components": {}
    }

    # 1. Database check
    try:
        await db.execute(text("SELECT 1"))
        health_data["components"]["database"] = {"status": "UP", "url_scheme": settings.DATABASE_URL.split(":")[0]}
    except Exception as e:
        health_data["components"]["database"] = {"status": "DOWN", "error": str(e)}
        health_data["status"] = "DEGRADED"

    # 2. Redis check
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.ping()
            health_data["components"]["redis"] = {"status": "UP"}
        except Exception as e:
            health_data["components"]["redis"] = {"status": "DOWN", "error": str(e)}
    else:
        health_data["components"]["redis"] = {"status": "NOT_CONNECTED", "celery_enabled": settings.CELERY_ENABLED}

    # 3. Storage directory check
    try:
        storage_exists = storage_service.base_dir.exists()
        health_data["components"]["storage"] = {
            "status": "UP" if storage_exists else "DOWN",
            "path": str(storage_service.base_dir)
        }
    except Exception as e:
        health_data["components"]["storage"] = {"status": "DOWN", "error": str(e)}
        health_data["status"] = "DEGRADED"

    # 4. AI Engine check
    gemini_extractor = GeminiExtractor()
    health_data["components"]["gemini_ai"] = {
        "configured": gemini_extractor.is_available(),
        "model": settings.GEMINI_MODEL,
        "fallback_engine": "RuleBasedDocumentExtractor"
    }

    return health_data
