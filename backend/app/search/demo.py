"""
Demo search provider — returns realistic mock results.
Used when no search API key is configured.
"""
import logging
from typing import List, Dict
from app.search.base import SearchProvider
from app.schemas.schemas import SearchResultItem

logger = logging.getLogger(__name__)

# Realistic demo data for common product queries
DEMO_PRODUCTS: Dict[str, List[dict]] = {
    "default": [
        {
            "title": "{query} - Buy Online at Best Price | Amazon.in",
            "url": "https://www.amazon.in/dp/B0DEMO001",
            "domain": "amazon.in",
            "snippet": "Buy {query} online at the best price in India. Free delivery, EMI options available.",
            "metadata": {"source_store": "Amazon", "price": "₹29,999"}
        },
        {
            "title": "{query} Price in India | Flipkart.com",
            "url": "https://www.flipkart.com/product/p/itm/DEMO002",
            "domain": "flipkart.com",
            "snippet": "{query} at best price. Compare prices across sellers on Flipkart.",
            "metadata": {"source_store": "Flipkart", "price": "₹30,499"}
        },
        {
            "title": "Buy {query} Online | Croma",
            "url": "https://www.croma.com/product/DEMO003",
            "domain": "croma.com",
            "snippet": "Shop {query} at Croma. Best deals, no cost EMI, fast delivery.",
            "metadata": {"source_store": "Croma", "price": "₹31,999"}
        },
        {
            "title": "{query} | Reliance Digital",
            "url": "https://www.reliancedigital.in/product/DEMO004",
            "domain": "reliancedigital.in",
            "snippet": "Buy {query} from Reliance Digital. Jio offers, exchange bonus available.",
            "metadata": {"source_store": "Reliance Digital", "price": "₹32,499"}
        },
        {
            "title": "{query} | Vijay Sales",
            "url": "https://www.vijaysales.com/product/DEMO005",
            "domain": "vijaysales.com",
            "snippet": "{query} available at Vijay Sales. Check offers and compare prices.",
            "metadata": {"source_store": "Vijay Sales", "price": "₹31,499"}
        },
    ]
}


class DemoSearchProvider(SearchProvider):
    """Demo search provider with realistic mock data."""

    @property
    def name(self) -> str:
        return "demo"

    async def is_available(self) -> bool:
        return True

    async def search(self, query: str, num_results: int = 15) -> List[SearchResultItem]:
        """Return mock search results based on query."""
        logger.info(f"[DEMO] Search for: {query}")

        templates = DEMO_PRODUCTS.get("default", [])
        results = []

        for template in templates[:num_results]:
            results.append(SearchResultItem(
                title=template["title"].format(query=query),
                url=template["url"],
                domain=template["domain"],
                snippet=template["snippet"].format(query=query),
                source="demo",
                is_product_page=True,
                relevance_score=0.9,
                metadata=template.get("metadata", {})
            ))

        return results
