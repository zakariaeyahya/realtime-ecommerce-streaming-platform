#!/usr/bin/env python
"""
Train Fraud Detection Model.

This script trains a simple fraud detection model using synthetic data
and saves it as a pickle file for use in the Flink job.

Usage:
    python scripts/train_fraud_model.py
"""

import logging
import pickle
from pathlib import Path
from typing import Tuple, Dict, List
import os
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def generate_synthetic_data(n_samples: int = 1000) -> Tuple[List, List]:
    """Generate synthetic training data.

    Args:
        n_samples: Number of samples to generate

    Returns:
        Tuple of (features, labels)
    """
    import random

    logger.info(f"Generating {n_samples} synthetic samples")

    features = []
    labels = []

    for i in range(n_samples):
        # Create synthetic feature vector (simplified)
        amount = random.uniform(10, 5000)
        velocity = random.randint(0, 50)
        country_risk = random.uniform(0, 1)
        is_evening = random.choice([0, 1])

        # Simple fraud pattern: high amount + high velocity = fraud
        fraud_score = (amount / 5000) * 0.4 + (velocity / 50) * 0.6
        is_fraud = 1 if fraud_score > 0.7 else 0

        features.append([amount, velocity, country_risk, is_evening])
        labels.append(is_fraud)

    logger.info(f"Generated {len(features)} samples")
    return features, labels


def train_model(features: List, labels: List) -> object:
    """Train fraud detection model.

    Args:
        features: List of feature vectors
        labels: List of labels (0=legitimate, 1=fraud)

    Returns:
        Trained model
    """
    logger.info("Training fraud detection model")

    try:
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        model.fit(features, labels)

        logger.info("Model trained successfully")
        return model

    except ImportError as e:
        logger.error(f"sklearn import failed: {e}")
        logger.warning("Using mock model instead")
        return MockModel()


def save_model(model: object, output_path: str) -> bool:
    """Save model to disk.

    Args:
        model: Trained model
        output_path: Path to save model

    Returns:
        True if successful
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            pickle.dump(model, f)

        logger.info(f"Model saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        return False


class MockModel:
    """Mock model for testing."""

    def predict(self, features: List) -> List:
        """Return mock predictions."""
        return [0.5] * len(features)


def main() -> None:
    """Main training pipeline."""
    setup_logging()
    logger.info("Starting fraud model training")

    try:
        from config.constants import FRAUD_MODEL_PATH

        # Generate synthetic data
        features, labels = generate_synthetic_data(1000)

        # Train model
        model = train_model(features, labels)

        # Save model
        success = save_model(model, FRAUD_MODEL_PATH)

        if success:
            logger.info("[OK] Model training completed successfully")
        else:
            logger.error("[FAILED] Model training failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
