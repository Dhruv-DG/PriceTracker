"""
Serper.dev search provider — uses Google Search API.
Free tier: 2,500 one-time credits.
"""
import httpx
import logging
from typing import List
from urllib.parse import urlparse

from app.search.base import SearchProvider
from app.schemas.schemas import SearchResultItem
from app.config import settings

logger = logging.getLogger(__name__)


class SerperSearchProvider(SearchProvider):
    """Serper.dev Google Search API provider."""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(self):
        self.api_key = settings.SERPER_API_KEY

    @property
    def name(self) -> str:
        return "serper"

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, num_results: int = 15) -> List[SearchResultItem]:
        """Execute Google search via Serper.dev API."""
        if not self.api_key:
            logger.warning("Serper API key not configured")
            return []

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        # Optimize query for product price discovery
        search_query = f"{query} price buy India"

        payload = {
            "q": search_query,
            "gl": "in",  # India
            "hl": "en",
            "num": num_results,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post(self.BASE_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            results = []

            # Process organic results
            for item in data.get("organic", []):
                url = item.get("link", "")
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.replace("www.", "")

                results.append(SearchResultItem(
                    title=item.get("title", ""),
                    url=url,
                    domain=domain,
                    snippet=item.get("snippet", ""),
                    source="serper",
                    metadata={
                        "position": item.get("position"),
                        "date": item.get("date"),
                    }
                ))

            # Also process shopping results if available
            for item in data.get("shopping", []):
                url = item.get("link", "")
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.replace("www.", "")

                results.append(SearchResultItem(
                    title=item.get("title", ""),
                    url=url,
                    domain=domain,
                    snippet=item.get("source", ""),
                    source="serper_shopping",
                    metadata={
                        "price": item.get("price"),
                        "extracted_price": item.get("price"),
                        "source_store": item.get("source"),
                        "rating": item.get("rating"),
                        "reviews": item.get("ratingCount"),
                        "thumbnail": item.get("imageUrl"),
                    }
                ))

            logger.info(f"Serper search returned {len(results)} results for: {query}")
            return results

        except httpx.TimeoutException:
            logger.error(f"Serper search timeout for: {query}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"Serper HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"Serper search error: {e}")
            return []
