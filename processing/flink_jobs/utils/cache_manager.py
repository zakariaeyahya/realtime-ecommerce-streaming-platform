"""
Cache Manager - Redis-based caching with in-memory fallback.

Caches inventory forecasts and recommendations with configurable TTL.
Falls back to in-memory dict when Redis is unavailable.
Tracks cache statistics (hits, misses, evictions).
"""

import logging
from typing import Any, Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache with in-memory fallback."""

    def __init__(self, host: str = 'localhost', port: int = 6379,
                 ttl_seconds: int = 604800):
        """Initialize cache manager.

        Args:
            host: Redis host
            port: Redis port
            ttl_seconds: TTL for cached entries (default 7 days)
        """
        self.host = host
        self.port = port
        self.ttl_seconds = ttl_seconds
        self.redis_client = None
        self.connected = False
        self._memory_cache: Dict[str, str] = {}

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        # Try to connect
        self._connect()
        logger.info("CacheManager initialized (connected=%s)", self.connected)

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
            logger.info("Connected to Redis at %s:%s", self.host, self.port)
        except Exception as e:
            logger.warning("Redis connection failed: %s. Using mock cache.", e)
            self.connected = False

    def connect(self) -> None:
        """Public method to connect/reconnect to Redis."""
        self._connect()

    def _get(self, key: str) -> Optional[str]:
        """Get a raw value by key from Redis or memory fallback.

        Args:
            key: Cache key

        Returns:
            Raw string value or None
        """
        try:
            if self.connected and self.redis_client:
                return self.redis_client.get(key)
            return self._memory_cache.get(key)
        except Exception as e:
            logger.error("Cache get failed: %s", e)
            return self._memory_cache.get(key)

    def _set(self, key: str, value: str) -> bool:
        """Set a raw value by key in Redis or memory fallback.

        Args:
            key: Cache key
            value: String value to store

        Returns:
            True if successful
        """
        try:
            if self.connected and self.redis_client:
                self.redis_client.setex(key, self.ttl_seconds, value)
            self._memory_cache[key] = value
            return True
        except Exception as e:
            logger.error("Cache set failed: %s", e)
            self._memory_cache[key] = value
            return True

    def get_forecast(self, item_id: str, warehouse_id: str) -> Optional[Dict]:
        """Retrieve cached forecast.

        Args:
            item_id: Product item ID
            warehouse_id: Warehouse identifier

        Returns:
            Cached forecast dict or None
        """
        key = f"inventory:forecast:{item_id}:{warehouse_id}"
        value = self._get(key)

        if value:
            self.hits += 1
            return json.loads(value) if isinstance(value, str) else value

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
        return self._set(key, json.dumps(forecast))

    def get_recommendations(self, user_id: str) -> Optional[List[Dict]]:
        """Retrieve cached recommendations for a user.

        Args:
            user_id: User identifier

        Returns:
            List of recommendation dicts or None
        """
        key = f"recommendations:{user_id}"
        value = self._get(key)

        if value:
            self.hits += 1
            return json.loads(value) if isinstance(value, str) else value

        self.misses += 1
        return None

    def set_recommendations(self, user_id: str, recommendations: List[Dict]) -> bool:
        """Cache recommendations for a user.

        Args:
            user_id: User identifier
            recommendations: List of recommendation dicts

        Returns:
            True if successful
        """
        key = f"recommendations:{user_id}"
        return self._set(key, json.dumps(recommendations))

    def get_stats(self) -> Dict:
        """Return cache statistics (alias for get_cache_stats)."""
        return self.get_cache_stats()

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
