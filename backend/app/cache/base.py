import time
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Tuple

class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600):
        pass

    @abstractmethod
    async def delete(self, key: str):
        pass

    @abstractmethod
    async def clear(self):
        pass


class MemoryCache(CacheBackend):
    """Thread-safe in-memory cache with TTL expiration."""

    def __init__(self, max_size: int = 1000):
        self._store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._store:
                value, expire_at = self._store[key]
                if time.time() < expire_at:
                    return value
                else:
                    del self._store[key]
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        async with self._lock:
            if len(self._store) >= self._max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest_key]
            self._store[key] = (value, time.time() + ttl)

    async def delete(self, key: str):
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self):
        async with self._lock:
            self._store.clear()

    async def cleanup(self):
        async with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self._store.items() if now >= exp]
            for k in expired:
                del self._store[k]

    @property
    def size(self) -> int:
        return len(self._store)
