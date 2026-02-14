"""Tests unitaires avances pour le Consumer Kafka.

Couvre: _process_message, run, close, gestion d'erreurs.
"""
import json
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from ingestion.basic_consumer import KafkaEventConsumer

logger = logging.getLogger(__name__)


@pytest.fixture
def consumer(monkeypatch):
    """Consumer avec mock Kafka."""
    mock_kafka = MagicMock()
    monkeypatch.setattr(
        'ingestion.basic_consumer.Consumer',
        lambda *args, **kwargs: mock_kafka
    )
    c = KafkaEventConsumer(brokers='localhost:9092')
    c.consumer = mock_kafka
    return c


class TestProcessMessage:
    """Tests pour _process_message."""

    def test_process_valid_message(self, consumer, sample_view_event):
        """Test traitement d'un message valide."""
        msg = MagicMock()
        msg.error.return_value = None
        msg.value.return_value = json.dumps(sample_view_event).encode('utf-8')
        msg.topic.return_value = 'raw-events'
        msg.partition.return_value = 0
        msg.offset.return_value = 42

        consumer._process_message(msg)
        assert consumer.messages_consumed == 1
        assert consumer.messages_invalid == 0

    def test_process_invalid_json(self, consumer):
        """Test traitement d'un message JSON invalide."""
        msg = MagicMock()
        msg.error.return_value = None
        msg.value.return_value = b'not-valid-json'

        consumer._process_message(msg)
        assert consumer.messages_invalid == 1

    def test_process_invalid_event(self, consumer):
        """Test traitement d'un evenement invalide (champs manquants)."""
        msg = MagicMock()
        msg.error.return_value = None
        msg.value.return_value = json.dumps({'foo': 'bar'}).encode('utf-8')

        consumer._process_message(msg)
        assert consumer.messages_invalid == 1

    def test_process_message_with_partition_eof(self, consumer):
        """Test message avec erreur PARTITION_EOF."""
        from confluent_kafka import KafkaError
        mock_error = MagicMock()
        mock_error.code.return_value = KafkaError._PARTITION_EOF

        msg = MagicMock()
        msg.error.return_value = mock_error
        msg.topic.return_value = 'raw-events'
        msg.partition.return_value = 0
        msg.offset.return_value = 100

        consumer._process_message(msg)
        assert consumer.messages_consumed == 0

    def test_process_message_with_kafka_error(self, consumer):
        """Test message avec erreur Kafka generique."""
        mock_error = MagicMock()
        mock_error.code.return_value = -1

        msg = MagicMock()
        msg.error.return_value = mock_error

        consumer._process_message(msg)
        assert consumer.messages_consumed == 0

    def test_stats_logging_every_100(self, consumer, sample_view_event):
        """Test logging des statistiques tous les 100 messages."""
        consumer.messages_consumed = 99

        msg = MagicMock()
        msg.error.return_value = None
        msg.value.return_value = json.dumps(sample_view_event).encode('utf-8')
        msg.topic.return_value = 'raw-events'
        msg.partition.return_value = 0
        msg.offset.return_value = 1

        consumer._process_message(msg)
        assert consumer.messages_consumed == 100


class TestConsumerRun:
    """Tests pour run et close."""

    def test_run_keyboard_interrupt(self, consumer):
        """Test arret par KeyboardInterrupt."""
        consumer.consumer.poll.side_effect = KeyboardInterrupt()
        consumer.run()
        consumer.consumer.close.assert_called_once()

    def test_run_processes_messages(self, consumer, sample_view_event):
        """Test run traite des messages puis s'arrete."""
        msg = MagicMock()
        msg.error.return_value = None
        msg.value.return_value = json.dumps(sample_view_event).encode('utf-8')
        msg.topic.return_value = 'raw-events'
        msg.partition.return_value = 0
        msg.offset.return_value = 0

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count > 2:
                raise KeyboardInterrupt()
            return msg

        consumer.consumer.poll.side_effect = poll_side_effect
        consumer.run()
        assert consumer.messages_consumed == 2

    def test_run_skips_none_messages(self, consumer):
        """Test run ignore les messages None."""
        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count > 3:
                raise KeyboardInterrupt()
            return None

        consumer.consumer.poll.side_effect = poll_side_effect
        consumer.run()
        assert consumer.messages_consumed == 0

    def test_close_handles_exception(self, consumer):
        """Test fermeture gere les exceptions."""
        consumer.consumer.close.side_effect = Exception("Close failed")
        consumer.close()

    def test_invalid_topics_raises(self, monkeypatch):
        """Test erreur si aucun topic valide."""
        mock_kafka = MagicMock()
        monkeypatch.setattr(
            'ingestion.basic_consumer.Consumer',
            lambda *args, **kwargs: mock_kafka
        )
        with pytest.raises(ValueError, match="Au moins un topic valide"):
            KafkaEventConsumer(
                brokers='localhost:9092',
                topics=['nonexistent_topic']
            )
