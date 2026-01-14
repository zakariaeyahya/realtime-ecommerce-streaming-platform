"""Train inventory forecasting models (Prophet + ARIMA)."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def main():
    """Train inventory forecasting models."""
    try:
        from processing.flink_jobs.utils.forecasting_engine import ForecastingEngine

        logger.info("Training inventory forecasting models...")

        # Generate synthetic training data
        import random
        random.seed(42)

        interactions = []
        for item_id in range(10):
            for day in range(100):
                stock = 500 - day * (2 + random.uniform(-1, 1))
                interactions.append({
                    'item_id': f'sku-{item_id}',
                    'stock': max(0, stock),
                    'day': day
                })

        logger.info(f"Generated {len(interactions)} training samples")

        # Train engine
        engine = ForecastingEngine(config={'forecast_periods': 7})

        # Extract stock history
        stock_history = [float(e['stock']) for e in interactions[:100]]

        # Generate forecasts (training)
        forecast = engine.forecast(stock_history)

        logger.info(f"Model training completed")
        logger.info(f"Forecast accuracy: {forecast.get('accuracy', 0)}")

        # Save models
        model_path = Path(__file__).parent.parent / 'processing' / 'models' / 'inventory_forecast_models.joblib'
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
