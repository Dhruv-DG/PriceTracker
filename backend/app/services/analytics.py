"""
Analytics service — calculates all price statistics, trends, and metrics.
Pure computation, no external API calls.
"""
import statistics
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from app.schemas.schemas import (
    PriceData, PriceStatistics, VolatilityInfo, PriceMovement,
    PricePosition, AveragePricePoint, HighlightCards,
    HistoricalPriceResult, PlatformHistory, DataSourceInfo,
    ConfidenceLevel
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Computes all price analytics and statistics."""

    def compute_highlights(
        self,
        current_prices: List[PriceData],
        platform_histories: List[PlatformHistory],
    ) -> HighlightCards:
        """Compute the top-level highlight cards."""
        # Filter out 0 or null prices before doing any computation
        valid_current_prices = [p for p in current_prices if p.effective_price and p.effective_price > 0]
        
        if not valid_current_prices:
            return HighlightCards()

        prices = [p.effective_price for p in valid_current_prices]
        sorted_prices = sorted(valid_current_prices, key=lambda p: p.effective_price)

        current_lowest = sorted_prices[0] if sorted_prices else None
        current_highest = sorted_prices[-1] if sorted_prices else None
        current_average = round(statistics.mean(prices), 2) if prices else None

        # Historical metrics from all platforms
        all_hist_prices = []
        hist_low_platform = None
        hist_high_platform = None
        hist_low = None
        hist_high = None

        for ph in platform_histories:
            if ph.history.observations:
                obs_prices = [o.price for o in ph.history.observations if o.price and o.price > 0]
                if not obs_prices:
                    continue
                    
                all_hist_prices.extend(obs_prices)

                platform_low = min(obs_prices)
                platform_high = max(obs_prices)

                if hist_low is None or platform_low < hist_low:
                    hist_low = platform_low
                    hist_low_platform = ph.platform.name

                if hist_high is None or platform_high > hist_high:
                    hist_high = platform_high
                    hist_high_platform = ph.platform.name

        historical_avg = round(statistics.mean(all_hist_prices), 2) if all_hist_prices else None

        # Current vs historical comparisons
        current_vs_hist_avg = None
        current_vs_hist_low = None
        if current_lowest and historical_avg:
            current_vs_hist_avg = round(
                ((current_lowest.effective_price - historical_avg) / historical_avg) * 100, 1
            )
        if current_lowest and hist_low:
            current_vs_hist_low = round(
                ((current_lowest.effective_price - hist_low) / hist_low) * 100, 1
            )

        return HighlightCards(
            current_lowest=current_lowest,
            current_highest=current_highest,
            current_average=current_average,
            historical_low=hist_low,
            historical_low_platform=hist_low_platform,
            historical_high=hist_high,
            historical_high_platform=hist_high_platform,
            historical_avg=historical_avg,
            current_vs_hist_avg_pct=current_vs_hist_avg,
            current_vs_hist_low_pct=current_vs_hist_low,
            price_range_low=hist_low or (min(prices) if prices else None),
            price_range_high=hist_high or (max(prices) if prices else None),
        )

    def compute_statistics(self, prices: List[float]) -> PriceStatistics:
        """Compute descriptive statistics for a set of prices."""
        valid_prices = [p for p in prices if p and p > 0]
        if not valid_prices:
            return PriceStatistics()

        return PriceStatistics(
            mean=round(statistics.mean(valid_prices), 2),
            median=round(statistics.median(valid_prices), 2),
            min=round(min(valid_prices), 2),
            max=round(max(valid_prices), 2),
            std_dev=round(statistics.stdev(valid_prices), 2) if len(valid_prices) > 1 else 0,
            observations_count=len(valid_prices),
        )

    def compute_volatility(
        self,
        platform_histories: List[PlatformHistory]
    ) -> VolatilityInfo:
        """Compute price volatility metrics."""
        all_prices = []
        daily_changes = []
        pct_changes = []

        for ph in platform_histories:
            obs = sorted(ph.history.observations, key=lambda o: o.date)
            # Only consider valid, non-zero prices
            prices = [o.price for o in obs if o.price and o.price > 0]
            if not prices:
                continue
                
            all_prices.extend(prices)

            # Calculate daily percentage changes and raw changes
            for i in range(1, len(prices)):
                change = prices[i] - prices[i - 1]
                pct_change = change / prices[i - 1]
                daily_changes.append(change)
                pct_changes.append(pct_change)

        if not all_prices or len(all_prices) < 2:
            return VolatilityInfo()

        std_dev = statistics.stdev(all_prices)
        mean_price = statistics.mean(all_prices)
        
        # Volatility is now the standard deviation of percentage changes
        pct_volatility = None
        if len(pct_changes) > 1:
            pct_volatility = round(statistics.stdev(pct_changes) * 100, 2)

        # Classify volatility based on standard deviation of percentage changes
        if pct_volatility is not None:
            if pct_volatility < 2.0:
                level = "Low"
            elif pct_volatility < 5.0:
                level = "Medium"
            else:
                level = "High"
        else:
            level = "Unknown"

        # Find largest drop and increase
        largest_drop = min(daily_changes) if daily_changes else None
        largest_increase = max(daily_changes) if daily_changes else None
        
        largest_drop_pct = None
        if pct_changes:
            largest_drop_pct = round(min(pct_changes) * 100, 1)
            
        largest_increase_pct = None
        if pct_changes:
            largest_increase_pct = round(max(pct_changes) * 100, 1)

        return VolatilityInfo(
            level=level,
            std_dev=round(std_dev, 2),
            avg_daily_change=round(statistics.mean([abs(c) for c in daily_changes]), 2) if daily_changes else None,
            pct_volatility=pct_volatility,
            price_change_count=len([c for c in daily_changes if abs(c) > 1]),
            largest_drop=round(largest_drop, 2) if largest_drop else None,
            largest_drop_pct=largest_drop_pct,
            largest_increase=round(largest_increase, 2) if largest_increase else None,
            largest_increase_pct=largest_increase_pct,
        )

    def compute_price_movements(
        self,
        platform_histories: List[PlatformHistory],
        current_avg: Optional[float] = None
    ) -> List[PriceMovement]:
        """Compute price movements over standard periods."""
        periods = [
            ("24h", 1),
            ("7d", 7),
            ("30d", 30),
            ("90d", 90),
        ]

        if not current_avg:
            return [PriceMovement(period=p, direction="stable") for p, _ in periods]

        now = datetime.utcnow()
        movements = []

        for period_name, days in periods:
            cutoff = now - timedelta(days=days)
            past_prices = []

            for ph in platform_histories:
                for obs in ph.history.observations:
                    if abs((obs.date - cutoff).total_seconds()) < 86400 * 2:  # ~2 day window
                        if obs.price and obs.price > 0:
                            past_prices.append(obs.price)

            if past_prices:
                past_avg = statistics.mean(past_prices)
                change = current_avg - past_avg
                change_pct = round((change / past_avg) * 100, 1)
                direction = "down" if change < 0 else "up" if change > 0 else "stable"

                movements.append(PriceMovement(
                    period=period_name,
                    change_amount=round(change, 2),
                    change_pct=change_pct,
                    direction=direction,
                ))
            else:
                movements.append(PriceMovement(
                    period=period_name,
                    direction="stable"
                ))

        return movements

    def compute_average_price_over_time(
        self,
        platform_histories: List[PlatformHistory],
        days: int = 90
    ) -> List[AveragePricePoint]:
        """Compute the average price across platforms over time."""
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        # Group all observations by date
        daily_data: Dict[str, Dict[str, float]] = defaultdict(dict)

        for ph in platform_histories:
            platform_name = ph.platform.name
            for obs in ph.history.observations:
                if obs.date >= cutoff and obs.price and obs.price > 0:
                    date_str = obs.date.strftime("%Y-%m-%d")
                    daily_data[date_str][platform_name] = obs.price

        # Compute averages
        avg_points = []
        for date_str in sorted(daily_data.keys()):
            platform_prices = daily_data[date_str]
            prices = list(platform_prices.values())

            avg_points.append(AveragePricePoint(
                date=datetime.strptime(date_str, "%Y-%m-%d"),
                average_price=round(statistics.mean(prices), 2),
                min_price=round(min(prices), 2),
                max_price=round(max(prices), 2),
                platforms_count=len(prices),
                platform_prices=platform_prices,
            ))

        return avg_points

    def compute_price_position(
        self,
        current_price: float,
        platform_histories: List[PlatformHistory]
    ) -> Optional[PricePosition]:
        """Compute where the current price sits in the historical range."""
        all_prices = []
        for ph in platform_histories:
            all_prices.extend([o.price for o in ph.history.observations])

        if not all_prices or len(all_prices) < 2:
            return None

        hist_low = min(all_prices)
        hist_high = max(all_prices)
        hist_avg = statistics.mean(all_prices)
        price_range = hist_high - hist_low

        if price_range == 0:
            position_pct = 50.0
        else:
            position_pct = round(((current_price - hist_low) / price_range) * 100, 1)
            position_pct = max(0, min(100, position_pct))

        return PricePosition(
            current_price=current_price,
            historical_low=hist_low,
            historical_high=hist_high,
            position_pct=position_pct,
            vs_low_pct=round(((current_price - hist_low) / hist_low) * 100, 1) if hist_low else 0,
            vs_high_pct=round(((hist_high - current_price) / hist_high) * 100, 1) if hist_high else 0,
            vs_avg_pct=round(((current_price - hist_avg) / hist_avg) * 100, 1) if hist_avg else 0,
            historical_avg=round(hist_avg, 2),
        )

    def find_cheapest_historical_platform(
        self,
        platform_histories: List[PlatformHistory]
    ) -> Optional[str]:
        """Find which platform has been cheapest on average historically."""
        platform_avgs = {}
        for ph in platform_histories:
            if ph.history.observations:
                prices = [o.price for o in ph.history.observations]
                platform_avgs[ph.platform.name] = statistics.mean(prices)

        if not platform_avgs:
            return None

        return min(platform_avgs, key=platform_avgs.get)

    def find_most_consistent_platform(
        self,
        platform_histories: List[PlatformHistory]
    ) -> tuple[Optional[str], Optional[str]]:
        """Find the platform with lowest coefficient of variation (normalized price variability)."""
        platform_cv = {}
        for ph in platform_histories:
            if ph.history.observations and len(ph.history.observations) > 1:
                prices = [o.price for o in ph.history.observations]
                mean_price = statistics.mean(prices)
                if mean_price > 0:
                    cv = statistics.stdev(prices) / mean_price
                    platform_cv[ph.platform.name] = cv

        if not platform_cv:
            return None, None

        most_consistent = min(platform_cv, key=platform_cv.get)
        return most_consistent, "Lowest price variability (CV)"

    def build_data_sources(
        self,
        platform_histories: List[PlatformHistory]
    ) -> List[DataSourceInfo]:
        """Build data source provenance info for display."""
        sources = []
        for ph in platform_histories:
            hist = ph.history

            if hist.observations:
                days = (hist.end_date - hist.start_date).days if hist.start_date and hist.end_date else 0
                if days > 365:
                    coverage = f"{days // 365} year(s)"
                elif days > 30:
                    coverage = f"{days // 30} month(s)"
                elif days > 0:
                    coverage = f"{days} days"
                else:
                    coverage = "today"
            else:
                coverage = "unavailable"

            sources.append(DataSourceInfo(
                platform=ph.platform.name,
                provider=hist.provider,
                coverage=coverage,
                coverage_start=hist.start_date,
                coverage_end=hist.end_date,
                observation_count=hist.observation_count,
                last_updated=hist.end_date,
                confidence=hist.confidence,
                is_demo=hist.is_demo,
            ))

        return sources


# Global analytics service instance
analytics_service = AnalyticsService()
