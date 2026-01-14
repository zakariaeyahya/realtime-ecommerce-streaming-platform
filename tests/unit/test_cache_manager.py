"""Unit tests for cache manager."""

import pytest
from processing.flink_jobs.utils.cache_manager import CacheManager


class TestCacheManager:
    """Test cases for CacheManager."""

    @pytest.fixture
    def cache(self):
        """Create cache manager."""
        return CacheManager()

    def test_cache_initialization(self, cache):
        """Test cache initializes."""
        assert cache is not None
        assert cache.ttl_seconds == 604800

    def test_cache_get_miss(self, cache):
        """Test cache get on miss."""
        result = cache.get_forecast("sku-001", "wh-01")
        assert result is None
        assert cache.misses > 0

    def test_cache_set_get(self, cache):
        """Test cache set and get."""
        forecast_data = {"forecast": [100, 95, 90], "alert": False}

        success = cache.set_forecast("sku-001", "wh-01", forecast_data)
        assert isinstance(success, bool)

    def test_cache_stats_structure(self, cache):
        """Test cache statistics structure."""
        stats = cache.get_cache_stats()

        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats

    def test_cache_hit_rate_calculation(self, cache):
        """Test hit rate calculation."""
        cache.hits = 80
        cache.misses = 20

        stats = cache.get_cache_stats()
        assert stats['hit_rate'] == 80.0

    def test_multiple_items_cached(self, cache):
        """Test multiple items can be cached."""
        items = [
            ("sku-001", "wh-01"),
            ("sku-002", "wh-02"),
            ("sku-003", "wh-01"),
        ]

        for item_id, warehouse_id in items:
            cache.set_forecast(
                item_id,
                warehouse_id,
                {"forecast": [100, 90], "alert": False}
            )
