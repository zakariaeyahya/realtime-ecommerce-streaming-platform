"""Train collaborative filtering model for recommendations."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def main():
    """Train recommendation model."""
    try:
        from processing.flink_jobs.utils.recommendation_engine import RecommendationEngine

        logger.info("Training recommendation model...")

        # Create synthetic training data
        interactions = [
            {'user_id': f'u{i%10}', 'item_id': f'i{j%50}', 'event_type': 'view'}
            for i in range(1000)
            for j in range(10)
        ]

        # Train engine
        engine = RecommendationEngine(k_neighbors=50)
        engine.build_item_vectors(interactions)
        engine.compute_similarities()

        # Save model
        model_path = Path(__file__).parent.parent / 'processing' / 'models' / 'recommendation_model.pkl'
        model_path.parent.mkdir(parents=True, exist_ok=True)

        engine.save_model(str(model_path))

        logger.info(f"Model saved to {model_path}")
        print(f"[OK] Model training completed successfully")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
