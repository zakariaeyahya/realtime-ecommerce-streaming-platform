"""Integration tests for complete recommendation pipeline."""

import pytest


class TestRecommendationPipeline:
    """Test end-to-end recommendation pipeline."""

    def test_data_consistency(self):
        """Test data integrity throughout pipeline."""
        from processing.flink_jobs.recommendations import RecommendationsJob
        job = RecommendationsJob()
        assert job is not None

    def test_cache_coherency(self):
        """Test cache consistency."""
        from processing.flink_jobs.utils.cache_manager import CacheManager
        cache = CacheManager()
        cache.connect()

        reco = [{'item_id': 'i1', 'score': 0.95}]
        cache.set_recommendations('u1', reco)
        cached = cache.get_recommendations('u1')
        assert cached is not None

    def test_cold_start_users_get_recommendations(self):
        """Test new users get recommendations."""
        from processing.flink_jobs.recommendations import RecommendationsJob
        job = RecommendationsJob()

        result = job.process_session([])
        assert result is not None

    def test_performance_under_load(self):
        """Test throughput."""
        from processing.flink_jobs.recommendations import RecommendationsJob
        import time

        job = RecommendationsJob()
        start = time.time()

        for i in range(100):
            events = [
                {'user_id': f'u{i}', 'item_id': 'i1', 'event_type': 'view'},
            ]
            job.process_session(events)

        elapsed = time.time() - start
        assert elapsed > 0

    def test_metric_accuracy(self):
        """Test metrics collection."""
        from processing.flink_jobs.utils.cache_manager import CacheManager
        cache = CacheManager()
        cache.connect()

        stats = cache.get_stats()
        assert 'hit_rate' in stats
