"""Tests d'intégration pour Producer/Consumer Kafka.

Tests end-to-end nécessitant une instance Kafka réelle.
"""
import json
import logging
import sys
import time

import pytest

sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')
from ingestion.producer import KafkaEventProducer
from ingestion.basic_consumer import KafkaEventConsumer

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestKafkaIntegration:
    """Tests d'intégration Producer/Consumer."""

    @pytest.mark.skip(reason="Nécessite Kafka en cours d'exécution")
    def test_should_send_and_receive_event_end_to_end(self, kafka_broker_url):
        """Test complet: génération -> envoi -> réception."""
        producer = KafkaEventProducer(brokers=kafka_broker_url)
        consumer = KafkaEventConsumer(brokers=kafka_broker_url, group_id='test-e2e-group')

        # Générer et envoyer un événement
        event = producer.generate_event()
        success = producer.send_event(event)
        assert success is True

        producer.producer.flush()

        # Consommer l'événement
        consumer.subscribe()
        message = consumer.consumer.poll(timeout=5.0)

        assert message is not None
        assert message.error() is None

        received_event = json.loads(message.value().decode('utf-8'))
        assert received_event['event_type'] in ['view', 'addtocart', 'transaction', 'search', 'filter', 'review']

        consumer.close()
        producer.close()

    @pytest.mark.skip(reason="Nécessite Kafka en cours d'exécution")
    def test_should_handle_high_throughput(self, kafka_broker_url):
        """Test de performance: envoi de 1000 événements."""
        producer = KafkaEventProducer(brokers=kafka_broker_url, speed_multiplier=100.0)

        start_time = time.time()
        for _ in range(1000):
            event = producer.generate_event()
            producer.send_event(event)

        producer.producer.flush()
        elapsed = time.time() - start_time

        logger.info(f"1000 événements envoyés en {elapsed:.2f}s")
        assert elapsed < 10.0  # Devrait prendre moins de 10 secondes

        producer.close()
