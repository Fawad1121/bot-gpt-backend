"""
Health check endpoint
"""
from fastapi import APIRouter, HTTPException
from app.services.database import db_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service status and connectivity
    """
    status = {
        "status": "healthy",
        "service": "BOT GPT Backend",
        "version": "1.0.0"
    }
    
    # Check database connection
    try:
        await db_service.client.admin.command('ping')
        status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status["database"] = "disconnected"
        status["status"] = "unhealthy"
    
    # Check LLM service (basic check)
    try:
        from app.services.llm_service import llm_service
        if llm_service.client:
            status["llm"] = "available"
        else:
            status["llm"] = "unavailable"
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        status["llm"] = "unavailable"
    
    if status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=status)
    
    return status
