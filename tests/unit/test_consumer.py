"""Tests unitaires pour le Consumer Kafka.

Tests couvrant la consommation et validation d'événements e-commerce.
"""
import json
import logging
import sys
from unittest.mock import Mock, MagicMock

import pytest

sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')
from ingestion.basic_consumer import KafkaEventConsumer

logger = logging.getLogger(__name__)


class TestKafkaEventConsumer:
    """Tests pour la classe KafkaEventConsumer."""

    def test_should_initialize_consumer_successfully(self, event_consumer_instance):
        """Test l'initialisation du consumer."""
        assert event_consumer_instance is not None
        assert event_consumer_instance.brokers == 'localhost:9092'
        assert event_consumer_instance.messages_consumed == 0
        assert event_consumer_instance.messages_invalid == 0

    def test_should_subscribe_to_topics(self, event_consumer_instance):
        """Test l'abonnement aux topics."""
        event_consumer_instance.subscribe()
        event_consumer_instance.consumer.subscribe.assert_called_once()

    def test_should_validate_view_event_successfully(self, event_consumer_instance, sample_view_event):
        """Test la validation d'un événement 'view' valide."""
        result = event_consumer_instance._validate_event(sample_view_event)
        assert result is True

    def test_should_validate_transaction_event_successfully(self, event_consumer_instance, sample_transaction_event):
        """Test la validation d'un événement 'transaction' valide."""
        result = event_consumer_instance._validate_event(sample_transaction_event)
        assert result is True

    def test_should_reject_event_without_event_type(self, event_consumer_instance):
        """Test le rejet d'un événement sans event_type."""
        invalid = {'user_id': '123', 'timestamp': 1704067200000}
        result = event_consumer_instance._validate_event(invalid)
        assert result is False

    def test_should_reject_event_with_missing_required_fields(self, event_consumer_instance):
        """Test le rejet d'un événement avec champs manquants."""
        invalid = {'event_type': 'view', 'user_id': '123'}  # Manque timestamp, item_id
        result = event_consumer_instance._validate_event(invalid)
        assert result is False

    def test_should_reject_unknown_event_type(self, event_consumer_instance):
        """Test le rejet d'un type d'événement inconnu."""
        invalid = {'event_type': 'unknown', 'user_id': '123'}
        result = event_consumer_instance._validate_event(invalid)
        assert result is False

    def test_should_close_consumer_properly(self, event_consumer_instance):
        """Test la fermeture propre du consumer."""
        event_consumer_instance.close()
        event_consumer_instance.consumer.close.assert_called_once()

    def test_should_handle_multiple_topics(self, monkeypatch, mock_kafka_consumer):
        """Test la gestion de plusieurs topics."""
        def mock_consumer_init(*args, **kwargs):
            return mock_kafka_consumer

        monkeypatch.setattr('confluent_kafka.Consumer', mock_consumer_init)
        consumer = KafkaEventConsumer(
            brokers='localhost:9092',
            topics=['events', 'inventory']
        )
        assert len(consumer.topic_names) == 2
