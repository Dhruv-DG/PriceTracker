"""
SQLAlchemy ORM models for the Price Intelligence database.
Covers products, platforms, listings, price observations,
historical sources, searches, tracking jobs, and alerts.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, JSON, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SourceType(str, enum.Enum):
    EXTERNAL_API = "external_api"
    OWN_TRACKER = "own_tracker"
    USER_REPORTED = "user_reported"
    DEMO = "demo"


class TrackingStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class Product(Base):
    """Canonical product identity."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String(500), nullable=False, index=True)
    brand = Column(String(200))
    model = Column(String(200))
    variant = Column(String(200))
    category = Column(String(200))
    storage = Column(String(50))
    ram = Column(String(50))
    color = Column(String(100))
    size = Column(String(100))
    condition = Column(String(50), default="new")
    identifiers = Column(JSON, default=dict)  # ASIN, GTIN, EAN, UPC, MPN, SKU
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listings = relationship("ProductListing", back_populates="product", lazy="selectin")


class Platform(Base):
    """E-commerce platform."""
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    domain = Column(String(200), nullable=False, unique=True, index=True)
    country = Column(String(10), default="IN")
    currency = Column(String(10), default="INR")
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True)

    listings = relationship("ProductListing", back_populates="platform", lazy="selectin")


class ProductListing(Base):
    """A product listing on a specific platform."""
    __tablename__ = "product_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    url = Column(String(2000), nullable=False)
    external_product_id = Column(String(200), index=True)  # ASIN, etc.
    title = Column(String(1000))
    seller = Column(String(500))
    availability = Column(String(100), default="unknown")
    fulfilled_by = Column(String(200))
    product_condition = Column(String(50), default="new")
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="listings")
    platform = relationship("Platform", back_populates="listings")
    price_observations = relationship("PriceObservation", back_populates="listing", lazy="selectin")
    tracking_jobs = relationship("TrackingJob", back_populates="listing", lazy="selectin")

    __table_args__ = (
        Index("ix_listing_product_platform", "product_id", "platform_id"),
    )


class PriceObservation(Base):
    """A single price data point."""
    __tablename__ = "price_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("product_listings.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    mrp = Column(Float)
    shipping = Column(Float)
    effective_price = Column(Float)
    currency = Column(String(10), default="INR")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(200))  # "keepa", "own_tracker", "demo"
    source_type = Column(String(50), default=SourceType.OWN_TRACKER.value)
    provider = Column(String(200))
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0

    listing = relationship("ProductListing", back_populates="price_observations")

    __table_args__ = (
        Index("ix_observation_listing_timestamp", "listing_id", "timestamp"),
    )


class HistoricalSource(Base):
    """Metadata about historical data sources."""
    __tablename__ = "historical_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(200), nullable=False)
    platform_domain = Column(String(200))
    product_id = Column(Integer, ForeignKey("products.id"))
    coverage_start = Column(DateTime)
    coverage_end = Column(DateTime)
    observation_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    confidence = Column(String(50), default="medium")  # low, medium, high
    metadata_ = Column("metadata", JSON, default=dict)


class Search(Base):
    """User search record."""
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(1000), nullable=False, index=True)
    parsed_query = Column(JSON)  # LLM-parsed product attributes
    status = Column(String(50), default="DISCOVERING") # ENRICHING, COMPLETED, FAILED
    timestamp = Column(DateTime, default=datetime.utcnow)
    results_count = Column(Integer, default=0)
    latency_ms = Column(Float)

    results = relationship("SearchResult", back_populates="search", lazy="selectin")


class SearchResult(Base):
    """Individual search result."""
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False, index=True)
    url = Column(String(2000), nullable=False)
    title = Column(String(1000))
    domain = Column(String(200))
    snippet = Column(Text)
    relevance_score = Column(Float)
    is_product_page = Column(Boolean, default=False)
    matched_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    search = relationship("Search", back_populates="results")


class TrackingJob(Base):
    """Background tracking job for a product listing."""
    __tablename__ = "tracking_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("product_listings.id"), nullable=False, index=True)
    frequency_minutes = Column(Integer, default=360)  # 6 hours
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    status = Column(String(50), default=TrackingStatus.ACTIVE.value)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("ProductListing", back_populates="tracking_jobs")


class PriceAlert(Base):
    """Price alert configuration (extensible for future)."""
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    alert_type = Column(String(50))  # "price_below", "price_drop_pct", "historical_low"
    threshold_value = Column(Float)
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
