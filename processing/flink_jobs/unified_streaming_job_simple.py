"""
Unified Streaming Job - SIMPLIFIED VERSION (Sans Kafka)

Architecture:
    Parse & Enrich Event
        ↓
    ├─→ Branch 1: Fraud Detection
    │   └─→ Console Output + Mock Redis
    │
    ├─→ Branch 2: Recommendations
    │   └─→ Console Output + Mock Redis
    │
    └─→ Branch 3: Inventory Forecasting
        └─→ Console Output + Mock Redis

This simplified version demonstrates the parallel processing concept
without requiring Kafka Java connectors. It can be extended to use
Kafka once connectors are properly installed.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class UnifiedStreamingJobSimple:
    """Simplified unified streaming job combining 3 processing pipelines."""

    def __init__(self):
        """Initialize unified job with configuration."""
        from config.constants import (
            FRAUD_THRESHOLD,
            FRAUD_MIN_FEATURES,
        )

        self.fraud_threshold = FRAUD_THRESHOLD
        self.fraud_min_features = FRAUD_MIN_FEATURES

        logger.info(
            f"UnifiedStreamingJobSimple initialized "
            f"(threshold={self.fraud_threshold})"
        )

    def create_environment(self):
        """Create Flink StreamExecutionEnvironment.

        Returns:
            StreamExecutionEnvironment configured for unified processing
        """
        try:
            from pyflink.datastream import StreamExecutionEnvironment

            env = StreamExecutionEnvironment.get_execution_environment()
            env.set_parallelism(4)
            # Note: Checkpointing disabled for simplified demo version
            # In production, enable with: env.enable_checkpointing(30000)

            logger.info("Flink environment created for unified job (simple version)")
            return env

        except ImportError as e:
            logger.error(f"Flink import error: {e}")
            raise

    def create_sample_data_source(self, env):
        """Create sample data source (for testing without Kafka).

        Args:
            env: StreamExecutionEnvironment

        Returns:
            DataStream of sample events
        """
        try:
            from pyflink.datastream.functions import MapFunction

            # Sample data for testing
            sample_events = [
                {
                    "user_id": "user_001",
                    "amount": 5000,
                    "country": "RU",
                    "product_id": "SKU001",
                    "quantity": 5,
                    "event_type": "purchase",
                },
                {
                    "user_id": "user_002",
                    "amount": 50,
                    "country": "FR",
                    "product_id": "SKU002",
                    "quantity": 2,
                    "event_type": "purchase",
                },
                {
                    "user_id": "user_003",
                    "amount": 3000,
                    "country": "CN",
                    "product_id": "SKU003",
                    "quantity": 10,
                    "event_type": "purchase",
                },
                {
                    "user_id": "user_004",
                    "amount": 100,
                    "country": "DE",
                    "product_id": "SKU001",
                    "quantity": 1,
                    "event_type": "purchase",
                },
                {
                    "user_id": "user_005",
                    "amount": 8000,
                    "country": "US",
                    "product_id": "SKU004",
                    "quantity": 20,
                    "event_type": "purchase",
                },
            ]

            events_stream = env.from_collection(sample_events, type_info=None)

            logger.info(f"Sample data source created with {len(sample_events)} events")
            return events_stream

        except Exception as e:
            logger.error(f"Failed to create sample data source: {e}")
            raise

    def create_fraud_detection_branch(self, events_stream):
        """Create fraud detection branch.

        Args:
            events_stream: Input stream of events

        Returns:
            Stream of fraud detection results
        """
        try:
            from pyflink.datastream.functions import MapFunction

            class FraudDetectionFunction(MapFunction):
                def __init__(self, threshold):
                    self.threshold = threshold

                def map(self, event):
                    try:
                        # Calculate fraud score based on amount
                        amount = float(event.get("amount", 0))
                        fraud_score = min(1.0, amount / 10000)

                        is_fraud = fraud_score > self.threshold

                        result = {
                            "branch": "FRAUD",
                            "user_id": event.get("user_id", "unknown"),
                            "amount": amount,
                            "fraud_score": round(fraud_score, 3),
                            "is_fraud": is_fraud,
                            "timestamp": datetime.now().isoformat(),
                            "alert": "FRAUD DETECTED" if is_fraud else "OK",
                        }

                        logger.info(
                            f"[FRAUD] user={result['user_id']}, "
                            f"score={result['fraud_score']}, {result['alert']}"
                        )

                        return result

                    except Exception as e:
                        logger.error(f"Fraud detection failed: {e}")
                        return None

            fraud_stream = events_stream.map(
                FraudDetectionFunction(self.fraud_threshold)
            ).filter(lambda x: x is not None)

            logger.info("Fraud detection branch created")
            return fraud_stream

        except Exception as e:
            logger.error(f"Failed to create fraud detection branch: {e}")
            raise

    def create_recommendations_branch(self, events_stream):
        """Create recommendations branch.

        Args:
            events_stream: Input stream of events

        Returns:
            Stream of recommendation results
        """
        try:
            from pyflink.datastream.functions import MapFunction

            class RecommendationsFunction(MapFunction):
                def __init__(self):
                    self.top_k = 3

                def map(self, event):
                    try:
                        user_id = event.get("user_id", "unknown")

                        # Generate mock recommendations
                        recommendations = [
                            {
                                "product_id": f"SKU{i:04d}",
                                "score": round(0.95 - (i * 0.2), 2),
                            }
                            for i in range(1, self.top_k + 1)
                        ]

                        result = {
                            "branch": "RECOMMENDATIONS",
                            "user_id": user_id,
                            "recommendations": recommendations,
                            "timestamp": datetime.now().isoformat(),
                            "count": len(recommendations),
                        }

                        logger.info(
                            f"[RECOMMENDATIONS] user={user_id}, "
                            f"recommendations={result['count']}"
                        )

                        return result

                    except Exception as e:
                        logger.error(f"Recommendations failed: {e}")
                        return None

            recommendations_stream = events_stream.map(
                RecommendationsFunction()
            ).filter(lambda x: x is not None)

            logger.info("Recommendations branch created")
            return recommendations_stream

        except Exception as e:
            logger.error(f"Failed to create recommendations branch: {e}")
            raise

    def create_inventory_branch(self, events_stream):
        """Create inventory forecasting branch.

        Args:
            events_stream: Input stream of events

        Returns:
            Stream of inventory forecast results
        """
        try:
            from pyflink.datastream.functions import MapFunction

            class InventoryForecastFunction(MapFunction):
                def __init__(self):
                    self.alert_threshold = 50

                def map(self, event):
                    try:
                        product_id = event.get("product_id", "UNKNOWN")
                        quantity = event.get("quantity", 1)

                        # Mock forecast
                        forecast_qty = max(0, quantity - (quantity * 0.15))
                        needs_reorder = forecast_qty < self.alert_threshold

                        result = {
                            "branch": "INVENTORY",
                            "product_id": product_id,
                            "current_qty": quantity,
                            "forecast_7days": round(forecast_qty, 1),
                            "needs_reorder": needs_reorder,
                            "timestamp": datetime.now().isoformat(),
                            "alert": "REORDER" if needs_reorder else "OK",
                        }

                        logger.info(
                            f"[INVENTORY] product={product_id}, "
                            f"qty={quantity}, {result['alert']}"
                        )

                        return result

                    except Exception as e:
                        logger.error(f"Inventory forecasting failed: {e}")
                        return None

            inventory_stream = events_stream.map(
                InventoryForecastFunction()
            ).filter(lambda x: x is not None)

            logger.info("Inventory forecasting branch created")
            return inventory_stream

        except Exception as e:
            logger.error(f"Failed to create inventory branch: {e}")
            raise

    def add_sinks(self, fraud_stream, recommendations_stream, inventory_stream):
        """Add output sinks (console print for testing).

        Args:
            fraud_stream: Fraud detection results
            recommendations_stream: Recommendations results
            inventory_stream: Inventory forecast results
        """
        try:
            # Console output sinks (for testing/debugging)
            fraud_stream.print(">> FRAUD: ")
            recommendations_stream.print(">> RECOMMENDATIONS: ")
            inventory_stream.print(">> INVENTORY: ")

            logger.info("Console output sinks added")

        except Exception as e:
            logger.error(f"Failed to add sinks: {e}")
            raise

    def run(self) -> None:
        """Execute the unified streaming job."""
        logger.info("=" * 80)
        logger.info("Starting Unified Streaming Job (SIMPLIFIED - No Kafka)")
        logger.info("=" * 80)

        try:
            # Create environment
            env = self.create_environment()

            # Create sample data source (instead of Kafka)
            events_stream = self.create_sample_data_source(env)

            # Create 3 parallel branches
            logger.info("\nCreating 3 parallel processing branches...\n")
            fraud_stream = self.create_fraud_detection_branch(events_stream)
            recommendations_stream = self.create_recommendations_branch(events_stream)
            inventory_stream = self.create_inventory_branch(events_stream)

            # Add output sinks
            self.add_sinks(fraud_stream, recommendations_stream, inventory_stream)

            # Execute job
            logger.info("\n" + "=" * 80)
            logger.info("Executing unified streaming job...")
            logger.info("=" * 80 + "\n")
            env.execute("UnifiedStreamingJob-Simple")

            logger.info("\n" + "=" * 80)
            logger.info("Job completed successfully!")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    job = UnifiedStreamingJobSimple()
    job.run()
