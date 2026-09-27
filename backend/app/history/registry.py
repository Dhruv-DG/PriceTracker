"""
Historical Provider registry.
Resolves which historical data provider to use for a given platform.
"""
import logging
from typing import Dict, List, Optional
from app.history.base import HistoricalPriceProvider
from app.history.own_database import OwnDatabaseProvider

logger = logging.getLogger(__name__)

class HistoryRegistry:
    def __init__(self):
        self._providers: List[HistoricalPriceProvider] = []
        self._fallback_provider: Optional[HistoricalPriceProvider] = None

    def register(self, provider: HistoricalPriceProvider):
        self._providers.append(provider)
        self._providers.sort(key=lambda p: p.priority)
        logger.info(f"Registered history provider: {provider.name} (Priority {provider.priority})")

    def set_fallback(self, provider: HistoricalPriceProvider):
        self._fallback_provider = provider
        logger.info(f"Set fallback history provider: {provider.name}")

    async def get_provider(self, platform_domain: str) -> HistoricalPriceProvider:
        """Find the best available provider for a domain."""
        for provider in self._providers:
            if await provider.is_available() and await provider.can_provide(platform_domain):
                return provider
        
        if self._fallback_provider and await self._fallback_provider.is_available():
            return self._fallback_provider
            
        raise Exception("No historical provider available (not even fallback).")


history_registry = HistoryRegistry()
