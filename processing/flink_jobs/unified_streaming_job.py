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
"""

import logging
import os
import json
import sys
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
        from config.constants import FRAUD_THRESHOLD, KAFKA_TOPICS

        self.fraud_threshold = FRAUD_THRESHOLD
        self.kafka_topics = KAFKA_TOPICS
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")

        logger.info(
            f"UnifiedStreamingJob initialized "
            f"(brokers={self.kafka_brokers}, threshold={self.fraud_threshold})"
        )

    def run(self) -> None:
        """Execute the unified streaming job using Table API."""
        logger.info("=" * 80)
        logger.info("Starting Unified Streaming Job (FULL - With Kafka)")
        logger.info(f"Kafka brokers: {self.kafka_brokers}")
        logger.info(f"Input topic: {self.kafka_topics['events']}")
        logger.info("=" * 80)

        try:
            from pyflink.table import EnvironmentSettings, TableEnvironment

            # Create Table Environment
            env_settings = EnvironmentSettings.in_streaming_mode()
            t_env = TableEnvironment.create(env_settings)
            t_env.get_config().set("parallelism.default", "2")

            logger.info("Table environment created")

            # Create Kafka source table
            t_env.execute_sql(f"""
                CREATE TABLE raw_events (
                    `raw_value` STRING
                ) WITH (
                    'connector' = 'kafka',
                    'topic' = '{self.kafka_topics["events"]}',
                    'properties.bootstrap.servers' = '{self.kafka_brokers}',
                    'properties.group.id' = 'unified-streaming-job',
                    'scan.startup.mode' = 'earliest-offset',
                    'format' = 'raw'
                )
            """)
            logger.info(f"Kafka source created (topic={self.kafka_topics['events']})")

            # Create Kafka sink tables
            for name, topic in [
                ("fraud_sink", self.kafka_topics["fraud_scores"]),
                ("reco_sink", self.kafka_topics["recommendations"]),
                ("inventory_sink", self.kafka_topics["inventory"]),
            ]:
                t_env.execute_sql(f"""
                    CREATE TABLE {name} (
                        `result` STRING
                    ) WITH (
                        'connector' = 'kafka',
                        'topic' = '{topic}',
                        'properties.bootstrap.servers' = '{self.kafka_brokers}',
                        'format' = 'raw'
                    )
                """)
                logger.info(f"Kafka sink created: {name} -> {topic}")

            # Create print sink for debugging
            t_env.execute_sql("""
                CREATE TABLE print_sink (
                    `result` STRING
                ) WITH (
                    'connector' = 'print'
                )
            """)

            # Register UDFs for processing
            from pyflink.table.udf import udf
            from pyflink.table import DataTypes

            threshold = self.fraud_threshold

            @udf(result_type=DataTypes.STRING())
            def detect_fraud(raw_value: str) -> str:
                try:
                    event = json.loads(raw_value)
                    amount = float(event.get("price", event.get("amount", 0)))
                    fraud_score = min(1.0, amount / 10000 if amount > 0 else 0)
                    is_fraud = fraud_score > threshold
                    return json.dumps({
                        "user_id": event.get("user_id", "unknown"),
                        "fraud_score": round(fraud_score, 3),
                        "is_fraud": is_fraud,
                        "amount": amount,
                        "alert": "FRAUD DETECTED" if is_fraud else "OK",
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception:
                    return json.dumps({"error": "parse_failed"})

            @udf(result_type=DataTypes.STRING())
            def recommend(raw_value: str) -> str:
                try:
                    event = json.loads(raw_value)
                    user_id = event.get("user_id", "unknown")
                    item_id = event.get("item_id", "")
                    recommendations = [
                        {"product_id": f"SKU{i:04d}", "score": round(0.95 - (i * 0.15), 2)}
                        for i in range(1, 6)
                    ]
                    return json.dumps({
                        "user_id": user_id,
                        "source_item": item_id,
                        "recommendations": recommendations,
                        "count": len(recommendations),
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception:
                    return json.dumps({"error": "parse_failed"})

            @udf(result_type=DataTypes.STRING())
            def forecast_inventory(raw_value: str) -> str:
                try:
                    event = json.loads(raw_value)
                    product_id = event.get("item_id", event.get("product_id", "UNKNOWN"))
                    quantity = int(event.get("quantity", 1))
                    forecast_qty = max(0, quantity - int(quantity * 0.1))
                    return json.dumps({
                        "product_id": product_id,
                        "current_quantity": quantity,
                        "forecast_7days": forecast_qty,
                        "needs_reorder": forecast_qty < 100,
                        "alert": "REORDER NEEDED" if forecast_qty < 100 else "OK",
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception:
                    return json.dumps({"error": "parse_failed"})

            t_env.create_temporary_function("detect_fraud", detect_fraud)
            t_env.create_temporary_function("recommend", recommend)
            t_env.create_temporary_function("forecast_inventory", forecast_inventory)

            logger.info("3 processing branches registered (fraud, reco, inventory)")

            # Use StatementSet to execute all 3 sinks + print in one job
            stmt_set = t_env.create_statement_set()

            # Fraud detection -> fraud-scores topic
            stmt_set.add_insert_sql("""
                INSERT INTO fraud_sink
                SELECT detect_fraud(raw_value) FROM raw_events
            """)

            # Recommendations -> recommendations topic
            stmt_set.add_insert_sql("""
                INSERT INTO reco_sink
                SELECT recommend(raw_value) FROM raw_events
            """)

            # Inventory forecasting -> inventory-changes topic
            stmt_set.add_insert_sql("""
                INSERT INTO inventory_sink
                SELECT forecast_inventory(raw_value) FROM raw_events
            """)

            # Print for debugging
            stmt_set.add_insert_sql("""
                INSERT INTO print_sink
                SELECT detect_fraud(raw_value) FROM raw_events
            """)

            logger.info("=" * 80)
            logger.info("Executing unified streaming job...")
            logger.info("=" * 80)

            # Execute all sinks together
            result = stmt_set.execute()
            logger.info("Job submitted, waiting for completion...")
            result.wait()

            logger.info("Job completed successfully!")

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
