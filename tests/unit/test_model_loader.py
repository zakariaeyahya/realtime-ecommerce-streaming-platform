"""
Unit tests for model loader.

Tests:
- Model loading
- Model prediction
- Fallback strategies
- Error handling
"""

import pytest
from processing.flink_jobs.utils.model_loader import ModelLoader


class TestModelLoader:
    """Test suite for ModelLoader."""

    @pytest.fixture
    def loader(self):
        """Create model loader instance."""
        return ModelLoader()

    def test_loader_initialization(self, loader):
        """Test model loader initialization."""
        assert loader is not None
        assert loader.model is None  # Not loaded yet
        assert loader.model_path is not None

    def test_load_nonexistent_model(self, loader):
        """Test loading nonexistent model."""
        loader.model_path = '/tmp/nonexistent_model.pkl'
        result = loader.load_model()

        # Should fail gracefully
        assert result is False or loader.model is None

    def test_prepare_input(self, loader):
        """Test input preparation for model."""
        features = {
            'amount': 100.0,
            'velocity': 5,
            'user_id': 'user123',
            'country': 'US'
        }

        input_vector = loader._prepare_input(features)

        assert isinstance(input_vector, list)
        assert len(input_vector) > 0

    def test_get_model_version(self, loader):
        """Test model version retrieval."""
        version = loader._get_model_version()

        assert isinstance(version, str)
