"""Unit tests for Cache Manager."""

import pytest
from unittest.mock import Mock, patch


class TestCacheManager:
    """Test Redis cache manager."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager."""
        from processing.flink_jobs.utils.cache_manager import CacheManager
        return CacheManager(host='localhost', port=6379)

    def test_cache_manager_initialization(self, cache_manager):
        """Test cache manager initializes."""
        assert cache_manager.host == 'localhost'
        assert cache_manager.port == 6379

    def test_connect(self, cache_manager):
        """Test Redis connection."""
        result = cache_manager.connect()
        assert result is True

    def test_set_recommendations(self, cache_manager):
        """Test storing recommendations."""
        cache_manager.connect()
        reco = [{'item_id': 'i1', 'score': 0.95}]
        result = cache_manager.set_recommendations('user1', reco)
        assert result is True

    def test_get_recommendations_hit(self, cache_manager):
        """Test retrieving cached recommendations."""
        cache_manager.connect()
        reco = [{'item_id': 'i1', 'score': 0.95}]
        cache_manager.set_recommendations('user1', reco)
        cached = cache_manager.get_recommendations('user1')
        assert cached is not None

    def test_get_recommendations_miss(self, cache_manager):
        """Test miss when not cached."""
        cache_manager.connect()
        cached = cache_manager.get_recommendations('nonexistent_user')
        assert cached is None

    def test_invalidate_user(self, cache_manager):
        """Test invalidating cache."""
        cache_manager.connect()
        reco = [{'item_id': 'i1', 'score': 0.95}]
        cache_manager.set_recommendations('user1', reco)
        result = cache_manager.invalidate_user('user1')
        assert result is True

    def test_get_hit_rate(self, cache_manager):
        """Test cache hit rate calculation."""
        cache_manager.connect()
        hit_rate = cache_manager.get_hit_rate()
        assert 0 <= hit_rate <= 100
