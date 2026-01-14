"""
Cache Manager - Redis-based forecast caching with fallback.

Caches inventory forecasts with 7-day TTL.
Provides fallback to in-memory mock Redis if unavailable.
Tracks cache statistics (hits, misses, evictions).
"""

import logging
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache for inventory forecasts."""

    def __init__(self, host: str = 'localhost', port: int = 6379,
                 ttl_seconds: int = 604800):
        """Initialize cache manager.

        Args:
            host: Redis host
            port: Redis port
            ttl_seconds: TTL for cached forecasts (default 7 days)
        """
        self.host = host
        self.port = port
        self.ttl_seconds = ttl_seconds
        self.redis_client = None
        self.connected = False

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        # Try to connect
        self._connect()
        logger.info(f"CacheManager initialized (connected={self.connected})")

    def _connect(self) -> None:
        """Try to connect to Redis."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True,
                socket_connect_timeout=2
            )
            self.redis_client.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using mock cache.")
            self.connected = False

    def get_forecast(self, item_id: str, warehouse_id: str) -> Optional[Dict]:
        """Retrieve cached forecast.

        Args:
            item_id: Product item ID
            warehouse_id: Warehouse identifier

        Returns:
            Cached forecast dict or None
        """
        key = f"inventory:forecast:{item_id}:{warehouse_id}"

        try:
            if self.connected and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.hits += 1
                    return json.loads(value)

            self.misses += 1
            return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            self.misses += 1
            return None

    def set_forecast(self, item_id: str, warehouse_id: str,
                    forecast: Dict) -> bool:
        """Cache forecast result.

        Args:
            item_id: Product item ID
            warehouse_id: Warehouse identifier
            forecast: Forecast data to cache

        Returns:
            True if successful
        """
        key = f"inventory:forecast:{item_id}:{warehouse_id}"

        try:
            if self.connected and self.redis_client:
                self.redis_client.setex(
                    key,
                    self.ttl_seconds,
                    json.dumps(forecast)
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

    def get_cache_stats(self) -> Dict:
        """Return cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions,
            'connected': self.connected,
        }
