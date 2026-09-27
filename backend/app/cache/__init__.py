"""
In-memory cache with TTL support.
Architecture allows swapping to Redis later.
"""
import time
import asyncio
from typing import Any, Optional, Dict, Tuple
from functools import wraps
import hashlib
import json


class TTLCache:
    """Thread-safe in-memory cache with TTL expiration."""

    def __init__(self, max_size: int = 1000):
        self._store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value if exists and not expired."""
        async with self._lock:
            if key in self._store:
                value, expire_at = self._store[key]
                if time.time() < expire_at:
                    return value
                else:
                    del self._store[key]
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value with TTL in seconds."""
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._store) >= self._max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest_key]
            self._store[key] = (value, time.time() + ttl)

    async def delete(self, key: str):
        """Delete a key."""
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self):
        """Clear all entries."""
        async with self._lock:
            self._store.clear()

    async def cleanup(self):
        """Remove expired entries."""
        async with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self._store.items() if now >= exp]
            for k in expired:
                del self._store[k]

    @property
    def size(self) -> int:
        return len(self._store)


def make_cache_key(*args, **kwargs) -> str:
    """Create a deterministic cache key from arguments."""
    key_data = json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}})
    return hashlib.md5(key_data.encode()).hexdigest()


# Global cache instances
search_cache = TTLCache(max_size=500)
price_cache = TTLCache(max_size=1000)
history_cache = TTLCache(max_size=500)
product_cache = TTLCache(max_size=500)
