"""Tests unitaires pour le Producer Kafka.

Tests couvrant la génération et l'envoi d'événements e-commerce.
"""
import json
import logging
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')
from ingestion.producer import KafkaEventProducer

logger = logging.getLogger(__name__)


class TestKafkaEventProducer:
    """Tests pour la classe KafkaEventProducer."""

    def test_should_initialize_producer_successfully(self, event_producer_instance):
        """Test l'initialisation du producer."""
        assert event_producer_instance is not None
        assert event_producer_instance.brokers == 'localhost:9092'
        assert event_producer_instance.events_sent == 0
        assert event_producer_instance.events_failed == 0

    def test_should_generate_event_id_as_uuid(self, event_producer_instance):
        """Test la génération d'un event_id UUID valide."""
        event_id = event_producer_instance._generate_event_id()

        assert event_id is not None
        assert isinstance(event_id, str)
        assert len(event_id) == 36  # UUID v4 format

    def test_should_generate_view_event_with_required_fields(self, event_producer_instance):
        """Test la génération d'un événement 'view'."""
        event = event_producer_instance._generate_view_event()

        assert event['event_type'] == 'view'
        assert 'event_id' in event
        assert 'timestamp' in event
        assert 'user_id' in event
        assert 'item_id' in event
        assert 'category' in event

    def test_should_generate_transaction_event_with_price(self, event_producer_instance):
        """Test la génération d'un événement 'transaction'."""
        event = event_producer_instance._generate_transaction_event()

        assert event['event_type'] == 'transaction'
        assert 'price' in event
        assert 'quantity' in event
        assert isinstance(event['price'], float)
        assert isinstance(event['quantity'], int)
        assert event['quantity'] >= 1

    def test_should_generate_search_event_with_query(self, event_producer_instance):
        """Test la génération d'un événement 'search'."""
        event = event_producer_instance._generate_search_event()

        assert event['event_type'] == 'search'
        assert 'search_query' in event
        assert isinstance(event['search_query'], str)

    def test_should_reject_event_without_user_id(self, event_producer_instance):
        """Test le rejet d'un événement sans user_id."""
        invalid_event = {'event_type': 'view', 'item_id': '123'}

        result = event_producer_instance.send_event(invalid_event)

        assert result is False

    def test_should_reject_event_without_event_type(self, event_producer_instance):
        """Test le rejet d'un événement sans event_type."""
        invalid_event = {'user_id': '12345', 'item_id': '123'}

        result = event_producer_instance.send_event(invalid_event)

        assert result is False

    def test_should_send_event_successfully(self, event_producer_instance, sample_view_event):
        """Test l'envoi réussi d'un événement."""
        result = event_producer_instance.send_event(sample_view_event)

        assert result is True
        event_producer_instance.producer.produce.assert_called_once()

    def test_should_use_user_id_as_message_key(self, event_producer_instance, sample_view_event):
        """Test que le user_id est utilisé comme clé du message."""
        event_producer_instance.send_event(sample_view_event)

        call_args = event_producer_instance.producer.produce.call_args
        assert call_args is not None

        key = call_args.kwargs.get('key')
        assert key == b'12345'

    def test_should_generate_events_with_different_types(self, event_producer_instance):
        """Test la génération d'événements de types variés."""
        events = [event_producer_instance.generate_event() for _ in range(100)]
        event_types = {e['event_type'] for e in events}

        assert len(event_types) > 1  # Au moins 2 types différents

    def test_should_handle_buffer_error_gracefully(self, event_producer_instance, sample_view_event):
        """Test la gestion d'une BufferError."""
        event_producer_instance.producer.produce.side_effect = BufferError("Buffer full")

        result = event_producer_instance.send_event(sample_view_event)

        assert result is False
        event_producer_instance.producer.flush.assert_called_once()

    def test_should_log_warning_for_unknown_topic(self, event_producer_instance, sample_view_event):
        """Test le logging d'un avertissement pour topic inconnu."""
        result = event_producer_instance.send_event(sample_view_event, topic='unknown')

        assert result is False

    def test_should_close_producer_properly(self, event_producer_instance):
        """Test la fermeture propre du producer."""
        event_producer_instance.close()

        event_producer_instance.producer.flush.assert_called()
