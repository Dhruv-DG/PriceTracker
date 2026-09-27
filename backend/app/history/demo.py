"""
Demo historical price provider.
Generates realistic synthetic historical data for demo mode.
All demo data is clearly labeled.
"""
import random
import math
import logging
from typing import Optional
from datetime import datetime, timedelta

from app.history.base import HistoricalPriceProvider
from app.schemas.schemas import (
    HistoricalPriceResult, HistoricalObservation,
    ConfidenceLevel
)

logger = logging.getLogger(__name__)

# Coverage varies by platform (realistic)
PLATFORM_COVERAGE = {
    "amazon.in": {"days": 365, "provider": "Keepa (Demo)", "confidence": ConfidenceLevel.HIGH},
    "flipkart.com": {"days": 180, "provider": "Own Tracker (Demo)", "confidence": ConfidenceLevel.MEDIUM},
    "croma.com": {"days": 90, "provider": "Own Tracker (Demo)", "confidence": ConfidenceLevel.MEDIUM},
    "reliancedigital.in": {"days": 60, "provider": "Own Tracker (Demo)", "confidence": ConfidenceLevel.LOW},
    "vijaysales.com": {"days": 30, "provider": "Own Tracker (Demo)", "confidence": ConfidenceLevel.LOW},
}


class DemoHistoricalProvider(HistoricalPriceProvider):
    """Generates realistic demo historical data."""

    @property
    def name(self) -> str:
        return "demo"

    @property
    def priority(self) -> int:
        return 200  # Only used in demo mode

    async def is_available(self) -> bool:
        return True

    async def can_provide(self, platform_domain: str) -> bool:
        return True

    async def get_history(
        self,
        product_identifier: str,
        platform_domain: str,
        days: int = 365
    ) -> Optional[HistoricalPriceResult]:
        """Generate synthetic but realistic historical price data."""
        platform_config = PLATFORM_COVERAGE.get(
            platform_domain,
            {"days": 30, "provider": "Demo", "confidence": ConfidenceLevel.LOW}
        )

        actual_days = min(days, platform_config["days"])
        if actual_days <= 0:
            return None

        # Generate price series
        observations = self._generate_price_series(
            product_identifier, platform_domain, actual_days
        )

        if not observations:
            return None

        return HistoricalPriceResult(
            provider=platform_config["provider"],
            platform=platform_domain,
            platform_domain=platform_domain,
            product_id=product_identifier,
            currency="INR",
            observations=observations,
            start_date=observations[0].date,
            end_date=observations[-1].date,
            observation_count=len(observations),
            confidence=platform_config["confidence"],
            is_demo=True,
        )

    def _generate_price_series(
        self, product_id: str, domain: str, days: int
    ) -> list[HistoricalObservation]:
        """Generate a realistic price series with trends and events."""
        # Seed for consistency
        seed = hash(f"{product_id}_{domain}") % 100000
        rng = random.Random(seed)

        # Determine base price from product identifier
        base_price = self._estimate_base_price(product_id)

        # Platform-specific price offset
        platform_offsets = {
            "amazon.in": -0.05,
            "flipkart.com": -0.03,
            "croma.com": 0.02,
            "reliancedigital.in": 0.04,
            "vijaysales.com": 0.01,
        }
        offset = platform_offsets.get(domain, 0)
        platform_base = base_price * (1 + offset)

        observations = []
        now = datetime.utcnow()
        current_price = platform_base

        # Generate daily observations
        for day_offset in range(days, 0, -1):
            date = now - timedelta(days=day_offset)

            # Natural price movement
            daily_change = rng.gauss(0, base_price * 0.005)
            current_price += daily_change

            # Occasional sales events (every ~45 days)
            if rng.random() < 0.022:
                drop = base_price * rng.uniform(0.05, 0.15)
                current_price -= drop

            # Gradual price recovery after drops
            if current_price < platform_base * 0.85:
                current_price += base_price * 0.01

            # Price floor
            current_price = max(current_price, platform_base * 0.75)
            # Price ceiling
            current_price = min(current_price, platform_base * 1.2)

            # Round to realistic price (ends in 9 or 99)
            rounded = round(current_price / 10) * 10 - 1

            # Not every day has an observation (realistic gaps)
            if rng.random() < 0.85:
                observations.append(HistoricalObservation(
                    date=date,
                    price=rounded,
                    currency="INR",
                    source="demo",
                    source_type="demo",
                    provider="demo",
                    confidence=0.9,
                ))

        return observations

    def _estimate_base_price(self, product_id: str) -> float:
        """Estimate a base price from the product name/ID."""
        pid = product_id.lower()

        # Known product categories with typical prices
        if any(w in pid for w in ["iphone 17", "iphone 16"]):
            return 79999
        if any(w in pid for w in ["iphone 15", "iphone 14"]):
            return 59999
        if "galaxy s2" in pid:
            return 74999
        if "wh-1000xm" in pid:
            return 29999
        if "airpods pro" in pid:
            return 24999
        if "macbook" in pid:
            return 114999
        if any(w in pid for w in ["pixel", "oneplus"]):
            return 49999
        if any(w in pid for w in ["ipad"]):
            return 39999

        # Default — hash-based
        h = hash(pid) % 100000
        return 10000 + (h % 90000)
