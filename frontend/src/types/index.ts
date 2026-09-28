/**
 * TypeScript types matching the backend Pydantic schemas.
 */

export interface ParsedQuery {
  brand: string | null;
  model: string | null;
  variant: string | null;
  storage: string | null;
  ram: string | null;
  color: string | null;
  size: string | null;
  condition: string;
  category: string | null;
  search_query: string;
}

export interface PlatformInfo {
  id: number | null;
  name: string;
  domain: string;
  country: string;
  currency: string;
  logo_url: string | null;
}

export interface ProductInfo {
  id: number | null;
  canonical_name: string;
  brand: string | null;
  model: string | null;
  variant: string | null;
  category: string | null;
  storage: string | null;
  ram: string | null;
  color: string | null;
  size: string | null;
  condition: string;
  identifiers: Record<string, string>;
}

export interface PriceData {
  platform: PlatformInfo;
  listing_id: number | null;
  url: string;
  price: number | null;
  mrp: number | null;
  discount_pct: number | null;
  shipping: number | null;
  shipping_note: string;
  effective_price: number | null;
  currency: string;
  availability: string;
  seller: string | null;
  fulfilled_by: string | null;
  condition: string;
  title: string | null;
  last_updated: string;
  external_product_id: string | null;
  
  // Discovery & Verification fields
  search_price: number | null;
  verified_price: number | null;
  verification_status: 'PENDING' | 'VERIFIED' | 'FAILED';
  discovery_source: string;
  match_confidence: string;
  thumbnail: string | null;
  rating: number | null;
  review_count: number | null;
}

export interface HistoricalObservation {
  date: string;
  price: number;
  currency: string;
  source: string;
  source_type: string;
  provider: string;
  confidence: number;
}

export interface HistoricalPriceResult {
  provider: string;
  platform: string;
  platform_domain: string;
  product_id: string | null;
  currency: string;
  observations: HistoricalObservation[];
  start_date: string | null;
  end_date: string | null;
  observation_count: number;
  confidence: string;
  source_url: string | null;
  is_demo: boolean;
}

export interface PlatformHistory {
  platform: PlatformInfo;
  history: HistoricalPriceResult;
  historical_low: number | null;
  historical_high: number | null;
  historical_avg: number | null;
}

export interface PriceMovement {
  period: string;
  change_amount: number | null;
  change_pct: number | null;
  direction: string;
}

export interface PriceStatistics {
  mean: number | null;
  median: number | null;
  min: number | null;
  max: number | null;
  std_dev: number | null;
  observations_count: number;
  platforms_count: number;
}

export interface VolatilityInfo {
  level: string;
  std_dev: number | null;
  avg_daily_change: number | null;
  pct_volatility: number | null;
  price_change_count: number;
  largest_drop: number | null;
  largest_drop_pct: number | null;
  largest_increase: number | null;
  largest_increase_pct: number | null;
}

export interface PricePosition {
  current_price: number;
  historical_low: number;
  historical_high: number;
  position_pct: number;
  vs_low_pct: number;
  vs_high_pct: number;
  vs_avg_pct: number;
  historical_avg: number;
}

export interface AveragePricePoint {
  date: string;
  average_price: number;
  min_price: number;
  max_price: number;
  platforms_count: number;
  platform_prices: Record<string, number>;
}

export interface DataSourceInfo {
  platform: string;
  provider: string;
  coverage: string;
  coverage_start: string | null;
  coverage_end: string | null;
  observation_count: number;
  last_updated: string | null;
  confidence: string;
  is_demo: boolean;
}

export interface HighlightCards {
  current_lowest: PriceData | null;
  current_highest: PriceData | null;
  current_average: number | null;
  historical_low: number | null;
  historical_low_platform: string | null;
  historical_high: number | null;
  historical_high_platform: string | null;
  historical_avg: number | null;
  current_vs_hist_avg_pct: number | null;
  current_vs_hist_low_pct: number | null;
  price_range_low: number | null;
  price_range_high: number | null;
}

export interface DashboardResponse {
  product: ProductInfo;
  is_demo: boolean;
  highlights: HighlightCards;
  current_prices: PriceData[];
  platform_histories: PlatformHistory[];
  average_price_over_time: AveragePricePoint[];
  price_movements: PriceMovement[];
  current_statistics: PriceStatistics;
  historical_statistics: PriceStatistics;
  volatility: VolatilityInfo;
  price_position: PricePosition | null;
  data_sources: DataSourceInfo[];
  cheapest_platform: string | null;
  cheapest_historical_platform: string | null;
  most_consistent_platform: string | null;
  most_consistent_metric: string | null;
  timestamp: string;
  latency_ms: number | null;
}

export interface SearchResponse {
  search_id: number | null;
  query: string;
  parsed_query: ParsedQuery | null;
  product: ProductInfo | null;
  dashboard: DashboardResponse | null;
  current_prices: PriceData[];
  status: string;
  is_demo: boolean;
  latency_ms: number | null;
  errors: string[];
  warnings: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  demo_mode: boolean;
  providers: Record<string, string>;
}


