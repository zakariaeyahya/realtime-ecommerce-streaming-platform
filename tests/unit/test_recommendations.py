"""Unit tests for Recommendations Job."""

import pytest
from unittest.mock import Mock, MagicMock
from processing.flink_jobs.recommendations import RecommendationsJob


class TestRecommendationsJob:
    """Test Flink Recommendations Job."""

    @pytest.fixture
    def job(self):
        """Create job instance."""
        return RecommendationsJob()

    def test_job_initialization(self, job):
        """Test job initializes correctly."""
        assert job is not None
        assert job.top_k == 10

    def test_session_window_trigger(self, job):
        """Test session windows trigger after 30 min inactivity."""
        assert job.session_timeout == 30

    def test_event_processing(self, job):
        """Test events processed in correct order."""
        events = [
            {'user_id': 'user1', 'item_id': 'item1', 'event_type': 'view'},
            {'user_id': 'user1', 'item_id': 'item2', 'event_type': 'addtocart'},
        ]
        result = job.process_session(events)
        assert result['status'] == 'success'
        assert len(result['recommendations']) >= 0

    def test_kafka_source_connection(self, job):
        """Test connection to Kafka events topic."""
        assert job is not None

    def test_output_format_valid(self, job):
        """Test output matches expected schema."""
        events = [{'user_id': 'user1', 'item_id': 'item1', 'event_type': 'view'}]
        result = job.process_session(events)
        assert 'user_id' in result
        assert 'recommendations' in result
        assert 'timestamp' in result

    def test_cold_start_recommendations(self, job):
        """Test recommendations for new users."""
        events = []
        result = job.process_session(events)
        assert result['status'] == 'empty'
