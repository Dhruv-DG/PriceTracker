"""
Pydantic schemas for API request/response models.
These are the data contracts between frontend and backend.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class SourceTypeEnum(str, Enum):
    EXTERNAL_API = "external_api"
    OWN_TRACKER = "own_tracker"
    DEMO = "demo"


# ─── Search ──────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Product search query")


class ParsedQuery(BaseModel):
    """LLM-parsed product attributes."""
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    storage: Optional[str] = None
    ram: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    condition: str = "new"
    category: Optional[str] = None
    search_query: str = ""  # Optimized search query


class SearchResultItem(BaseModel):
    """A single search result."""
    title: str
    url: str
    domain: str
    snippet: Optional[str] = None
    source: str = "search"
    is_product_page: bool = False
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = {}
    match_confidence: str = "HIGH"


# ─── Product ─────────────────────────────────────────────

class ProductInfo(BaseModel):
    """Canonical product information."""
    id: Optional[int] = None
    canonical_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    category: Optional[str] = None
    storage: Optional[str] = None
    ram: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    condition: str = "new"
    identifiers: Dict[str, str] = {}


class PlatformInfo(BaseModel):
    """Platform/store information."""
    id: Optional[int] = None
    name: str
    domain: str
    country: str = "IN"
    currency: str = "INR"
    logo_url: Optional[str] = None


# ─── Price ───────────────────────────────────────────────

class PriceData(BaseModel):
    """Current price from a platform."""
    platform: PlatformInfo
    listing_id: Optional[int] = None
    url: str
    price: float
    mrp: Optional[float] = None
    discount_pct: Optional[float] = None
    shipping: Optional[float] = None
    shipping_note: str = "Unknown"
    effective_price: float
    currency: str = "INR"
    availability: str = "available"
    seller: Optional[str] = None
    fulfilled_by: Optional[str] = None
    condition: str = "new"
    title: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    external_product_id: Optional[str] = None
    
    # Discovery & Verification fields
    search_price: Optional[float] = None
    verified_price: Optional[float] = None
    verification_status: str = "PENDING"  # PENDING, VERIFIED, FAILED
    discovery_source: str = "search"
    match_confidence: str = "HIGH"
    thumbnail: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class HistoricalObservation(BaseModel):
    """A single historical price point."""
    date: datetime
    price: float
    currency: str = "INR"
    source: str
    source_type: str = SourceTypeEnum.OWN_TRACKER.value
    provider: str
    confidence: float = 1.0


class HistoricalPriceResult(BaseModel):
    """Historical price data from a provider."""
    provider: str
    platform: str
    platform_domain: str
    product_id: Optional[str] = None
    currency: str = "INR"
    observations: List[HistoricalObservation] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observation_count: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    source_url: Optional[str] = None
    is_demo: bool = False


class PlatformHistory(BaseModel):
    """History data for a single platform."""
    platform: PlatformInfo
    history: HistoricalPriceResult
    historical_low: Optional[float] = None
    historical_high: Optional[float] = None
    historical_avg: Optional[float] = None


# ─── Analytics ───────────────────────────────────────────

class PriceMovement(BaseModel):
    """Price change over a period."""
    period: str  # "24h", "7d", "30d", "90d"
    change_amount: Optional[float] = None
    change_pct: Optional[float] = None
    direction: str = "stable"  # "up", "down", "stable"


class PriceStatistics(BaseModel):
    """Statistical summary of prices."""
    mean: Optional[float] = None
    median: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    std_dev: Optional[float] = None
    observations_count: int = 0
    platforms_count: int = 0


class VolatilityInfo(BaseModel):
    """Price volatility metrics."""
    level: str = "unknown"  # "low", "medium", "high"
    std_dev: Optional[float] = None
    avg_daily_change: Optional[float] = None
    pct_volatility: Optional[float] = None
    price_change_count: int = 0
    largest_drop: Optional[float] = None
    largest_drop_pct: Optional[float] = None
    largest_increase: Optional[float] = None
    largest_increase_pct: Optional[float] = None


class PricePosition(BaseModel):
    """Current price position within historical range."""
    current_price: float
    historical_low: float
    historical_high: float
    position_pct: float  # 0-100
    vs_low_pct: float  # % above low
    vs_high_pct: float  # % below high
    vs_avg_pct: float  # % vs average
    historical_avg: float


class AveragePricePoint(BaseModel):
    """Average price at a point in time."""
    date: datetime
    average_price: float
    min_price: float
    max_price: float
    platforms_count: int
    platform_prices: Dict[str, float] = {}


class DataSourceInfo(BaseModel):
    """Information about a data source."""
    platform: str
    provider: str
    coverage: str  # e.g., "12 months", "30 days", "unavailable"
    coverage_start: Optional[datetime] = None
    coverage_end: Optional[datetime] = None
    observation_count: int = 0
    last_updated: Optional[datetime] = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    is_demo: bool = False


# ─── Dashboard Response ──────────────────────────────────

class HighlightCards(BaseModel):
    """Top-level dashboard highlight cards."""
    current_lowest: Optional[PriceData] = None
    current_highest: Optional[PriceData] = None
    current_average: Optional[float] = None
    historical_low: Optional[float] = None
    historical_low_platform: Optional[str] = None
    historical_high: Optional[float] = None
    historical_high_platform: Optional[str] = None
    historical_avg: Optional[float] = None
    current_vs_hist_avg_pct: Optional[float] = None
    current_vs_hist_low_pct: Optional[float] = None
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None


class DashboardResponse(BaseModel):
    """Complete dashboard data."""
    product: ProductInfo
    is_demo: bool = False
    highlights: HighlightCards
    current_prices: List[PriceData] = []
    platform_histories: List[PlatformHistory] = []
    average_price_over_time: List[AveragePricePoint] = []
    price_movements: List[PriceMovement] = []
    current_statistics: PriceStatistics
    historical_statistics: PriceStatistics
    volatility: VolatilityInfo
    price_position: Optional[PricePosition] = None
    data_sources: List[DataSourceInfo] = []
    cheapest_platform: Optional[str] = None
    cheapest_historical_platform: Optional[str] = None
    most_consistent_platform: Optional[str] = None
    most_consistent_metric: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: Optional[float] = None


class SearchResponse(BaseModel):
    """Response from a search request."""
    search_id: Optional[int] = None
    query: str
    parsed_query: Optional[ParsedQuery] = None
    product: Optional[ProductInfo] = None
    dashboard: Optional[DashboardResponse] = None
    current_prices: List[PriceData] = []
    status: str = "COMPLETED"
    is_demo: bool = False
    latency_ms: Optional[float] = None
    errors: List[str] = []
    warnings: List[str] = []


class SearchStatusResponse(BaseModel):
    """Response from a search status check."""
    status: str
    current_prices_ready: bool = False
    history_ready: bool = False
    analytics_ready: bool = False
    completed: bool = False
    dashboard: Optional[DashboardResponse] = None


# ─── Tracking ────────────────────────────────────────────

class TrackingRequest(BaseModel):
    product_id: int
    frequency_minutes: int = 360


class TrackingJobInfo(BaseModel):
    id: int
    product: ProductInfo
    platforms: List[PlatformInfo] = []
    frequency_minutes: int
    status: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime


# ─── Health ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    demo_mode: bool
    providers: Dict[str, str] = {}
