"""Unit tests for inventory forecasting job."""

import pytest
from typing import List, Dict
from processing.flink_jobs.inventory_forecasting import InventoryForecastingJob


class TestInventoryForecastingJob:
    """Test cases for InventoryForecastingJob."""

    @pytest.fixture
    def job(self):
        """Create job instance."""
        return InventoryForecastingJob()

    def test_job_initialization(self, job):
        """Test job initializes correctly."""
        assert job.alert_threshold == 100
        assert job.forecast_days == 7
        assert job.model_path is not None

    def test_high_stock_no_alert(self, job):
        """Test no alert for high stock levels."""
        events = [
            {'current_stock': 500, 'timestamp': 1000},
            {'current_stock': 480, 'timestamp': 2000},
            {'current_stock': 450, 'timestamp': 3000},
        ]

        forecast = job.forecast_inventory(events)
        assert forecast.get('alert') == False

    def test_low_stock_triggers_alert(self, job):
        """Test alert for low stock levels."""
        events = [
            {'current_stock': 50, 'timestamp': 1000},
            {'current_stock': 45, 'timestamp': 2000},
            {'current_stock': 40, 'timestamp': 3000},
        ]

        forecast = job.forecast_inventory(events)
        assert forecast.get('alert') == True

    def test_empty_events_handled(self, job):
        """Test empty events handled gracefully."""
        forecast = job.forecast_inventory([])
        assert isinstance(forecast, dict)

    def test_environment_creation(self, job):
        """Test Flink environment created."""
        try:
            env = job.create_environment()
            assert env is not None
        except ImportError:
            pytest.skip("Flink not available in test environment")

    def test_forecast_output_structure(self, job):
        """Test forecast output has correct structure."""
        events = [
            {'current_stock': 200 + i*10, 'timestamp': 1000+i*100}
            for i in range(10)
        ]

        forecast = job.forecast_inventory(events)
        assert 'forecast_values' in forecast or 'alert' in forecast
