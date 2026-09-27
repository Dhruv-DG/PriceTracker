"""
Search API endpoint.
POST /api/search — the main entry point for the application.
"""
import logging
from fastapi import APIRouter, HTTPException

from app.schemas.schemas import SearchRequest, SearchResponse
from app.services.search_service import SearchOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])

# Create orchestrator instance
orchestrator = SearchOrchestrator()


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute a product price search.
    
    Accepts a natural-language query and returns a complete
    price intelligence dashboard with current prices, historical
    data, analytics, and data provenance.
    """
    logger.info(f"Search request: {request.query}")

    try:
        result = await orchestrator.execute_search(request)
        return result
    except Exception as e:
        logger.error(f"Search endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{search_id}/status", response_model=SearchResponse)
async def get_search_status(search_id: int):
    """
    Get the status of an ongoing or completed search.
    Returns the enriched dashboard when ready.
    """
    try:
        status_res = await orchestrator.get_search_status(search_id)
        if not status_res:
            raise HTTPException(status_code=404, detail="Search not found")
        return status_res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
