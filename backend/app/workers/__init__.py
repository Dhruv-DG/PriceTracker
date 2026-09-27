"""
Background price tracking worker.
Periodically checks prices for tracked products and stores new observations.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class PriceTracker:
    """Background worker for tracking prices over time."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background tracking loop."""
        if not settings.TRACKING_ENABLED:
            logger.info("Tracking is disabled")
            return

        self._running = True
        self._task = asyncio.create_task(self._tracking_loop())
        logger.info("Price tracker started")

    async def stop(self):
        """Stop the tracking loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Price tracker stopped")

    async def _tracking_loop(self):
        """Main tracking loop."""
        while self._running:
            try:
                await self._run_tracking_cycle()
            except Exception as e:
                logger.error(f"Tracking cycle error: {e}", exc_info=True)

            # Wait for next cycle
            await asyncio.sleep(settings.TRACKING_INTERVAL_MINUTES * 60)

    async def _run_tracking_cycle(self):
        """Execute one tracking cycle."""
        logger.info("Starting tracking cycle")
        
        from sqlalchemy import select, or_, update
        from app.database import async_session
        from app.models.models import TrackingJob, ProductListing, PriceObservation, TrackingStatus, SourceType
        from app.adapters.generic import GenericAdapter
        
        generic_adapter = GenericAdapter()

        try:
            async with async_session() as session:
                # 1. Query the database for active tracking jobs that are due
                now = datetime.utcnow()
                stmt = (
                    select(TrackingJob, ProductListing)
                    .join(ProductListing)
                    .where(
                        TrackingJob.status == TrackingStatus.ACTIVE.value,
                        or_(
                            TrackingJob.next_run == None,
                            TrackingJob.next_run <= now
                        )
                    )
                )
                result = await session.execute(stmt)
                jobs_to_run = result.all()
                
                if not jobs_to_run:
                    logger.info("No tracking jobs due right now.")
                    return
                    
                logger.info(f"Found {len(jobs_to_run)} tracking jobs due.")
                
                # 2. For each job, fetch current price using the adapter
                for job, listing in jobs_to_run:
                    try:
                        logger.info(f"Tracking job {job.id}: fetching {listing.url}")
                        product_data = await generic_adapter.extract_product(listing.url)
                        
                        if product_data and product_data.price:
                            # 3. Store new price observation
                            observation = PriceObservation(
                                listing_id=listing.id,
                                price=product_data.price,
                                mrp=product_data.mrp,
                                shipping=product_data.shipping,
                                effective_price=product_data.effective_price,
                                currency=product_data.currency,
                                source="tracking_worker",
                                source_type=SourceType.OWN_TRACKER.value,
                                provider="serper_extraction",
                                confidence=1.0,
                            )
                            session.add(observation)
                            
                            # 4. Update job status
                            job.last_run = now
                            job.next_run = now + timedelta(minutes=job.frequency_minutes)
                            job.error_count = 0
                            job.last_error = None
                        else:
                            logger.warning(f"Failed to extract price for job {job.id}")
                            job.error_count += 1
                            job.last_error = "Failed to extract price"
                            
                    except Exception as e:
                        logger.error(f"Error in tracking job {job.id}: {e}")
                        job.error_count += 1
                        job.last_error = str(e)
                        
                    # Backoff on consecutive errors
                    if job.error_count > 5:
                        job.status = TrackingStatus.ERROR.value
                        
                await session.commit()
                logger.info(f"tracking_run: completed jobs_processed={len(jobs_to_run)}")
                
        except Exception as e:
            logger.error(f"Tracking cycle failed: {e}", exc_info=True)

# Workers package init
