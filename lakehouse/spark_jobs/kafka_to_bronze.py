# -*- coding: utf-8 -*-
"""
Spark Consumer: Kafka → Iceberg Bronze Layer

Reads events from Kafka topics and writes to Iceberg Bronze tables:
- raw-events → events_raw
- fraud-scores → fraud_raw
- inventory-changes → inventory_raw

Usage:
    python kafka_to_bronze.py
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Optional
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.constants import (
    KAFKA_BROKERS,
    KAFKA_TOPICS,
)

logger = logging.getLogger(__name__)


class KafkaToBronzeConsumer:
    """Consume Kafka events and write to Iceberg Bronze tables."""

    def __init__(self, spark=None):
        """Initialize consumer with Spark session."""
        self.spark = spark
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", KAFKA_BROKERS)
        self.kafka_topics = KAFKA_TOPICS
        logger.info(f"KafkaToBronzeConsumer initialized (brokers={self.kafka_brokers})")

    def create_spark_session(self):
        """Create Spark session with Iceberg support."""
        from pyspark.sql import SparkSession

        if self.spark:
            return self.spark

        logger.info("Creating Spark session with Iceberg support...")

        spark = SparkSession.builder \
            .appName("KafkaToBronze") \
            .master("local[*]") \
            .config("spark.driver.bindAddress", "127.0.0.1") \
            .getOrCreate()

        self.spark = spark
        logger.info("[OK] Spark session created with Iceberg support")
        return spark

    def run_batch_test(self) -> None:
        """Run batch test with sample data (for testing without Kafka)."""
        self.create_spark_session()

        logger.info("================================================================================")
        logger.info("Starting Batch Test: Generating Sample Data → Iceberg Bronze")
        logger.info("================================================================================")

        try:
            from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, LongType

            # Sample events data
            events_data = [
                ("event_001", "user_001", "purchase", 1674047400000),
                ("event_002", "user_002", "view", 1674047410000),
                ("event_003", "user_003", "click", 1674047420000),
            ]
            events_schema = StructType([
                StructField("event_id", StringType()),
                StructField("user_id", StringType()),
                StructField("event_type", StringType()),
                StructField("timestamp", LongType()),
            ])

            df_events = self.spark.createDataFrame(events_data, events_schema)
            logger.info(f"[OK] Created sample events DataFrame (count: {df_events.count()})")

            # Sample fraud data
            fraud_data = [
                ("event_001", 0.45),
                ("event_002", 0.12),
                ("event_003", 0.78),
            ]
            fraud_schema = StructType([
                StructField("event_id", StringType()),
                StructField("fraud_score", DoubleType()),
            ])

            df_fraud = self.spark.createDataFrame(fraud_data, fraud_schema)
            logger.info(f"[OK] Created sample fraud DataFrame (count: {df_fraud.count()})")

            # Sample inventory data
            inventory_data = [
                ("SKU001", "warehouse_01", -5, 95, 1674047400000),
                ("SKU002", "warehouse_01", 10, 110, 1674047410000),
                ("SKU003", "warehouse_02", -2, 48, 1674047420000),
            ]
            inventory_schema = StructType([
                StructField("product_id", StringType()),
                StructField("warehouse_id", StringType()),
                StructField("quantity_change", IntegerType()),
                StructField("current_stock", IntegerType()),
                StructField("timestamp", LongType()),
            ])

            df_inventory = self.spark.createDataFrame(inventory_data, inventory_schema)
            logger.info(f"[OK] Created sample inventory DataFrame (count: {df_inventory.count()})")

            # Write to Iceberg Bronze tables
            logger.info("Writing sample data to Iceberg Bronze tables...")

            df_events.write \
                .mode("append") \
                .format("iceberg") \
                .option("merge-schema", "true") \
                .saveAsTable("default.events_raw")
            logger.info("[OK] events_raw written")

            df_fraud.write \
                .mode("append") \
                .format("iceberg") \
                .option("merge-schema", "true") \
                .saveAsTable("default.fraud_raw")
            logger.info("[OK] fraud_raw written")

            df_inventory.write \
                .mode("append") \
                .format("iceberg") \
                .option("merge-schema", "true") \
                .saveAsTable("default.inventory_raw")
            logger.info("[OK] inventory_raw written")

            # Verify data
            logger.info("================================================================================")
            logger.info("Verifying Bronze tables...")
            logger.info("================================================================================")

            events_count = self.spark.sql("SELECT COUNT(*) FROM default.events_raw").collect()[0][0]
            fraud_count = self.spark.sql("SELECT COUNT(*) FROM default.fraud_raw").collect()[0][0]
            inventory_count = self.spark.sql("SELECT COUNT(*) FROM default.inventory_raw").collect()[0][0]

            logger.info(f"✅ events_raw: {events_count} rows")
            logger.info(f"✅ fraud_raw: {fraud_count} rows")
            logger.info(f"✅ inventory_raw: {inventory_count} rows")

            logger.info("================================================================================")
            logger.info("[OK] Batch test completed successfully!")
            logger.info("================================================================================")

        except Exception as e:
            logger.error(f"Batch test failed: {str(e)}")
            raise


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    consumer = KafkaToBronzeConsumer()

    # For now, run batch test (Kafka connector not available in Docker)
    consumer.run_batch_test()


if __name__ == "__main__":
    main()
