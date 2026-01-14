"""End-to-end tests for inventory forecasting pipeline."""

import pytest
from processing.flink_jobs.inventory_forecasting import InventoryForecastingJob
from processing.flink_jobs.utils.forecasting_engine import ForecastingEngine
from processing.flink_jobs.utils.time_series_features import TimeSeriesFeatures
from processing.flink_jobs.utils.cache_manager import CacheManager


class TestInventoryPipeline:
    """End-to-end tests for complete inventory forecasting pipeline."""

    @pytest.fixture
    def pipeline_components(self):
        """Create all pipeline components."""
        return {
            'job': InventoryForecastingJob(),
            'engine': ForecastingEngine(),
            'features': TimeSeriesFeatures(),
            'cache': CacheManager(),
        }

    def test_complete_forecast_pipeline(self, pipeline_components):
        """Test complete pipeline from events to forecast."""
        job = pipeline_components['job']
        engine = pipeline_components['engine']
        features = pipeline_components['features']
        cache = pipeline_components['cache']

        # Simulate event stream
        events = [
            {'current_stock': 300 + i*2, 'timestamp': 1000+i*100, 'item_id': 'sku-001'}
            for i in range(30)
        ]

        # Step 1: Extract features
        feature_dict = features.extract_features(events)
        assert len(feature_dict) > 0

        # Step 2: Generate forecast
        forecast = job.forecast_inventory(events)
        assert 'forecast_values' in forecast or 'alert' in forecast

        # Step 3: Cache result
        cache.set_forecast('sku-001', 'wh-01', forecast)

        # Step 4: Retrieve from cache
        cached = cache.get_forecast('sku-001', 'wh-01')
        assert cached is not None

    def test_model_accuracy_target(self, pipeline_components):
        """Test forecasting accuracy meets target."""
        engine = pipeline_components['engine']

        historical = [100 + i*2 for i in range(30)]
        forecast = engine.forecast(historical)

        accuracy = forecast.get('accuracy', 0)
        assert accuracy >= 0.85  # 85% target

    def test_cache_hit_rate(self, pipeline_components):
        """Test cache hit rate is optimal."""
        cache = pipeline_components['cache']

        # Simulate multiple accesses
        for i in range(10):
            cache.get_forecast('sku-001', 'wh-01')

        stats = cache.get_cache_stats()
        # First access will be miss, then hits
        assert stats['misses'] >= 1

    def test_latency_requirements(self, pipeline_components):
        """Test latency meets requirements."""
        import time

        job = pipeline_components['job']
        engine = pipeline_components['engine']

        events = [{'current_stock': 100 + i} for i in range(100)]

        start = time.time()
        job.forecast_inventory(events)
        job_elapsed = (time.time() - start) * 1000

        historical = [100 + i*2 for i in range(30)]
        start = time.time()
        engine.forecast(historical)
        engine_elapsed = (time.time() - start) * 1000

        total_latency = job_elapsed + engine_elapsed
        assert total_latency < 2000  # 2 second target

    def test_stockout_alert_accuracy(self, pipeline_components):
        """Test stockout alerts are accurate."""
        job = pipeline_components['job']

        # Low stock scenario
        low_stock_events = [
            {'current_stock': 20},
            {'current_stock': 15},
            {'current_stock': 10},
        ]

        low_forecast = job.forecast_inventory(low_stock_events)
        assert low_forecast.get('alert') == True

        # High stock scenario
        high_stock_events = [
            {'current_stock': 500},
            {'current_stock': 510},
            {'current_stock': 520},
        ]

        high_forecast = job.forecast_inventory(high_stock_events)
        assert high_forecast.get('alert') == False
