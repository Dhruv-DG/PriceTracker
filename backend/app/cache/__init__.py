"""
Cache module exposing a unified abstraction that can switch to Redis later.
"""
import hashlib
import json

from app.cache.base import CacheBackend, MemoryCache

def make_cache_key(*args, **kwargs) -> str:
    """Create a deterministic cache key from arguments."""
    key_data = json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}})
    return hashlib.md5(key_data.encode()).hexdigest()

# Global cache instances (currently MemoryCache, but easily swapped to RedisCache later)
search_cache: CacheBackend = MemoryCache(max_size=500)
price_cache: CacheBackend = MemoryCache(max_size=1000)
history_cache: CacheBackend = MemoryCache(max_size=500)
product_cache: CacheBackend = MemoryCache(max_size=500)
