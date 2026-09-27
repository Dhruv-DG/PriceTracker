"""
Adapter registry — deterministic domain-to-adapter resolution.
No LLM required for routing.
"""
import logging
from typing import Optional, Dict, List
from urllib.parse import urlparse

from app.adapters.base import EcommerceAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Registry that maps normalized domains to their adapters.
    Resolution is deterministic — no LLM needed.
    """

    def __init__(self):
        self._adapters: Dict[str, EcommerceAdapter] = {}
        self._fallback: Optional[EcommerceAdapter] = None

    def register(self, adapter: EcommerceAdapter):
        """Register an adapter for its domains."""
        for domain in adapter.platform_domains:
            normalized = self._normalize_domain(domain)
            self._adapters[normalized] = adapter
            logger.info(f"Registered adapter: {normalized} → {adapter.platform_name}")

    def set_fallback(self, adapter: EcommerceAdapter):
        """Set a fallback adapter for unregistered domains."""
        self._fallback = adapter
        logger.info(f"Set fallback adapter: {adapter.platform_name}")

    def get_adapter(self, url: str) -> Optional[EcommerceAdapter]:
        """Get the adapter for a URL by domain lookup."""
        domain = self._extract_domain(url)
        normalized = self._normalize_domain(domain)

        # Try exact match
        if normalized in self._adapters:
            return self._adapters[normalized]

        # Try parent domain (e.g., "store.amazon.in" → "amazon.in")
        parts = normalized.split(".")
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self._adapters:
                return self._adapters[parent]

        # Return fallback
        if self._fallback:
            logger.debug(f"Using fallback adapter for: {domain}")
            return self._fallback

        logger.warning(f"No adapter found for: {domain}")
        return None

    def get_all_adapters(self) -> List[EcommerceAdapter]:
        """Get all unique registered adapters."""
        seen = set()
        adapters = []
        for adapter in self._adapters.values():
            if adapter.platform_name not in seen:
                seen.add(adapter.platform_name)
                adapters.append(adapter)
        return adapters

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url

    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain: remove www., lowercase."""
        domain = domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain


# Global registry instance
adapter_registry = AdapterRegistry()
