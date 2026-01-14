"""
Unit tests for feature engineering module.

Tests:
- Feature extraction from various event types
- Feature normalization
- Edge cases and invalid inputs
- Feature counts and types
"""

import pytest
from processing.flink_jobs.utils.feature_engineering import FeatureEngineer


class TestFeatureEngineer:
    """Test suite for FeatureEngineer."""

    @pytest.fixture
    def engineer(self):
        """Create feature engineer instance."""
        return FeatureEngineer()

    def test_extract_features_valid_event(self, engineer):
        """Test feature extraction from valid event."""
        event = {
            'user_id': 'user123',
            'event_type': 'transaction',
            'timestamp': 1234567890,
            'price': 99.99,
            'quantity': 2
        }

        features = engineer.extract_features(event)

        assert isinstance(features, dict)
        assert len(features) > 0
        assert features.get('user_id') == 'user123'
        assert features.get('amount') == 99.99

    def test_extract_features_empty_event(self, engineer):
        """Test feature extraction from empty event."""
        event = {}
        features = engineer.extract_features(event)

        assert isinstance(features, dict)

    def test_extract_features_invalid_input(self, engineer):
        """Test feature extraction with invalid input."""
        result = engineer.extract_features(None)
        assert result == {}

        result = engineer.extract_features("invalid")
        assert result == {}

    def test_normalize_features(self, engineer):
        """Test feature normalization."""
        features = {
            'amount': 150.0,
            'velocity': 5,
            'user_id': 'user123'
        }

        normalized = engineer.normalize_features(features)

        assert isinstance(normalized, dict)
        # Normalized numeric values should be 0-1
        for key, value in normalized.items():
            if isinstance(value, float) and key != 'user_id':
                assert 0.0 <= value <= 1.0

    def test_normalize_features_edge_cases(self, engineer):
        """Test normalization with edge case values."""
        features = {
            'amount': -100.0,  # Negative
            'velocity': 1000.0,  # Very large
            'user_id': 'user123'
        }

        normalized = engineer.normalize_features(features)

        # Should still return dict
        assert isinstance(normalized, dict)
