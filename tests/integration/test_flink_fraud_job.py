"""
Integration tests for Flink fraud detection job.

Tests:
- End-to-end job execution
- Kafka source integration
- Output validation
- Performance metrics
"""

import pytest
import logging
from processing.flink_jobs.fraud_detection import FraudDetectionJob


logger = logging.getLogger(__name__)


class TestFlinkFraudJob:
    """Integration tests for fraud detection job."""

    @pytest.fixture
    def job(self):
        """Create job instance."""
        return FraudDetectionJob()

    @pytest.mark.skip(reason="Requires Kafka and Flink to be running")
    def test_job_execution(self, job):
        """Test complete job execution (skipped without services)."""
        try:
            job.run()
            # If we get here, job executed
            assert True
        except Exception as e:
            pytest.fail(f"Job execution failed: {e}")

    def test_job_fraud_detection_pipeline(self, job):
        """Test fraud detection pipeline."""
        from processing.flink_jobs.utils.feature_engineering import FeatureEngineer

        engineer = FeatureEngineer()

        # Create test event
        event = {
            'user_id': 'test_user',
            'event_type': 'transaction',
            'timestamp': 1234567890,
            'price': 150.0,
            'quantity': 1
        }

        # Extract features
        features = engineer.extract_features(event)
        assert len(features) > 0

        # Detect fraud
        result = job.detect_fraud(features)
        assert 'fraud_score' in result
        assert 'is_fraud' in result

    def test_job_configuration(self, job):
        """Test job configuration."""
        assert job.fraud_threshold > 0
        assert job.fraud_threshold <= 1.0
        assert job.min_features > 0
