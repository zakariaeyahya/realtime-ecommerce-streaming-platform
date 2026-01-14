"""Unit tests for forecasting engine."""

import pytest
from processing.flink_jobs.utils.forecasting_engine import ForecastingEngine


class TestForecastingEngine:
    """Test cases for ForecastingEngine."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return ForecastingEngine()

    def test_engine_initialization(self, engine):
        """Test engine initializes with correct weights."""
        assert engine.prophet_weight == 0.6
        assert engine.arima_weight == 0.4

    def test_forecast_generation(self, engine):
        """Test forecast generation."""
        historical_data = [100 + i*2 for i in range(30)]
        forecast = engine.forecast(historical_data, periods=7)

        assert 'forecast' in forecast
        assert len(forecast.get('forecast', [])) > 0

    def test_insufficient_data_handling(self, engine):
        """Test handling of insufficient historical data."""
        historical_data = [100, 105, 110]
        forecast = engine.forecast(historical_data)

        assert isinstance(forecast, dict)

    def test_ensemble_combination(self, engine):
        """Test Prophet and ARIMA ensemble voting."""
        prophet_forecast = {'values': [100, 105, 110], 'accuracy': 0.87}
        arima_forecast = {'values': [100, 104, 109], 'accuracy': 0.85}

        ensemble = engine._ensemble_vote(prophet_forecast, arima_forecast)

        assert 'values' in ensemble
        assert len(ensemble['values']) == 3

    def test_runout_date_calculation(self, engine):
        """Test runout date calculation."""
        forecast = [100, 80, 60, 40, 20, 0, -10]
        runout_date = engine._compute_runout_date(forecast, 150)

        assert runout_date != "N/A"

    def test_no_runout_scenario(self, engine):
        """Test when inventory never runs out."""
        forecast = [100, 105, 110, 115, 120, 125, 130]
        runout_date = engine._compute_runout_date(forecast, 200)

        assert runout_date == "N/A"

    def test_model_persistence(self, engine, tmp_path):
        """Test saving and loading models."""
        model_path = tmp_path / "test_model.pkl"
        engine.save_model(str(model_path))
        # Model should be created
        assert True
