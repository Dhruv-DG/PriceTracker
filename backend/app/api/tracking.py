"""
Tracking API endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.models import TrackingJob, ProductListing, Product, Platform, TrackingStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.post("")
async def start_tracking(product_name: str, frequency_minutes: int = 360, db: AsyncSession = Depends(get_db)):
    """Start tracking all listings for a product by its canonical name."""
    # Find all listings for this product
    stmt = select(ProductListing).join(Product).where(Product.canonical_name == product_name)
    result = await db.execute(stmt)
    listings = result.scalars().all()
    
    if not listings:
        raise HTTPException(status_code=404, detail="Product or listings not found. Search for it first so it is saved in the database.")
        
    jobs_created = 0
    for listing in listings:
        # Check if already tracking
        stmt = select(TrackingJob).where(TrackingJob.listing_id == listing.id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        
        if existing:
            existing.status = TrackingStatus.ACTIVE.value
            existing.frequency_minutes = frequency_minutes
        else:
            job = TrackingJob(
                listing_id=listing.id,
                frequency_minutes=frequency_minutes
            )
            db.add(job)
            jobs_created += 1
            
    await db.commit()
    return {
        "status": "tracking_started",
        "product_name": product_name,
        "jobs_created_or_updated": len(listings),
        "frequency_minutes": frequency_minutes,
        "message": "Tracking will begin in the next cycle"
    }


@router.get("")
async def list_tracking_jobs(db: AsyncSession = Depends(get_db)):
    """List all active tracking jobs."""
    stmt = (
        select(TrackingJob, ProductListing, Product, Platform)
        .join(ProductListing)
        .join(Product)
        .join(Platform)
        .where(TrackingJob.status == TrackingStatus.ACTIVE.value)
    )
    result = await db.execute(stmt)
    
    jobs = []
    for job, listing, product, platform in result:
        jobs.append({
            "job_id": job.id,
            "product_name": product.canonical_name,
            "platform": platform.name,
            "url": listing.url,
            "frequency_minutes": job.frequency_minutes,
            "last_run": job.last_run,
            "next_run": job.next_run,
        })
        
    return {"jobs": jobs, "total": len(jobs)}


@router.delete("/{job_id}")
async def stop_tracking(job_id: int, db: AsyncSession = Depends(get_db)):
    """Stop tracking a product listing."""
    stmt = select(TrackingJob).where(TrackingJob.id == job_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job.status = TrackingStatus.PAUSED.value
    await db.commit()
    
    return {"status": "stopped", "job_id": job_id}
