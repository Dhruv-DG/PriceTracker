"""
Tracking API endpoints.
"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.post("")
async def start_tracking(product_id: int, frequency_minutes: int = 360):
    """Start tracking a product."""
    return {
        "status": "tracking_started",
        "product_id": product_id,
        "frequency_minutes": frequency_minutes,
        "message": "Tracking will begin in the next cycle"
    }


@router.get("")
async def list_tracking_jobs():
    """List all active tracking jobs."""
    return {"jobs": [], "total": 0}


@router.delete("/{job_id}")
async def stop_tracking(job_id: int):
    """Stop tracking a product."""
    return {"status": "stopped", "job_id": job_id}
