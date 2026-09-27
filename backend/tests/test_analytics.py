import pytest
from datetime import datetime, timedelta
from app.services.analytics import AnalyticsService
from app.schemas.schemas import PlatformHistory, HistoricalPriceResult, HistoricalObservation, PlatformInfo, PriceData

def test_volatility():
    service = AnalyticsService()
    
    # Create deterministic historical observations
    now = datetime.utcnow()
    # Prices: 100, 110 (+10%), 110 (0%), 88 (-20%), 88 (0%)
    obs = [
        HistoricalObservation(date=now - timedelta(days=4), price=100.0, source="test", provider="test"),
        HistoricalObservation(date=now - timedelta(days=3), price=110.0, source="test", provider="test"),
        HistoricalObservation(date=now - timedelta(days=2), price=110.0, source="test", provider="test"),
        HistoricalObservation(date=now - timedelta(days=1), price=88.0, source="test", provider="test"),
        HistoricalObservation(date=now, price=88.0, source="test", provider="test"),
    ]
    
    ph = PlatformHistory(
        platform=PlatformInfo(name="Test", domain="test.com"),
        history=HistoricalPriceResult(provider="test", platform="Test", platform_domain="test.com", observations=obs)
    )
    
    vol = service.compute_volatility([ph])
    
    # Largest increase is 10%
    assert vol.largest_increase_pct == 10.0
    # Largest drop is -20%
    assert vol.largest_drop_pct == -20.0
    
def test_historical_low_high():
    service = AnalyticsService()
    now = datetime.utcnow()
    obs = [
        HistoricalObservation(date=now - timedelta(days=2), price=150.0, source="test", provider="test"),
        HistoricalObservation(date=now - timedelta(days=1), price=50.0, source="test", provider="test"),
        HistoricalObservation(date=now, price=100.0, source="test", provider="test"),
    ]
    
    ph = PlatformHistory(
        platform=PlatformInfo(name="Test", domain="test.com"),
        history=HistoricalPriceResult(provider="test", platform="Test", platform_domain="test.com", observations=obs)
    )
    
    # Test compute_statistics instead since it's what calculates the stats
    stats = service.compute_statistics([o.price for o in obs])
    assert stats.min == 50.0
    assert stats.max == 150.0
    assert stats.mean == 100.0

def test_price_position():
    service = AnalyticsService()
    now = datetime.utcnow()
    obs = [
        HistoricalObservation(date=now - timedelta(days=1), price=50.0, source="test", provider="test"),
        HistoricalObservation(date=now, price=150.0, source="test", provider="test"),
    ]
    
    ph = PlatformHistory(
        platform=PlatformInfo(name="Test", domain="test.com"),
        history=HistoricalPriceResult(provider="test", platform="Test", platform_domain="test.com", observations=obs)
    )
    
    # Range is 50 to 150 (width = 100). Current is 100.
    pos = service.compute_price_position(current_price=100.0, platform_histories=[ph])
    
    # 100 is exactly in the middle of 50-150, so position_pct should be 50.0
    assert pos.position_pct == 50.0
    # Average is 100.0. vs_avg_pct should be 0.
    assert pos.vs_avg_pct == 0.0
    
    # If current is 150
    pos2 = service.compute_price_position(current_price=150.0, platform_histories=[ph])
    assert pos2.position_pct == 100.0
