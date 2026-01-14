"""Unit tests for Feature Extractor."""

import pytest


class TestFeatureExtractor:
    """Test feature extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor."""
        from processing.flink_jobs.utils.feature_extractor import FeatureExtractor
        return FeatureExtractor()

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes."""
        assert extractor is not None

    def test_extract_user_features(self, extractor):
        """Test extracting user features."""
        events = [
            {'user_id': 'u1', 'item_id': 'i1', 'event_type': 'view'},
            {'user_id': 'u1', 'item_id': 'i2', 'event_type': 'purchase'},
        ]
        features = extractor.extract_user_features('u1', events)
        assert features['user_id'] == 'u1'
        assert features['total_interactions'] == 2

    def test_extract_item_features(self, extractor):
        """Test extracting item features."""
        interactions = [
            {'user_id': 'u1', 'item_id': 'i1', 'event_type': 'view'},
            {'user_id': 'u2', 'item_id': 'i1', 'event_type': 'purchase'},
        ]
        features = extractor.extract_item_features('i1', interactions)
        assert features['item_id'] == 'i1'
        assert features['unique_users'] == 2

    def test_extract_session_features(self, extractor):
        """Test extracting session features."""
        events = [
            {'user_id': 'u1', 'item_id': 'i1', 'event_type': 'view'},
            {'user_id': 'u1', 'item_id': 'i2', 'event_type': 'addtocart'},
        ]
        features = extractor.extract_session_features(events)
        assert features['session_length'] == 2
        assert features['has_cart'] is True

    def test_empty_events(self, extractor):
        """Test with empty events."""
        features = extractor.extract_user_features('u1', [])
        assert features['total_interactions'] == 0
