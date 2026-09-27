import re
import logging
from typing import Optional, List
from urllib.parse import urlparse

from app.adapters.base import EcommerceAdapter, ExtractedProduct
from app.adapters.generic import GenericAdapter

logger = logging.getLogger(__name__)

class AmazonAdapter(EcommerceAdapter):
    """Amazon-specific adapter to reliably extract ASINs."""
    
    def __init__(self):
        self._generic = GenericAdapter(name="Amazon", domain="amazon.in")

    @property
    def platform_name(self) -> str:
        return "Amazon"

    @property
    def platform_domain(self) -> str:
        return "amazon.in"

    @property
    def platform_domains(self) -> List[str]:
        return ["amazon.in", "amazon.com", "amazon.co.uk", "amazon.ca"]

    async def can_handle(self, url: str) -> bool:
        return any(domain in url for domain in self.platform_domains)

    async def extract_product(self, url: str) -> Optional[ExtractedProduct]:
        """Extract product info, ensuring ASIN is captured even if price fails."""
        # First try the generic extraction (which might fail due to anti-bot)
        product = await self._generic.extract_product(url)
        
        # Ensure we at least capture the ASIN from the URL
        asin = self._extract_asin_from_url(url)
        
        if product:
            if not product.external_id and asin:
                product.external_id = asin
            return product
            
        # If generic extraction completely failed but we have an ASIN, we can still return a shell
        # so that Keepa (historical provider) can pick it up!
        if asin:
            logger.info(f"Fallback to URL ASIN extraction for {url}: {asin}")
            return ExtractedProduct(
                title=f"Amazon Product ({asin})",  # Shell title
                price=None,
                currency="INR",
                url=url,
                external_id=asin,
                metadata={"source": "url-regex", "platform_name": "Amazon"}
            )
            
        return None

    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from an Amazon URL using common patterns."""
        patterns = [
            r"/(?:dp|gp/product|exec/obidos/ASIN|o/ASIN|as/|p)/([A-Z0-9]{10})(?:[/?]|$)",
            r"([A-Z0-9]{10})(?:[/?]|$)"
        ]
        
        parsed = urlparse(url)
        path = parsed.path
        
        for pattern in patterns:
            match = re.search(pattern, path, re.IGNORECASE)
            if match:
                return match.group(1).upper()
                
        return None
