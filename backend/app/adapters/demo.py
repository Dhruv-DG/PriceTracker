"""
Demo e-commerce adapter — returns realistic mock pricing data.
Used when DEMO_MODE is enabled or when real extraction fails.
"""
import random
import logging
from typing import Optional, Dict, List
from app.adapters.base import EcommerceAdapter, ExtractedProduct

logger = logging.getLogger(__name__)


# Realistic price ranges by platform for demo mode
DEMO_PLATFORMS = {
    "amazon.in": {
        "name": "Amazon",
        "base_discount": 0.08,  # typically 8% lower
        "price_variance": 0.03,
        "seller": "RetailNet (Amazon Fulfilled)",
        "fulfilled_by": "Amazon",
        "availability": "in_stock",
    },
    "flipkart.com": {
        "name": "Flipkart",
        "base_discount": 0.06,
        "price_variance": 0.04,
        "seller": "SuperComNet",
        "fulfilled_by": "Flipkart",
        "availability": "in_stock",
    },
    "croma.com": {
        "name": "Croma",
        "base_discount": 0.02,
        "price_variance": 0.02,
        "seller": "Croma (Tata)",
        "fulfilled_by": "Croma",
        "availability": "in_stock",
    },
    "reliancedigital.in": {
        "name": "Reliance Digital",
        "base_discount": 0.01,
        "price_variance": 0.03,
        "seller": "Reliance Retail",
        "fulfilled_by": "Reliance Digital",
        "availability": "in_stock",
    },
    "vijaysales.com": {
        "name": "Vijay Sales",
        "base_discount": 0.04,
        "price_variance": 0.02,
        "seller": "Vijay Sales",
        "fulfilled_by": "Vijay Sales",
        "availability": "in_stock",
    },
}

# Base MRP ranges for product categories (for generating realistic prices)
CATEGORY_PRICES = {
    "phone": (15000, 150000),
    "headphone": (5000, 40000),
    "laptop": (40000, 250000),
    "tablet": (15000, 100000),
    "tv": (15000, 300000),
    "default": (5000, 80000),
}


def _detect_category(query: str) -> str:
    """Simple category detection from query."""
    q = query.lower()
    if any(w in q for w in ["iphone", "galaxy", "pixel", "phone", "mobile"]):
        return "phone"
    if any(w in q for w in ["headphone", "earphone", "earbud", "wh-1000", "airpod"]):
        return "headphone"
    if any(w in q for w in ["macbook", "laptop", "thinkpad", "zenbook"]):
        return "laptop"
    if any(w in q for w in ["ipad", "tab", "tablet"]):
        return "tablet"
    if any(w in q for w in ["tv", "television", "bravia"]):
        return "tv"
    return "default"


def _get_known_base_price(query: str) -> int:
    """Get realistic base prices for well-known products."""
    q = query.lower().strip()
    known = {
        "iphone 17": 79999, "iphone 16": 69999, "iphone 15": 59999,
        "galaxy s26": 124999, "galaxy s25": 109999, "galaxy s24": 79999,
        "wh-1000xm6": 29999, "wh-1000xm5": 24999, "wh-1000xm4": 19999,
        "airpods pro": 24999, "airpods max": 59999, "airpods 4": 14999,
        "macbook air m4": 114999, "macbook air m3": 99999, "macbook pro": 169999,
        "pixel 9": 79999, "pixel 8": 49999, "oneplus 14": 49999,
        "ipad air": 59999, "ipad pro": 99999,
        "air max 270": 12999, "air max 90": 11999,
    }
    for key, price in known.items():
        if key in q:
            return price
    return 0


def _generate_demo_price(query: str, domain: str) -> float:
    """Generate a realistic demo price based on product and platform."""
    # Try known product first
    base_mrp = _get_known_base_price(query)

    if not base_mrp:
        category = _detect_category(query)
        low, high = CATEGORY_PRICES[category]
        # Use query hash for consistent prices
        seed = hash(query.lower().strip()) % 10000
        random.seed(seed)
        base_mrp = random.randint(low, high)
        base_mrp = round(base_mrp / 500) * 500  # Round to nearest 500

    platform_info = DEMO_PLATFORMS.get(domain, DEMO_PLATFORMS["amazon.in"])
    discount = platform_info["base_discount"]
    variance = platform_info["price_variance"]

    # Each platform has slightly different pricing
    platform_seed = hash(f"{query}_{domain}") % 10000
    random.seed(platform_seed)
    price_factor = 1.0 - discount + random.uniform(-variance, variance)
    price = base_mrp * price_factor
    price = round(price / 10) * 10 - 1  # e.g., 29,999

    random.seed()  # Reset random seed
    return max(price, 1999)


class DemoAdapter(EcommerceAdapter):
    """Demo adapter returning realistic mock data."""

    def __init__(self, domain: str = "", name: str = "Demo"):
        self._domain = domain
        self._name = name

    @property
    def platform_name(self) -> str:
        return self._name

    @property
    def platform_domain(self) -> str:
        return self._domain

    @property
    def platform_domains(self) -> list[str]:
        return list(DEMO_PLATFORMS.keys())

    async def can_handle(self, url: str) -> bool:
        return True

    async def extract_product(self, url: str) -> Optional[ExtractedProduct]:
        """Generate realistic demo product data."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")

        platform_info = DEMO_PLATFORMS.get(domain, {
            "name": "Unknown Store",
            "base_discount": 0.05,
            "price_variance": 0.03,
            "seller": "Unknown Seller",
            "fulfilled_by": "Store",
            "availability": "in_stock",
        })

        return None  # Price will be set by the demo orchestrator

    def generate_for_query(self, query: str, domain: str, url: str) -> ExtractedProduct:
        """Generate demo product data for a specific query and platform."""
        platform_info = DEMO_PLATFORMS.get(domain, DEMO_PLATFORMS["amazon.in"])
        price = _generate_demo_price(query, domain)
        mrp = round(price * 1.15 / 100) * 100 - 1  # MRP ~15% higher

        return ExtractedProduct(
            title=f"{query}",
            price=price,
            mrp=mrp,
            currency="INR",
            shipping=0,
            availability=platform_info["availability"],
            seller=platform_info["seller"],
            fulfilled_by=platform_info["fulfilled_by"],
            condition="new",
            url=url,
            metadata={
                "source": "demo",
                "is_demo": True,
            }
        )
