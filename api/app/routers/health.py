"""
Health check router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import logging

from app.database import get_db
from app.services.storage import StorageService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "resume-rewriter-api"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "resume-rewriter-api",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check storage service
    try:
        storage_service = StorageService()
        await storage_service.ensure_bucket_exists()
        health_status["checks"]["storage"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        health_status["checks"]["storage"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check NLP models (basic check)
    try:
        import spacy
        # Don't load the full model in health check, just verify it's available
        spacy.util.find_package("en_core_web_sm")
        health_status["checks"]["nlp"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"NLP health check failed: {e}")
        health_status["checks"]["nlp"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status
