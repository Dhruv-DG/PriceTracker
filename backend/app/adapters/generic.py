"""
Generic e-commerce adapter.
Extracts product data using JSON-LD structured data and HTML meta tags.
Works as a fallback for any e-commerce site that uses standard markup.
"""
import httpx
import json
import re
import logging
from typing import Optional
from urllib.parse import urlparse

from app.adapters.base import EcommerceAdapter, ExtractedProduct
from app.config import settings

logger = logging.getLogger(__name__)


class GenericAdapter(EcommerceAdapter):
    """
    Generic adapter using structured data extraction.
    Preferred extraction order:
    1. JSON-LD structured data
    2. Open Graph meta tags
    3. HTML meta tags
    """

    def __init__(self, domain: str = "", name: str = "Generic"):
        self._domain = domain
        self._name = name

    @property
    def platform_name(self) -> str:
        return self._name

    @property
    def platform_domain(self) -> str:
        return self._domain

    async def can_handle(self, url: str) -> bool:
        """Generic adapter can attempt to handle any URL."""
        return True

    async def extract_product(self, url: str) -> Optional[ExtractedProduct]:
        """Extract product info from a URL using structured data."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            async with httpx.AsyncClient(
                timeout=settings.REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

            # Try JSON-LD first (most reliable)
            product = self._extract_jsonld(html, url)
            if product:
                return product

            # Try meta tags
            product = self._extract_meta(html, url)
            if product:
                return product

            logger.warning(f"Could not extract product data from: {url}")
            return None

        except httpx.TimeoutException:
            logger.error(f"Timeout extracting from: {url}")
            return None
        except Exception as e:
            logger.error(f"Error extracting from {url}: {e}")
            return None

    def _extract_jsonld(self, html: str, url: str) -> Optional[ExtractedProduct]:
        """Extract from JSON-LD structured data."""
        try:
            # Find all JSON-LD blocks
            pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

            for match in matches:
                try:
                    data = json.loads(match.strip())

                    # Handle @graph wrapper
                    if isinstance(data, dict) and "@graph" in data:
                        items = data["@graph"]
                    elif isinstance(data, list):
                        items = data
                    else:
                        items = [data]

                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        item_type = item.get("@type", "")
                        if isinstance(item_type, list):
                            item_type = item_type[0] if item_type else ""

                        if item_type in ("Product", "IndividualProduct"):
                            return self._parse_jsonld_product(item, url)

                except json.JSONDecodeError:
                    continue

        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")

        return None

    def _parse_jsonld_product(self, data: dict, url: str) -> ExtractedProduct:
        """Parse a JSON-LD Product object."""
        # Extract price from offers
        price = None
        currency = "INR"
        availability = "unknown"
        seller = None

        offers = data.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        if isinstance(offers, dict):
            price = self._parse_price(offers.get("price") or offers.get("lowPrice"))
            currency = offers.get("priceCurrency", "INR")
            avail_url = offers.get("availability", "")
            if "InStock" in avail_url:
                availability = "in_stock"
            elif "OutOfStock" in avail_url:
                availability = "out_of_stock"
            seller_data = offers.get("seller", {})
            if isinstance(seller_data, dict):
                seller = seller_data.get("name")

        brand = None
        brand_data = data.get("brand", {})
        if isinstance(brand_data, dict):
            brand = brand_data.get("name")
        elif isinstance(brand_data, str):
            brand = brand_data

        return ExtractedProduct(
            title=data.get("name", "Unknown Product"),
            price=price,
            currency=currency,
            availability=availability,
            seller=seller,
            brand=brand,
            external_id=data.get("sku") or data.get("gtin13") or data.get("mpn"),
            image_url=data.get("image", [None])[0] if isinstance(data.get("image"), list) else data.get("image"),
            url=url,
            metadata={
                "source": "json-ld",
                "description": (data.get("description") or "")[:500],
            }
        )

    def _extract_meta(self, html: str, url: str) -> Optional[ExtractedProduct]:
        """Extract from Open Graph and standard meta tags."""
        try:
            title = self._get_meta(html, "og:title") or self._get_meta(html, "title") or self._get_title_tag(html)
            price_str = self._get_meta(html, "product:price:amount") or self._get_meta(html, "og:price:amount")
            currency = self._get_meta(html, "product:price:currency") or "INR"

            if not title:
                return None

            price = self._parse_price(price_str) if price_str else None

            return ExtractedProduct(
                title=title,
                price=price,
                currency=currency,
                url=url,
                image_url=self._get_meta(html, "og:image"),
                metadata={"source": "meta-tags"}
            )

        except Exception as e:
            logger.debug(f"Meta extraction failed: {e}")
            return None

    def _get_meta(self, html: str, property_name: str) -> Optional[str]:
        """Get a meta tag value."""
        patterns = [
            rf'<meta[^>]*property=["\']?{re.escape(property_name)}["\']?[^>]*content=["\']([^"\']*)["\']',
            rf'<meta[^>]*content=["\']([^"\']*)["\'][^>]*property=["\']?{re.escape(property_name)}["\']?',
            rf'<meta[^>]*name=["\']?{re.escape(property_name)}["\']?[^>]*content=["\']([^"\']*)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _get_title_tag(self, html: str) -> Optional[str]:
        """Get the page title."""
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _parse_price(self, price_val) -> Optional[float]:
        """Parse a price value to float."""
        if price_val is None:
            return None
        if isinstance(price_val, (int, float)):
            return float(price_val)
        try:
            cleaned = re.sub(r'[^\d.,]', '', str(price_val))
            cleaned = cleaned.replace(',', '')
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
