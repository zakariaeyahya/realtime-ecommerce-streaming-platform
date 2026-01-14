"""Evaluate inventory forecasting models."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def main():
    """Evaluate forecasting models."""
    try:
        from processing.flink_jobs.utils.forecasting_engine import ForecastingEngine

        logger.info("Evaluating inventory models...")

        # Generate synthetic test data
        import random
        random.seed(123)

        test_interactions = []
        for item_id in range(5):
            for day in range(30):
                stock = 400 - day * (1.5 + random.uniform(-0.5, 0.5))
                test_interactions.append({
                    'item_id': f'sku-{item_id}',
                    'stock': max(0, stock),
                    'day': day
                })

        logger.info(f"Generated {len(test_interactions)} test samples")

        # Load and evaluate
        engine = ForecastingEngine()

        # Extract test stock history
        stock_history = [float(e['stock']) for e in test_interactions[:50]]

        # Generate predictions
        predictions = engine.forecast(stock_history, periods=7)

        # Calculate metrics
        accuracy = predictions.get('accuracy', 0)
        runout_date = predictions.get('runout_date', 'N/A')

        logger.info(f"Evaluation metrics:")
        logger.info(f"  - Accuracy: {accuracy*100:.1f}%")
        logger.info(f"  - Runout Date: {runout_date}")
        logger.info(f"  - Forecast Values: {predictions.get('forecast', [])}")

        print(f"[OK] Evaluation completed successfully")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
