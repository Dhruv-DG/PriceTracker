"""
Own database historical price provider.
Uses the application's own price_observations table.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.history.base import HistoricalPriceProvider
from app.schemas.schemas import (
    HistoricalPriceResult, HistoricalObservation,
    ConfidenceLevel
)
from app.models.models import PriceObservation, ProductListing, Platform

logger = logging.getLogger(__name__)


class OwnDatabaseProvider(HistoricalPriceProvider):
    """Retrieves historical data from the application's own database."""

    def __init__(self, db_session_factory):
        self._session_factory = db_session_factory

    @property
    def name(self) -> str:
        return "own_tracker"

    @property
    def priority(self) -> int:
        return 50  # Lower priority than external providers

    async def is_available(self) -> bool:
        return True

    async def can_provide(self, platform_domain: str) -> bool:
        """Can always try — data may or may not exist."""
        return True

    async def get_history(
        self,
        product_identifier: str,
        platform_domain: str,
        days: int = 365
    ) -> Optional[HistoricalPriceResult]:
        """Query own database for historical observations."""
        try:
            async with self._session_factory() as session:
                cutoff = datetime.utcnow() - timedelta(days=days)

                # Find listings matching product and platform
                query = (
                    select(PriceObservation)
                    .join(ProductListing)
                    .join(Platform)
                    .where(
                        Platform.domain == platform_domain,
                        PriceObservation.timestamp >= cutoff,
                    )
                )

                # If product_identifier is numeric, use product_id
                if product_identifier.isdigit():
                    query = query.where(ProductListing.product_id == int(product_identifier))

                result = await session.execute(query)
                observations_rows = result.scalars().all()

                if not observations_rows:
                    return None

                observations = [
                    HistoricalObservation(
                        date=obs.timestamp,
                        price=obs.price,
                        currency=obs.currency or "INR",
                        source="own_tracker",
                        source_type="own_tracker",
                        provider="own_tracker",
                        confidence=obs.confidence or 1.0,
                    )
                    for obs in observations_rows
                ]

                observations.sort(key=lambda x: x.date)

                # Determine confidence based on data density
                days_covered = (observations[-1].date - observations[0].date).days if len(observations) > 1 else 0
                if len(observations) > 100 and days_covered > 30:
                    confidence = ConfidenceLevel.HIGH
                elif len(observations) > 10:
                    confidence = ConfidenceLevel.MEDIUM
                else:
                    confidence = ConfidenceLevel.LOW

                return HistoricalPriceResult(
                    provider="own_tracker",
                    platform=platform_domain,
                    platform_domain=platform_domain,
                    product_id=product_identifier,
                    currency="INR",
                    observations=observations,
                    start_date=observations[0].date,
                    end_date=observations[-1].date,
                    observation_count=len(observations),
                    confidence=confidence,
                )

        except Exception as e:
            logger.error(f"Own database history error: {e}")
            return None
