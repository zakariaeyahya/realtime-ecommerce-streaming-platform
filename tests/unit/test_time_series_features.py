"""Unit tests for time-series feature extraction."""

import pytest
from processing.flink_jobs.utils.time_series_features import TimeSeriesFeatures


class TestTimeSeriesFeatures:
    """Test cases for TimeSeriesFeatures."""

    @pytest.fixture
    def extractor(self):
        """Create feature extractor."""
        return TimeSeriesFeatures()

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes."""
        assert extractor is not None

    def test_feature_extraction_with_data(self, extractor):
        """Test feature extraction with valid data."""
        events = [
            {'current_stock': 100 + i*5, 'timestamp': 1000+i*100}
            for i in range(20)
        ]

        features = extractor.extract_features(events)
        assert len(features) > 0

    def test_empty_events_handled(self, extractor):
        """Test empty events handled gracefully."""
        features = extractor.extract_features([])
        assert isinstance(features, dict)

    def test_historical_aggregations(self, extractor):
        """Test historical aggregation features."""
        stock_history = [100, 105, 110, 95, 90]
        aggs = extractor._historical_aggregations(stock_history)

        assert 'avg' in aggs
        assert 'min' in aggs
        assert 'max' in aggs

    def test_trend_indicators(self, extractor):
        """Test trend indicator calculation."""
        stock_history = [100, 105, 110, 115, 120]
        trends = extractor._trend_indicators(stock_history)

        assert 'trend' in trends
        assert trends['is_increasing'] == 1

    def test_feature_count(self, extractor):
        """Test feature count reaches target."""
        events = [
            {'current_stock': 100 + i*2, 'timestamp': 1000+i*100}
            for i in range(30)
        ]

        extractor.extract_features(events)
        assert extractor.feature_count > 0
