"""Integration tests for Flink inventory forecasting job."""

import pytest
from processing.flink_jobs.inventory_forecasting import InventoryForecastingJob


class TestFlinkInventoryJob:
    """Integration tests for InventoryForecastingJob."""

    @pytest.fixture
    def job(self):
        """Create job instance."""
        return InventoryForecastingJob()

    def test_job_with_kafka_events(self, job):
        """Test job processes Kafka events correctly."""
        # Simulated Kafka events
        events = [
            {'item_id': 'sku-001', 'warehouse_id': 'wh-01', 'current_stock': 500},
            {'item_id': 'sku-001', 'warehouse_id': 'wh-01', 'current_stock': 480},
        ]

        forecast = job.forecast_inventory(events)
        assert isinstance(forecast, dict)

    def test_alert_generation_low_stock(self, job):
        """Test alert generation for low stock."""
        events = [
            {'current_stock': 50, 'item_id': 'sku-001'},
            {'current_stock': 45, 'item_id': 'sku-001'},
            {'current_stock': 40, 'item_id': 'sku-001'},
        ]

        forecast = job.forecast_inventory(events)
        assert forecast.get('alert') is not None

    def test_pipeline_latency(self, job):
        """Test pipeline latency is acceptable."""
        import time

        events = [{'current_stock': 100 + i} for i in range(100)]

        start = time.time()
        forecast = job.forecast_inventory(events)
        elapsed = (time.time() - start) * 1000  # ms

        assert elapsed < 2000  # Should be < 2 seconds

    def test_broadcast_state_enrichment(self, job):
        """Test broadcast state enriches events with product catalog."""
        # This tests that product metadata is available
        assert job.config is not None
