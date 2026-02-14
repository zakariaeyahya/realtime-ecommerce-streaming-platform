"""Unit tests for Kafka consumers that feed the API cache.

Tests consumer message processing and Redis storage with mocked
Kafka and Redis dependencies.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.constants import (
    REDIS_CACHE_TTL_FRAUD,
    REDIS_CACHE_TTL_RECO,
    REDIS_INVENTORY_TTL_SECONDS,
    REDIS_KEY_FRAUD,
    REDIS_KEY_INVENTORY,
    REDIS_KEY_RECO,
)


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.setex.return_value = True
    return mock


def _make_kafka_message(value_dict: dict) -> MagicMock:
    """Create a mock Kafka message with the given value."""
    msg = MagicMock()
    msg.value.return_value = json.dumps(value_dict).encode("utf-8")
    msg.error.return_value = None
    return msg


class TestFraudConsumer:
    """Tests for FraudConsumer message processing."""

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_process_fraud_message(self, mock_consumer_cls, mock_redis_client):
        """FraudConsumer stores fraud score in Redis."""
        from serving.consumers.kafka_consumers import FraudConsumer

        consumer = FraudConsumer(redis_client=mock_redis_client)

        fraud_data = {
            "user_id": "user_1002",
            "fraud_score": 0.92,
            "amount": 1500.0,
            "timestamp": "2024-01-15T10:30:00",
        }
        msg = _make_kafka_message(fraud_data)

        consumer._process_message(msg)

        expected_key = f"{REDIS_KEY_FRAUD}:user_1002"
        mock_redis_client.setex.assert_called_once_with(
            expected_key, REDIS_CACHE_TTL_FRAUD, json.dumps(fraud_data)
        )

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_fraud_message_missing_user_id(self, mock_consumer_cls, mock_redis_client):
        """FraudConsumer skips messages without user_id."""
        from serving.consumers.kafka_consumers import FraudConsumer

        consumer = FraudConsumer(redis_client=mock_redis_client)

        msg = _make_kafka_message({"fraud_score": 0.5})
        consumer._process_message(msg)

        mock_redis_client.setex.assert_not_called()

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_fraud_invalid_json(self, mock_consumer_cls, mock_redis_client):
        """FraudConsumer handles invalid JSON gracefully."""
        from serving.consumers.kafka_consumers import FraudConsumer

        consumer = FraudConsumer(redis_client=mock_redis_client)

        msg = MagicMock()
        msg.value.return_value = b"not json"
        msg.error.return_value = None

        consumer._process_message(msg)

        mock_redis_client.setex.assert_not_called()


class TestRecoConsumer:
    """Tests for RecoConsumer message processing."""

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_process_reco_message(self, mock_consumer_cls, mock_redis_client):
        """RecoConsumer stores recommendations in Redis."""
        from serving.consumers.kafka_consumers import RecoConsumer

        consumer = RecoConsumer(redis_client=mock_redis_client)

        reco_data = {
            "user_id": "user_1001",
            "recommendations": [
                {"item_id": "item_100", "score": 0.95},
                {"item_id": "item_200", "score": 0.87},
            ],
            "timestamp": "2024-01-15T10:30:00",
        }
        msg = _make_kafka_message(reco_data)

        consumer._process_message(msg)

        expected_key = f"{REDIS_KEY_RECO}:user_1001"
        mock_redis_client.setex.assert_called_once_with(
            expected_key, REDIS_CACHE_TTL_RECO, json.dumps(reco_data)
        )

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_reco_message_missing_user_id(self, mock_consumer_cls, mock_redis_client):
        """RecoConsumer skips messages without user_id."""
        from serving.consumers.kafka_consumers import RecoConsumer

        consumer = RecoConsumer(redis_client=mock_redis_client)

        msg = _make_kafka_message({"recommendations": []})
        consumer._process_message(msg)

        mock_redis_client.setex.assert_not_called()


class TestInventoryConsumer:
    """Tests for InventoryConsumer message processing."""

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_process_inventory_message(self, mock_consumer_cls, mock_redis_client):
        """InventoryConsumer stores inventory data in Redis."""
        from serving.consumers.kafka_consumers import InventoryConsumer

        consumer = InventoryConsumer(redis_client=mock_redis_client)

        inv_data = {
            "product_id": "SKU0001",
            "current_quantity": 250,
            "forecast_7days": [240, 230, 220, 210, 200, 190, 180],
            "timestamp": "2024-01-15T10:30:00",
        }
        msg = _make_kafka_message(inv_data)

        consumer._process_message(msg)

        expected_key = f"{REDIS_KEY_INVENTORY}:SKU0001"
        mock_redis_client.setex.assert_called_once_with(
            expected_key, REDIS_INVENTORY_TTL_SECONDS, json.dumps(inv_data)
        )

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_inventory_fallback_item_id(self, mock_consumer_cls, mock_redis_client):
        """InventoryConsumer uses item_id when product_id is missing."""
        from serving.consumers.kafka_consumers import InventoryConsumer

        consumer = InventoryConsumer(redis_client=mock_redis_client)

        inv_data = {
            "item_id": "ITEM_42",
            "current_quantity": 100,
            "timestamp": "2024-01-15T10:30:00",
        }
        msg = _make_kafka_message(inv_data)

        consumer._process_message(msg)

        expected_key = f"{REDIS_KEY_INVENTORY}:ITEM_42"
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == expected_key

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_inventory_missing_product_id(self, mock_consumer_cls, mock_redis_client):
        """InventoryConsumer skips messages without any ID."""
        from serving.consumers.kafka_consumers import InventoryConsumer

        consumer = InventoryConsumer(redis_client=mock_redis_client)

        msg = _make_kafka_message({"current_quantity": 100})
        consumer._process_message(msg)

        mock_redis_client.setex.assert_not_called()


class TestConsumerStartStop:
    """Tests for consumer lifecycle management."""

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_start_and_stop(self, mock_consumer_cls, mock_redis_client):
        """Consumer can be started and stopped."""
        from serving.consumers.kafka_consumers import FraudConsumer

        consumer = FraudConsumer(redis_client=mock_redis_client)

        consumer.start()
        assert consumer._running is True
        assert consumer._thread is not None
        assert consumer._thread.is_alive()

        consumer.stop()
        assert consumer._running is False

    @patch("serving.consumers.kafka_consumers.Consumer")
    def test_double_start_ignored(self, mock_consumer_cls, mock_redis_client):
        """Starting an already running consumer is a no-op."""
        from serving.consumers.kafka_consumers import FraudConsumer

        consumer = FraudConsumer(redis_client=mock_redis_client)

        consumer.start()
        first_thread = consumer._thread
        consumer.start()
        assert consumer._thread is first_thread

        consumer.stop()
