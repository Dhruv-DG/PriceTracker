"""
Abstract base class for e-commerce adapters.
Each adapter handles extracting product/price info from a specific platform.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExtractedProduct:
    """Product data extracted from an e-commerce page."""
    title: str
    price: Optional[float] = None
    mrp: Optional[float] = None
    currency: str = "INR"
    shipping: Optional[float] = None
    availability: str = "unknown"
    seller: Optional[str] = None
    fulfilled_by: Optional[str] = None
    condition: str = "new"
    external_id: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    image_url: Optional[str] = None
    url: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Calculate effective price
        self.effective_price = (self.price or 0) + (self.shipping or 0)
        # Calculate discount
        if self.mrp and self.price and self.mrp > self.price:
            self.discount_pct = round(((self.mrp - self.price) / self.mrp) * 100, 1)
        else:
            self.discount_pct = None


class EcommerceAdapter(ABC):
    """Interface for e-commerce platform adapters."""

    @abstractmethod
    async def can_handle(self, url: str) -> bool:
        """Check if this adapter can handle the given URL."""
        ...

    @abstractmethod
    async def extract_product(self, url: str) -> Optional[ExtractedProduct]:
        """Extract product information from the URL."""
        ...

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name."""
        ...

    @property
    @abstractmethod
    def platform_domain(self) -> str:
        """Primary domain for this platform."""
        ...

    @property
    def platform_domains(self) -> list[str]:
        """All domains handled by this adapter."""
        return [self.platform_domain]

    @property
    def country(self) -> str:
        return "IN"

    @property
    def currency(self) -> str:
        return "INR"
