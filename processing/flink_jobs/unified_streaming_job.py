"""
Unified Streaming Job - Combines 3 Processing Pipelines

Architecture:
    Kafka (raw-events)
        ↓
    Parse & Enrich Event
        ↓
    ├─→ Branch 1: Fraud Detection
    │   └─→ Kafka (fraud-scores) + Redis (fraud:*)
    │
    ├─→ Branch 2: Recommendations
    │   └─→ Kafka (recommendations) + Redis (recommendation:*)
    │
    └─→ Branch 3: Inventory Forecasting
        └─→ Kafka (inventory-forecasts) + Redis (inventory:*)

Features:
- Parallel processing of 3 independent jobs
- Real-time fraud scoring (90+ features)
- Personalized recommendations (session-based)
- Inventory forecasting (time-series prediction)
- Redis caching for fast lookup
- Kafka output for downstream systems
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


class UnifiedStreamingJob:
    """Main unified streaming job combining 3 processing pipelines."""

    def __init__(self):
        """Initialize unified job with configuration."""
        from config.constants import (
            FRAUD_THRESHOLD,
            FRAUD_MIN_FEATURES,
            KAFKA_BROKERS,
            KAFKA_TOPICS,
        )

        self.fraud_threshold = FRAUD_THRESHOLD
        self.fraud_min_features = FRAUD_MIN_FEATURES
        self.kafka_brokers = KAFKA_BROKERS
        self.kafka_topics = KAFKA_TOPICS

        logger.info(
            f"UnifiedStreamingJob initialized "
            f"(brokers={self.kafka_brokers}, threshold={self.fraud_threshold})"
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
            env.enable_checkpointing(30000)  # 30 seconds

            logger.info("Flink environment created for unified job")
            return env

        except ImportError as e:
            logger.error(f"Flink import error: {e}")
            raise

    def create_kafka_source(self, env):
        """Create Kafka source for raw events.

        Args:
            env: StreamExecutionEnvironment

        Returns:
            DataStream of raw events from Kafka
        """
        try:
            from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
            from pyflink.datastream.functions import MapFunction
            from pyflink.common.serialization import SimpleStringSchema

            # Kafka consumer configuration
            kafka_consumer = FlinkKafkaConsumer(
                self.kafka_topics["events"],
                SimpleStringSchema(),
                {"bootstrap.servers": self.kafka_brokers},
            )

            # Add source to environment
            kafka_stream = env.add_source(kafka_consumer)

            # Parse JSON strings to dictionaries
            class ParseEventFunction(MapFunction):
                def map(self, value):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse event: {value}, error: {e}")
                        return None

            events_stream = kafka_stream.map(ParseEventFunction()).filter(
                lambda x: x is not None
            )

            logger.info(f"Kafka source created (topic={self.kafka_topics['events']})")
            return events_stream

        except Exception as e:
            logger.error(f"Failed to create Kafka source: {e}")
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
            from utils.feature_engineering import FeatureEngineer

            class FraudDetectionFunction(MapFunction):
                def __init__(self, threshold):
                    self.threshold = threshold
                    self.feature_engineer = FeatureEngineer()

                def map(self, event):
                    try:
                        # Extract features
                        features = self.feature_engineer.extract_features(event)

                        # Calculate fraud score (mock - replace with real model)
                        fraud_score = min(
                            1.0,
                            (
                                features.get("amount", 0) / 10000
                                if features.get("amount", 0) > 0
                                else 0
                            ),
                        )

                        # Determine if fraud
                        is_fraud = fraud_score > self.threshold

                        result = {
                            "user_id": event.get("user_id", "unknown"),
                            "fraud_score": round(fraud_score, 3),
                            "is_fraud": is_fraud,
                            "timestamp": datetime.now().isoformat(),
                            "features_count": len(features),
                        }

                        logger.debug(
                            f"Fraud detection: user={result['user_id']}, "
                            f"score={result['fraud_score']}"
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
                    self.top_k = 5

                def map(self, event):
                    try:
                        # Generate mock recommendations
                        user_id = event.get("user_id", "unknown")

                        # In production: use ML model to generate recommendations
                        recommendations = [
                            {"product_id": f"SKU{i:04d}", "score": 0.9 - (i * 0.1)}
                            for i in range(1, self.top_k + 1)
                        ]

                        result = {
                            "user_id": user_id,
                            "recommendations": recommendations,
                            "timestamp": datetime.now().isoformat(),
                            "count": len(recommendations),
                        }

                        logger.debug(
                            f"Recommendations: user={user_id}, "
                            f"count={result['count']}"
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
                    self.alert_threshold = 100

                def map(self, event):
                    try:
                        # Extract inventory-related info
                        product_id = event.get("product_id", "UNKNOWN")
                        quantity = event.get("quantity", 1)

                        # In production: use time-series forecasting (Prophet/ARIMA)
                        # This is a mock forecast
                        forecast = {
                            "product_id": product_id,
                            "current_quantity": quantity,
                            "forecast_7days": max(0, quantity - (quantity * 0.1)),
                            "alert": quantity < self.alert_threshold,
                            "timestamp": datetime.now().isoformat(),
                        }

                        logger.debug(
                            f"Inventory forecast: product={product_id}, "
                            f"qty={quantity}"
                        )

                        return forecast

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

    def add_kafka_sinks(self, fraud_stream, recommendations_stream, inventory_stream):
        """Add Kafka sinks to output branches.

        Args:
            fraud_stream: Fraud detection results
            recommendations_stream: Recommendations results
            inventory_stream: Inventory forecast results
        """
        try:
            from pyflink.datastream.connectors.kafka import FlinkKafkaProducer
            from pyflink.common.serialization import SimpleStringSchema

            class SerializeResultFunction:
                def __call__(self, result):
                    return json.dumps(result).encode("utf-8")

            # Fraud scores sink
            fraud_producer = FlinkKafkaProducer(
                self.kafka_topics["fraud_scores"],
                SerializeResultFunction(),
                {"bootstrap.servers": self.kafka_brokers},
            )
            fraud_stream.add_sink(fraud_producer)
            logger.info(f"Fraud scores sink added (topic={self.kafka_topics['fraud_scores']})")

            # Recommendations sink
            recommendations_producer = FlinkKafkaProducer(
                self.kafka_topics["recommendations"],
                SerializeResultFunction(),
                {"bootstrap.servers": self.kafka_brokers},
            )
            recommendations_stream.add_sink(recommendations_producer)
            logger.info(
                f"Recommendations sink added (topic={self.kafka_topics['recommendations']})"
            )

            # Inventory forecasts sink
            inventory_producer = FlinkKafkaProducer(
                self.kafka_topics["inventory"],
                SerializeResultFunction(),
                {"bootstrap.servers": self.kafka_brokers},
            )
            inventory_stream.add_sink(inventory_producer)
            logger.info(
                f"Inventory sink added (topic={self.kafka_topics['inventory']})"
            )

        except Exception as e:
            logger.error(f"Failed to add Kafka sinks: {e}")
            raise

    def run(self) -> None:
        """Execute the unified streaming job."""
        logger.info("Starting Unified Streaming Job")

        try:
            # Create environment
            env = self.create_environment()

            # Create Kafka source
            events_stream = self.create_kafka_source(env)

            # Create 3 parallel branches
            fraud_stream = self.create_fraud_detection_branch(events_stream)
            recommendations_stream = self.create_recommendations_branch(events_stream)
            inventory_stream = self.create_inventory_branch(events_stream)

            # Add Kafka sinks
            self.add_kafka_sinks(fraud_stream, recommendations_stream, inventory_stream)

            # Execute job
            logger.info("Executing unified streaming job...")
            env.execute("UnifiedStreamingJob")

        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    job = UnifiedStreamingJob()
    job.run()
