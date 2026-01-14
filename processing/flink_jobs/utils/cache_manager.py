"""
Cache Manager - Redis caching for recommendations.

Handles:
- Caching user recommendations with TTL
- Cache invalidation on user activity
- Hit rate tracking
- Fallback strategies
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for recommendations."""

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int = 3600
    ):
        """Initialize cache manager.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            ttl_seconds: Default TTL for cached items
        """
        self.host = host
        self.port = port
        self.db = db
        self.ttl_seconds = ttl_seconds
        self.client = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }

        logger.info(
            f"CacheManager initialized (host={host}:{port}, ttl={ttl_seconds}s)"
        )

    def connect(self) -> bool:
        """Connect to Redis server.

        Returns:
            True if connection successful
        """
        try:
            import redis
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            self.client.ping()
            logger.info("Connected to Redis")
            return True

        except ImportError:
            logger.warning("Redis library not installed, using mock cache")
            self.client = MockRedisClient()
            return True

        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.stats['errors'] += 1
            return False

    def get_recommendations(self, user_id: str) -> Optional[List[Dict]]:
        """Get cached recommendations for user.

        Args:
            user_id: User identifier

        Returns:
            List of recommendations or None if not cached
        """
        if not self.client:
            if not self.connect():
                return None

        key = self._get_cache_key(user_id)

        try:
            data = self.client.get(key)
            if data:
                self.stats['hits'] += 1
                logger.debug(f"Cache hit for user {user_id}")
                return json.loads(data)

            self.stats['misses'] += 1
            logger.debug(f"Cache miss for user {user_id}")
            return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            self.stats['errors'] += 1
            return None

    def set_recommendations(
        self,
        user_id: str,
        recommendations: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache recommendations for user.

        Args:
            user_id: User identifier
            recommendations: List of recommendations
            ttl: Optional TTL override

        Returns:
            True if successful
        """
        if not self.client:
            if not self.connect():
                return False

        key = self._get_cache_key(user_id)
        ttl = ttl or self.ttl_seconds

        try:
            data = json.dumps(recommendations)
            self.client.setex(key, ttl, data)
            self.stats['sets'] += 1
            logger.debug(f"Cached {len(recommendations)} recommendations for {user_id}")
            return True

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            self.stats['errors'] += 1
            return False

    def invalidate_user(self, user_id: str) -> bool:
        """Invalidate cache for a user.

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        if not self.client:
            return False

        key = self._get_cache_key(user_id)

        try:
            self.client.delete(key)
            logger.debug(f"Invalidated cache for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return False

    def get_hit_rate(self) -> float:
        """Get cache hit rate.

        Returns:
            Hit rate as percentage (0-100)
        """
        total = self.stats['hits'] + self.stats['misses']
        if total == 0:
            return 0.0
        return round((self.stats['hits'] / total) * 100, 2)

    def get_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dict with cache stats
        """
        return {
            **self.stats,
            'hit_rate': self.get_hit_rate(),
            'timestamp': datetime.now().isoformat()
        }

    def _get_cache_key(self, user_id: str) -> str:
        """Generate cache key for user.

        Args:
            user_id: User identifier

        Returns:
            Redis key string
        """
        return f"reco:user:{user_id}"

    def close(self) -> None:
        """Close Redis connection."""
        if self.client and hasattr(self.client, 'close'):
            self.client.close()
            logger.info("Redis connection closed")


class MockRedisClient:
    """Mock Redis client for testing without Redis server."""

    def __init__(self):
        """Initialize mock client."""
        self._store: Dict[str, str] = {}
        self._ttls: Dict[str, int] = {}

    def ping(self) -> bool:
        """Mock ping."""
        return True

    def get(self, key: str) -> Optional[str]:
        """Mock get."""
        return self._store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> bool:
        """Mock setex."""
        self._store[key] = value
        self._ttls[key] = ttl
        return True

    def delete(self, key: str) -> int:
        """Mock delete."""
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    def close(self) -> None:
        """Mock close."""
        pass
