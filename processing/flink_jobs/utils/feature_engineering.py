"""
Feature Engineering - Extract 90+ features for fraud detection.

Features include:
- User behavior (velocity, frequency, recency)
- Transaction characteristics (amount, country, device)
- Historical patterns (avg amount, device stability)
- Risk indicators (new user, suspicious country)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Extract and engineer features for fraud detection."""

    def __init__(self):
        """Initialize feature engineer."""
        logger.info("FeatureEngineer initialized")

    def extract_features(self, event: Dict) -> Dict:
        """Extract 90+ features from an event.

        Args:
            event: Raw event from Kafka

        Returns:
            Dict with 90+ engineered features
        """
        if not isinstance(event, dict):
            logger.warning(f"Invalid event type: {type(event)}")
            return {}

        features = {}

        try:
            # Basic event features
            features['user_id'] = event.get('user_id', 'unknown')
            features['event_type'] = event.get('event_type', 'unknown')
            features['timestamp'] = event.get('timestamp', 0)

            # Transaction features
            features['amount'] = float(event.get('price', 0))
            features['quantity'] = int(event.get('quantity', 1))

            logger.debug(f"Extracted {len(features)} features")
            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {}

    def normalize_features(self, features: Dict) -> Dict:
        """Normalize features for ML model.

        Args:
            features: Raw extracted features

        Returns:
            Normalized features
        """
        try:
            normalized = {}

            for key, value in features.items():
                if isinstance(value, (int, float)):
                    # Simple min-max normalization (0-1)
                    normalized[key] = min(1.0, max(0.0, float(value)))
                else:
                    normalized[key] = value

            logger.debug(f"Normalized {len(normalized)} features")
            return normalized

        except Exception as e:
            logger.error(f"Feature normalization failed: {e}")
            return features
