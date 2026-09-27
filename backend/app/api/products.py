"""
Product API endpoints.
"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/{product_id}")
async def get_product(product_id: int):
    """Get product details by ID."""
    # MVP placeholder — will be expanded
    return {"id": product_id, "status": "not_implemented_yet"}


@router.get("/{product_id}/prices")
async def get_product_prices(product_id: int):
    """Get current prices for a product."""
    return {"id": product_id, "prices": [], "status": "not_implemented_yet"}


@router.get("/{product_id}/history")
async def get_product_history(product_id: int, days: int = 90):
    """Get historical price data for a product."""
    return {"id": product_id, "history": [], "days": days, "status": "not_implemented_yet"}


@router.get("/{product_id}/analytics")
async def get_product_analytics(product_id: int):
    """Get analytics for a product."""
    return {"id": product_id, "analytics": {}, "status": "not_implemented_yet"}
