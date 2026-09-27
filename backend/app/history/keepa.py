"""
Keepa Historical Price Provider.
Retrieves historical price data from Keepa API for Amazon products.
"""
import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta

from app.config import settings
from app.history.base import HistoricalPriceProvider
from app.schemas.schemas import (
    HistoricalPriceResult, HistoricalObservation, 
    ConfidenceLevel, SourceTypeEnum
)
from app.models.models import ProductListing

logger = logging.getLogger(__name__)

class KeepaProvider(HistoricalPriceProvider):
    """
    Retrieves Amazon price history from the Keepa API.
    """
    
    def __init__(self):
        self.api_key = settings.KEEPA_API_KEY
        self.base_url = "https://api.keepa.com/product"
        self.provider_name = "keepa"
        
    async def can_handle(self, platform_domain: str) -> bool:
        """Keepa primarily handles Amazon domains."""
        return "amazon" in platform_domain.lower() and bool(self.api_key)
        
    def _parse_keepa_time(self, keepa_minutes: int) -> datetime:
        """Convert Keepa time (minutes since Jan 1, 2011) to datetime."""
        base_time = datetime(2011, 1, 1)
        return base_time + timedelta(minutes=keepa_minutes)
        
    def _parse_price_history(self, csv_data: list, currency: str) -> list[HistoricalObservation]:
        """Parse Keepa CSV price history into observations."""
        observations = []
        if not csv_data or len(csv_data) % 2 != 0:
            return observations
            
        for i in range(0, len(csv_data), 2):
            keepa_time = csv_data[i]
            price = csv_data[i+1]
            
            # -1 means out of stock
            if price == -1:
                continue
                
            observations.append(HistoricalObservation(
                date=self._parse_keepa_time(keepa_time),
                price=price / 100.0,  # Keepa returns price in cents/paise
                currency=currency,
                source="Keepa",
                source_type=SourceTypeEnum.EXTERNAL_API.value,
                provider=self.provider_name,
                confidence=ConfidenceLevel.HIGH.value
            ))
            
        return observations
        
    async def get_history(self, listing: ProductListing, platform_name: str, platform_domain: str) -> Optional[HistoricalPriceResult]:
        """Fetch historical prices from Keepa for a listing."""
        if not await self.can_handle(platform_domain):
            return None
            
        # Try to get ASIN from identifiers or external_product_id
        asin = listing.external_product_id
        if not asin:
            logger.warning(f"No ASIN found for listing {listing.id} on {platform_domain}")
            return None
            
        # Determine Keepa domain ID
        domain_id = 1  # default Amazon.com
        domain = platform_domain.lower()
        if "amazon.in" in domain:
            domain_id = 10
        elif "amazon.co.uk" in domain:
            domain_id = 2
        elif "amazon.de" in domain:
            domain_id = 3
        # ... add others if needed
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "key": self.api_key,
                    "domain": domain_id,
                    "asin": asin,
                    "history": 1
                }
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 403:
                    logger.error("Keepa API key invalid or quota exceeded")
                    return None
                    
                response.raise_for_status()
                data = response.json()
                
                if "products" not in data or not data["products"]:
                    return None
                    
                product_data = data["products"][0]
                
                # Keepa returns different price types (csv array index):
                # 0: Amazon, 1: New Marketplace, 2: Used
                # For simplicity, we use Amazon price (0) or New (1) as fallback
                csv = product_data.get("csv", [])
                amazon_csv = csv[0] if len(csv) > 0 else []
                new_csv = csv[1] if len(csv) > 1 else []
                
                # Use Amazon price if available, else New Marketplace
                target_csv = amazon_csv if amazon_csv else new_csv
                currency = "INR" if domain_id == 10 else "USD" # Simplify based on domain
                
                observations = self._parse_price_history(target_csv, currency)
                
                if not observations:
                    return None
                    
                return HistoricalPriceResult(
                    provider=self.provider_name,
                    platform=platform_name,
                    platform_domain=platform_domain,
                    product_id=asin,
                    currency=currency,
                    observations=observations,
                    start_date=observations[0].date if observations else None,
                    end_date=observations[-1].date if observations else None,
                    observation_count=len(observations),
                    confidence=ConfidenceLevel.HIGH,
                    source_url=f"https://keepa.com/#!product/{domain_id}-{asin}",
                    is_demo=False
                )
                
        except Exception as e:
            logger.error(f"Keepa API error for ASIN {asin}: {str(e)}")
            return None
