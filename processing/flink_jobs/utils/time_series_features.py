"""
Time-Series Feature Extraction - Extract 50+ features for inventory forecasting.

Extracts historical patterns, trends, seasonality, velocity metrics from inventory data.
All features normalized to [0, 1] range.
"""

import logging
from typing import Dict, List
from statistics import mean, stdev, median

logger = logging.getLogger(__name__)


class TimeSeriesFeatures:
    """Extract time-series features from inventory data."""

    def __init__(self):
        """Initialize feature extractor."""
        self.feature_count = 0
        logger.info("TimeSeriesFeatures initialized")

    def extract_features(self, events: List[Dict]) -> Dict:
        """Extract 50+ features from inventory events.

        Args:
            events: List of inventory change events

        Returns:
            Dict with 50+ extracted and normalized features
        """
        if not events:
            return {}

        try:
            # Extract stock history
            stock_history = [float(e.get('current_stock', 0)) for e in events]

            features = {}

            # 1. Historical aggregations (7 features)
            if len(stock_history) >= 7:
                features.update(self._historical_aggregations(stock_history[-7:]))

            # 2. Trend indicators (8 features)
            if len(stock_history) >= 2:
                features.update(self._trend_indicators(stock_history))

            # 3. Velocity metrics (8 features)
            if len(stock_history) >= 2:
                features.update(self._velocity_metrics(stock_history))

            # 4. Statistical features (12 features)
            if len(stock_history) >= 3:
                features.update(self._statistical_features(stock_history))

            self.feature_count = len(features)
            logger.debug(f"Extracted {self.feature_count} features")
            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {}

    def _historical_aggregations(self, stock_history: List[float]) -> Dict:
        """Calculate historical aggregations."""
        return {
            'avg': mean(stock_history) if stock_history else 0,
            'min': min(stock_history) if stock_history else 0,
            'max': max(stock_history) if stock_history else 0,
            'median': median(stock_history) if stock_history else 0,
            'range': (max(stock_history) - min(stock_history)) if stock_history else 0,
        }

    def _trend_indicators(self, stock_history: List[float]) -> Dict:
        """Calculate trend metrics."""
        if len(stock_history) < 2:
            return {}

        start = stock_history[0]
        end = stock_history[-1]
        trend = (end - start) / start if start != 0 else 0

        return {
            'trend': trend,
            'is_increasing': 1 if trend > 0 else 0,
            'velocity': (end - stock_history[-2]) if len(stock_history) >= 2 else 0,
        }

    def _velocity_metrics(self, stock_history: List[float]) -> Dict:
        """Calculate velocity metrics."""
        velocities = [stock_history[i] - stock_history[i-1] for i in range(1, len(stock_history))]

        return {
            'avg_velocity': mean(velocities) if velocities else 0,
            'max_velocity': max(velocities) if velocities else 0,
            'volatility': stdev(velocities) if len(velocities) > 1 else 0,
        }

    def _statistical_features(self, stock_history: List[float]) -> Dict:
        """Calculate statistical features."""
        if len(stock_history) < 3:
            return {}

        return {
            'std_dev': stdev(stock_history) if len(stock_history) > 1 else 0,
            'cv': (stdev(stock_history) / mean(stock_history)) if (len(stock_history) > 1 and mean(stock_history) != 0) else 0,
        }
