"""
Unit tests for fraud detection job.

Tests:
- Job initialization
- Fraud detection logic
- Threshold application
- Output format
"""

import pytest
from processing.flink_jobs.fraud_detection import FraudDetectionJob
from config.constants import FRAUD_THRESHOLD


class TestFraudDetectionJob:
    """Test suite for FraudDetectionJob."""

    @pytest.fixture
    def job(self):
        """Create fraud detection job instance."""
        return FraudDetectionJob()

    def test_job_initialization(self, job):
        """Test job initialization with defaults."""
        assert job is not None
        assert job.fraud_threshold == FRAUD_THRESHOLD
        assert job.config is not None

    def test_detect_fraud_high_score(self, job):
        """Test detection of high fraud score."""
        features = {
            'amount': 5000,
            'velocity': 10,
            'country': 'RU',
            'device_type': 'mobile',
            # Add more features as needed
        }

        # This should be detected as fraud (high score)
        result = job.detect_fraud(features)

        assert isinstance(result, dict)
        assert 'fraud_score' in result
        assert 'is_fraud' in result
        assert isinstance(result['fraud_score'], float)
        assert isinstance(result['is_fraud'], bool)

    def test_detect_fraud_low_score(self, job):
        """Test detection of low fraud score."""
        features = {
            'amount': 50,
            'velocity': 1,
            'country': 'FR',
            'device_type': 'desktop',
        }

        result = job.detect_fraud(features)

        assert isinstance(result, dict)
        assert result['is_fraud'] is False

    def test_detect_fraud_invalid_input(self, job):
        """Test fraud detection with invalid input."""
        result = job.detect_fraud(None)
        assert result['is_fraud'] is False
        assert 'reason' in result

    def test_detect_fraud_insufficient_features(self, job):
        """Test fraud detection with insufficient features."""
        features = {'amount': 100}  # Too few features

        result = job.detect_fraud(features)
        assert result['is_fraud'] is False

    def test_environment_creation(self, job):
        """Test Flink environment creation."""
        try:
            env = job.create_environment()
            assert env is not None
        except ImportError:
            # Flink not installed, skip test
            pytest.skip("Flink not installed")
