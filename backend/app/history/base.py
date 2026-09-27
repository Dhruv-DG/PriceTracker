"""
Abstract base class for historical price providers.
"""
from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.schemas import HistoricalPriceResult


class HistoricalPriceProvider(ABC):
    """Interface for historical price data providers."""

    @abstractmethod
    async def get_history(
        self,
        product_identifier: str,
        platform_domain: str,
        days: int = 365
    ) -> Optional[HistoricalPriceResult]:
        """
        Get historical price data for a product on a platform.
        
        Args:
            product_identifier: Product ID (ASIN, canonical name, etc.)
            platform_domain: E-commerce platform domain
            days: Number of days of history to retrieve
            
        Returns:
            HistoricalPriceResult with observations, or None if unavailable
        """
        ...

    @abstractmethod
    async def can_provide(self, platform_domain: str) -> bool:
        """Check if this provider can supply history for a platform."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this provider is available and configured."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for provenance tracking."""
        ...

    @property
    def priority(self) -> int:
        """Priority order (lower = higher priority)."""
        return 100
