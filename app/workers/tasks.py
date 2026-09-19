import logging
from typing import Optional
from fastapi import BackgroundTasks
from app.core.config import settings
from app.core.database import get_sync_db
from app.services.document_service import document_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.tasks.process_document_task")
def process_document_task(self, document_id: str):
    """Celery background worker task for processing a document."""
    logger.info(f"Celery task started for document {document_id}")
    db = get_sync_db()
    try:
        document_service.process_document(document_id, db)
        return {"status": "SUCCESS", "document_id": document_id}
    except Exception as exc:
        logger.error(f"Celery task failed for document {document_id}: {exc}")
        raise self.retry(exc=exc, countdown=10, max_retries=2)
    finally:
        db.close()


def run_local_processing(document_id: str):
    """Background task executed in-process when Celery is disabled."""
    logger.info(f"In-process background processing started for document {document_id}")
    db = get_sync_db()
    try:
        document_service.process_document(document_id, db)
    except Exception as e:
        logger.error(f"In-process processing failed for document {document_id}: {e}")
    finally:
        db.close()


def dispatch_document_processing(document_id: str, background_tasks: Optional[BackgroundTasks] = None):
    """Dispatches document processing asynchronously via Celery or FastAPI BackgroundTasks."""
    if settings.CELERY_ENABLED:
        try:
            process_document_task.delay(document_id)
            logger.info(f"Dispatched document {document_id} to Celery queue.")
            return
        except Exception as e:
            logger.warning(f"Failed to dispatch to Celery ({e}). Falling back to local background task.")

    if background_tasks:
        background_tasks.add_task(run_local_processing, document_id)
        logger.info(f"Dispatched document {document_id} to FastAPI BackgroundTasks.")
    else:
        # Direct call if neither is provided
        run_local_processing(document_id)
