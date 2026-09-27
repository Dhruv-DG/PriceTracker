"""
Abstract base class for search providers.
The application should not care which search engine produces results.
"""
from abc import ABC, abstractmethod
from typing import List
from app.schemas.schemas import SearchResultItem


class SearchProvider(ABC):
    """Interface for search providers."""

    @abstractmethod
    async def search(self, query: str, num_results: int = 15) -> List[SearchResultItem]:
        """
        Execute a search query and return normalized results.
        
        Args:
            query: The search query string (already optimized for product discovery)
            num_results: Maximum number of results to return
            
        Returns:
            List of normalized SearchResultItem objects
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this provider is available and configured."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and provenance."""
        ...
