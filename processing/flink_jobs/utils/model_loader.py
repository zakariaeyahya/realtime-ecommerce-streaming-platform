"""
Model Loader - Load and manage ML models for fraud detection.

Handles:
- Loading pickled models
- Model versioning
- Fallback strategies
- Model performance tracking
"""

import logging
import os
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load and manage fraud detection ML models."""

    def __init__(self, model_path: Optional[str] = None):
        """Initialize model loader.

        Args:
            model_path: Path to pickled model file
        """
        from config.constants import FRAUD_MODEL_PATH

        self.model_path = model_path or os.getenv('FRAUD_MODEL_PATH', FRAUD_MODEL_PATH)
        self.model = None
        self.model_version = None
        self.loaded_at = None

        logger.info(f"ModelLoader initialized (path={self.model_path})")

    def load_model(self) -> bool:
        """Load ML model from disk.

        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            import joblib

            model_file = Path(self.model_path)

            if not model_file.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                return False

            self.model = joblib.load(self.model_path)
            self.model_version = self._get_model_version()

            from datetime import datetime
            self.loaded_at = datetime.now().isoformat()

            logger.info(f"Model loaded successfully (version={self.model_version})")
            return True

        except ImportError as e:
            logger.error(f"joblib import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            return False

    def predict(self, features: dict) -> Optional[float]:
        """Make fraud prediction using loaded model.

        Args:
            features: Dictionary of engineered features

        Returns:
            Fraud score (0-1) or None if prediction failed
        """
        if self.model is None:
            logger.warning("Model not loaded. Call load_model() first")
            return None

        try:
            # Convert features dict to model input format
            feature_vector = self._prepare_input(features)

            # Get prediction
            score = self.model.predict([feature_vector])[0]

            logger.debug(f"Prediction: {score}")
            return float(score)

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

    def _prepare_input(self, features: dict) -> list:
        """Prepare features for model input.

        Args:
            features: Dictionary of features

        Returns:
            List of feature values in model's expected order
        """
        # TODO: Implement proper feature ordering
        return list(features.values())

    def _get_model_version(self) -> str:
        """Get model version from file metadata.

        Returns:
            Model version string
        """
        try:
            model_file = Path(self.model_path)
            stat = model_file.stat()
            return f"v1.0_{stat.st_mtime}"
        except Exception:
            return "unknown"
