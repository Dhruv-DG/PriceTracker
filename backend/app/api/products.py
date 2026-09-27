"""
Product API endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import Product, ProductListing, PriceObservation, Platform

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get product details by ID."""
    stmt = select(Product).where(Product.id == product_id)
    product = (await db.execute(stmt)).scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return {
        "id": product.id,
        "canonical_name": product.canonical_name,
        "brand": product.brand,
        "model": product.model,
        "variant": product.variant,
        "category": product.category,
        "created_at": product.created_at
    }


@router.get("/{product_id}/prices")
async def get_product_prices(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get current prices for a product (latest observation per listing)."""
    stmt = (
        select(ProductListing, Platform)
        .join(Platform)
        .where(ProductListing.product_id == product_id)
    )
    listings = (await db.execute(stmt)).all()
    
    prices = []
    for listing, platform in listings:
        obs_stmt = (
            select(PriceObservation)
            .where(PriceObservation.listing_id == listing.id)
            .order_by(desc(PriceObservation.timestamp))
            .limit(1)
        )
        latest_obs = (await db.execute(obs_stmt)).scalar_one_or_none()
        
        if latest_obs:
            prices.append({
                "platform": platform.name,
                "domain": platform.domain,
                "url": listing.url,
                "price": latest_obs.price,
                "effective_price": latest_obs.effective_price,
                "currency": latest_obs.currency,
                "timestamp": latest_obs.timestamp,
                "seller": listing.seller
            })
            
    return {"id": product_id, "prices": prices}


@router.get("/{product_id}/history")
async def get_product_history(product_id: int, days: int = 90, db: AsyncSession = Depends(get_db)):
    """Get historical price data for a product."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    stmt = (
        select(PriceObservation, Platform)
        .join(ProductListing)
        .join(Platform)
        .where(
            ProductListing.product_id == product_id,
            PriceObservation.timestamp >= cutoff
        )
        .order_by(PriceObservation.timestamp)
    )
    results = (await db.execute(stmt)).all()
    
    history = []
    for obs, platform in results:
        history.append({
            "platform": platform.name,
            "date": obs.timestamp,
            "price": obs.price,
            "currency": obs.currency,
            "source": obs.source,
            "confidence": obs.confidence
        })
        
    return {"id": product_id, "days": days, "history": history}


@router.get("/{product_id}/analytics")
async def get_product_analytics(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get basic analytics for a product from the database."""
    # We will get all observations and compute some basic stats
    history_res = await get_product_history(product_id, days=365, db=db)
    history = history_res["history"]
    
    if not history:
        return {"id": product_id, "analytics": {}, "status": "no_data"}
        
    prices = [h["price"] for h in history]
    
    return {
        "id": product_id,
        "analytics": {
            "historical_low": min(prices),
            "historical_high": max(prices),
            "historical_average": sum(prices) / len(prices),
            "observations_count": len(prices)
        }
    }
