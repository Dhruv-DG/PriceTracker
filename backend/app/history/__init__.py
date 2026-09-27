"""
Historical price provider system.
"""
from app.history.base import HistoricalPriceProvider
from app.history.own_database import OwnDatabaseProvider
from app.history.demo import DemoHistoricalProvider
