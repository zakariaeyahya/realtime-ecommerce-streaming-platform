"""
Unified Streaming Job - Combines 3 Processing Pipelines (Full Kafka Version)

Architecture:
    Kafka (raw-events)
        |
    Parse & Enrich Event
        |
    +---> Branch 1: Fraud Detection
    |   +---> Kafka (fraud-scores)
    |
    +---> Branch 2: Recommendations
    |   +---> Kafka (recommendations)
    |
    +---> Branch 3: Inventory Forecasting
        +---> Kafka (inventory-changes)

Features:
- Parallel processing of 3 independent jobs
- Real-time fraud scoring
- Personalized recommendations (session-based)
- Inventory forecasting
- Kafka input/output for real streaming
"""

import logging
import os
import json
import sys
from typing import Dict
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class UnifiedStreamingJob:
    """Main unified streaming job combining 3 processing pipelines with Kafka."""

    def __init__(self):
        """Initialize unified job with configuration."""
        from config.constants import (
            FRAUD_THRESHOLD,
            KAFKA_TOPICS,
        )

        self.fraud_threshold = FRAUD_THRESHOLD
        self.kafka_topics = KAFKA_TOPICS
        # Inside Docker: kafka:9092, outside: localhost:9092
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")

        logger.info(
            f"UnifiedStreamingJob initialized "
            f"(brokers={self.kafka_brokers}, threshold={self.fraud_threshold})"
        )

    def create_environment(self):
        """Create Flink StreamExecutionEnvironment.

        Returns:
            StreamExecutionEnvironment configured for unified processing
        """
        from pyflink.datastream import StreamExecutionEnvironment
        from pyflink.common import Configuration

        config = Configuration()
        config.set_string("pipeline.jars", "file:///opt/flink/lib/flink-connector-kafka-3.0.1-1.18.jar;file:///opt/flink/lib/kafka-clients-3.6.0.jar")

        env = StreamExecutionEnvironment.get_execution_environment(config)
        env.set_parallelism(2)
        env.enable_checkpointing(30000)  # 30 seconds

        logger.info("Flink environment created for unified job")
        return env

    def create_kafka_source(self, env):
        """Create Kafka source for raw events.

        Args:
            env: StreamExecutionEnvironment

        Returns:
            DataStream of raw events from Kafka
        """
        from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
        from pyflink.common.serialization import SimpleStringSchema
        from pyflink.datastream.functions import MapFunction
        from pyflink.common.watermark_strategy import WatermarkStrategy

        topic = self.kafka_topics["events"]

        kafka_source = (
            KafkaSource.builder()
            .set_bootstrap_servers(self.kafka_brokers)
            .set_topics(topic)
            .set_group_id("unified-streaming-job")
            .set_starting_offsets(KafkaOffsetsInitializer.earliest())
            .set_value_only_deserializer(SimpleStringSchema())
            .set_property("partition.discovery.interval.ms", "10000")
            .build()
        )

        kafka_stream = env.from_source(
            kafka_source,
            WatermarkStrategy.no_watermarks(),
            "KafkaSource-raw-events",
        )

        # Parse JSON strings to dictionaries
        class ParseEventFunction(MapFunction):
            def map(self, value):
                try:
                    return json.loads(value)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse event: {e}")
                    return None

        events_stream = kafka_stream.map(ParseEventFunction()).filter(
            lambda x: x is not None
        )

        logger.info(f"Kafka source created (topic={topic})")
        return events_stream

    def create_fraud_detection_branch(self, events_stream):
        """Create fraud detection branch.

        Args:
            events_stream: Input stream of events

        Returns:
            Stream of fraud detection results as JSON strings
        """
        from pyflink.datastream.functions import MapFunction

        class FraudDetectionFunction(MapFunction):
            def __init__(self, threshold):
                self.threshold = threshold

            def map(self, event):
                try:
                    amount = float(event.get("amount", event.get("price", 0)))
                    fraud_score = min(1.0, amount / 10000 if amount > 0 else 0)
                    is_fraud = fraud_score > self.threshold

                    result = {
                        "user_id": event.get("user_id", "unknown"),
                        "fraud_score": round(fraud_score, 3),
                        "is_fraud": is_fraud,
                        "amount": amount,
                        "timestamp": datetime.now().isoformat(),
                        "alert": "FRAUD DETECTED" if is_fraud else "OK",
                    }

                    if is_fraud:
                        logger.warning(
                            f"[FRAUD] user={result['user_id']}, "
                            f"score={result['fraud_score']}, amount={amount}"
                        )

                    return json.dumps(result)

                except Exception as e:
                    logger.error(f"Fraud detection failed: {e}")
                    return None

        fraud_stream = events_stream.map(
            FraudDetectionFunction(self.fraud_threshold)
        ).filter(lambda x: x is not None)

        logger.info("Fraud detection branch created")
        return fraud_stream

    def create_recommendations_branch(self, events_stream):
        """Create recommendations branch.

        Args:
            events_stream: Input stream of events

        Returns:
            Stream of recommendation results as JSON strings
        """
        from pyflink.datastream.functions import MapFunction

        class RecommendationsFunction(MapFunction):
            def __init__(self):
                self.top_k = 5

            def map(self, event):
                try:
                    user_id = event.get("user_id", "unknown")
                    item_id = event.get("item_id", event.get("product_id", ""))

                    recommendations = [
                        {"product_id": f"SKU{i:04d}", "score": round(0.95 - (i * 0.15), 2)}
                        for i in range(1, self.top_k + 1)
                    ]

                    result = {
                        "user_id": user_id,
                        "source_item": item_id,
                        "recommendations": recommendations,
                        "timestamp": datetime.now().isoformat(),
                        "count": len(recommendations),
                    }

                    return json.dumps(result)

                except Exception as e:
                    logger.error(f"Recommendations failed: {e}")
                    return None

        recommendations_stream = events_stream.map(
            RecommendationsFunction()
        ).filter(lambda x: x is not None)

        logger.info("Recommendations branch created")
        return recommendations_stream

    def create_inventory_branch(self, events_stream):
        """Create inventory forecasting branch.

        Args:
            events_stream: Input stream of events

        Returns:
            Stream of inventory forecast results as JSON strings
        """
        from pyflink.datastream.functions import MapFunction

        class InventoryForecastFunction(MapFunction):
            def __init__(self):
                self.alert_threshold = 100

            def map(self, event):
                try:
                    product_id = event.get("product_id", event.get("item_id", "UNKNOWN"))
                    quantity = int(event.get("quantity", 1))

                    forecast_qty = max(0, quantity - int(quantity * 0.1))
                    needs_reorder = forecast_qty < self.alert_threshold

                    result = {
                        "product_id": product_id,
                        "current_quantity": quantity,
                        "forecast_7days": forecast_qty,
                        "needs_reorder": needs_reorder,
                        "timestamp": datetime.now().isoformat(),
                        "alert": "REORDER NEEDED" if needs_reorder else "OK",
                    }

                    return json.dumps(result)

                except Exception as e:
                    logger.error(f"Inventory forecasting failed: {e}")
                    return None

        inventory_stream = events_stream.map(
            InventoryForecastFunction()
        ).filter(lambda x: x is not None)

        logger.info("Inventory forecasting branch created")
        return inventory_stream

    def add_kafka_sinks(self, fraud_stream, recommendations_stream, inventory_stream):
        """Add Kafka sinks to output branches.

        Args:
            fraud_stream: Fraud detection results (JSON strings)
            recommendations_stream: Recommendations results (JSON strings)
            inventory_stream: Inventory forecast results (JSON strings)
        """
        from pyflink.datastream.connectors.kafka import KafkaSink, KafkaRecordSerializationSchema
        from pyflink.common.serialization import SimpleStringSchema

        def create_sink(topic: str) -> KafkaSink:
            return (
                KafkaSink.builder()
                .set_bootstrap_servers(self.kafka_brokers)
                .set_record_serializer(
                    KafkaRecordSerializationSchema.builder()
                    .set_topic(topic)
                    .set_value_serialization_schema(SimpleStringSchema())
                    .build()
                )
                .build()
            )

        # Fraud scores sink
        fraud_stream.sink_to(create_sink(self.kafka_topics["fraud_scores"]))
        logger.info(f"Fraud sink added (topic={self.kafka_topics['fraud_scores']})")

        # Recommendations sink
        recommendations_stream.sink_to(create_sink(self.kafka_topics["recommendations"]))
        logger.info(f"Recommendations sink added (topic={self.kafka_topics['recommendations']})")

        # Inventory sink
        inventory_stream.sink_to(create_sink(self.kafka_topics["inventory"]))
        logger.info(f"Inventory sink added (topic={self.kafka_topics['inventory']})")

    def add_console_sinks(self, fraud_stream, recommendations_stream, inventory_stream):
        """Add console print sinks for debugging.

        Args:
            fraud_stream: Fraud detection results
            recommendations_stream: Recommendations results
            inventory_stream: Inventory forecast results
        """
        fraud_stream.print(">> FRAUD: ")
        recommendations_stream.print(">> RECO: ")
        inventory_stream.print(">> INVENTORY: ")
        logger.info("Console output sinks added (for debugging)")

    def run(self) -> None:
        """Execute the unified streaming job."""
        logger.info("=" * 80)
        logger.info("Starting Unified Streaming Job (FULL - With Kafka)")
        logger.info(f"Kafka brokers: {self.kafka_brokers}")
        logger.info(f"Input topic: {self.kafka_topics['events']}")
        logger.info(f"Output topics: {self.kafka_topics['fraud_scores']}, "
                     f"{self.kafka_topics['recommendations']}, "
                     f"{self.kafka_topics['inventory']}")
        logger.info("=" * 80)

        try:
            # Create environment
            env = self.create_environment()

            # Create Kafka source
            events_stream = self.create_kafka_source(env)

            # Create 3 parallel branches
            logger.info("Creating 3 parallel processing branches...")
            fraud_stream = self.create_fraud_detection_branch(events_stream)
            recommendations_stream = self.create_recommendations_branch(events_stream)
            inventory_stream = self.create_inventory_branch(events_stream)

            # Add Kafka sinks (output to topics)
            self.add_kafka_sinks(fraud_stream, recommendations_stream, inventory_stream)

            # Also add console sinks for debugging
            self.add_console_sinks(fraud_stream, recommendations_stream, inventory_stream)

            # Execute job
            logger.info("=" * 80)
            logger.info("Executing unified streaming job (streaming mode)...")
            logger.info("Job will run continuously until stopped (Ctrl+C)")
            logger.info("=" * 80)
            env.execute("UnifiedStreamingJob-Kafka")

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
