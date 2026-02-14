"""Kafka consumers for reading processed results and caching in Redis.

Background thread consumers that read from fraud-scores, recommendations,
and inventory-changes topics, then store results in Redis for fast API access.
"""

import json
import logging
import os
import sys
import threading
import time
from typing import Optional

import redis
from confluent_kafka import Consumer, KafkaError

# Ajout du repertoire racine au path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))

from config.constants import (
    KAFKA_BROKERS,
    KAFKA_TOPICS,
    REDIS_CACHE_TTL_FRAUD,
    REDIS_CACHE_TTL_RECO,
    REDIS_DB,
    REDIS_HOST,
    REDIS_INVENTORY_TTL_SECONDS,
    REDIS_KEY_FRAUD,
    REDIS_KEY_INVENTORY,
    REDIS_KEY_RECO,
    REDIS_PORT,
)

logger = logging.getLogger(__name__)


class BaseKafkaConsumer:
    """Base class for Kafka consumers with Redis storage."""

    def __init__(
        self,
        topic: str,
        group_id: str,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        self.topic = topic
        self.group_id = group_id
        self._running = False
        self._thread: Optional[threading.Thread] = None

        brokers = os.getenv("KAFKA_BROKERS", KAFKA_BROKERS)
        self.consumer = Consumer({
            "bootstrap.servers": brokers,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        })

        if redis_client is not None:
            self.redis = redis_client
        else:
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", REDIS_HOST),
                port=int(os.getenv("REDIS_PORT", str(REDIS_PORT))),
                db=int(os.getenv("REDIS_DB", str(REDIS_DB))),
                decode_responses=True,
            )

    def start(self) -> None:
        """Start consuming in a background thread."""
        if self._running:
            logger.warning("Consumer %s already running", self.group_id)
            return
        self._running = True
        self.consumer.subscribe([self.topic])
        self._thread = threading.Thread(
            target=self._consume_loop, daemon=True, name=self.group_id
        )
        self._thread.start()
        logger.info("Started consumer %s on topic %s", self.group_id, self.topic)

    def stop(self) -> None:
        """Stop the consumer."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        try:
            self.consumer.close()
        except Exception:
            logger.debug("Consumer already closed")
        logger.info("Stopped consumer %s", self.group_id)

    def _consume_loop(self) -> None:
        """Main consume loop running in background thread."""
        while self._running:
            try:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("Consumer error: %s", msg.error())
                    continue
                self._process_message(msg)
            except Exception:
                logger.exception("Error in consumer %s", self.group_id)
                time.sleep(1.0)

    def _process_message(self, msg) -> None:
        """Process a single message. Override in subclasses."""
        raise NotImplementedError


class FraudConsumer(BaseKafkaConsumer):
    """Consumes fraud scores and stores in Redis."""

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        topic = os.getenv("KAFKA_TOPIC_FRAUD", KAFKA_TOPICS["fraud_scores"])
        super().__init__(
            topic=topic,
            group_id="api-fraud-consumer",
            redis_client=redis_client,
        )

    def _process_message(self, msg) -> None:
        """Store fraud score in Redis keyed by user_id."""
        try:
            data = json.loads(msg.value().decode("utf-8"))
            user_id = data.get("user_id")
            if not user_id:
                logger.warning("Fraud message missing user_id: %s", data)
                return
            key = f"{REDIS_KEY_FRAUD}:{user_id}"
            self.redis.setex(key, REDIS_CACHE_TTL_FRAUD, json.dumps(data))
            logger.debug("Stored fraud score for %s", user_id)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Invalid fraud message format")


class RecoConsumer(BaseKafkaConsumer):
    """Consumes recommendations and stores in Redis."""

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        topic = os.getenv(
            "KAFKA_TOPIC_RECO", KAFKA_TOPICS["recommendations"]
        )
        super().__init__(
            topic=topic,
            group_id="api-reco-consumer",
            redis_client=redis_client,
        )

    def _process_message(self, msg) -> None:
        """Store recommendations in Redis keyed by user_id."""
        try:
            data = json.loads(msg.value().decode("utf-8"))
            user_id = data.get("user_id")
            if not user_id:
                logger.warning("Reco message missing user_id: %s", data)
                return
            key = f"{REDIS_KEY_RECO}:{user_id}"
            self.redis.setex(key, REDIS_CACHE_TTL_RECO, json.dumps(data))
            logger.debug("Stored recommendations for %s", user_id)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Invalid reco message format")


class InventoryConsumer(BaseKafkaConsumer):
    """Consumes inventory changes and stores in Redis."""

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        topic = os.getenv(
            "KAFKA_TOPIC_INVENTORY", KAFKA_TOPICS["inventory"]
        )
        super().__init__(
            topic=topic,
            group_id="api-inventory-consumer",
            redis_client=redis_client,
        )

    def _process_message(self, msg) -> None:
        """Store inventory data in Redis keyed by product_id."""
        try:
            data = json.loads(msg.value().decode("utf-8"))
            product_id = data.get("product_id") or data.get("item_id")
            if not product_id:
                logger.warning("Inventory message missing product_id: %s", data)
                return
            key = f"{REDIS_KEY_INVENTORY}:{product_id}"
            self.redis.setex(
                key, REDIS_INVENTORY_TTL_SECONDS, json.dumps(data)
            )
            logger.debug("Stored inventory for %s", product_id)
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Invalid inventory message format")
