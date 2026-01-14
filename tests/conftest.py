"""Fixtures pytest globales pour les tests du Sprint 1.

Ce module contient toutes les fixtures partagées entre les tests unitaires
et d'intégration pour le producer et consumer Kafka.
"""
import logging
import sys
from typing import Dict
from unittest.mock import Mock, MagicMock

import pytest

# Ajout du répertoire parent au path
sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')

from ingestion.producer import KafkaEventProducer
from ingestion.basic_consumer import KafkaEventConsumer
from config.constants import KAFKA_BROKERS, KAFKA_TOPICS

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_kafka_producer():
    """Fixture qui retourne un mock du Producer Kafka.

    Returns:
        Mock configuré pour simuler un Producer Kafka
    """
    mock_producer = MagicMock()
    mock_producer.produce = Mock(return_value=None)
    mock_producer.poll = Mock(return_value=0)
    mock_producer.flush = Mock(return_value=None)
    return mock_producer


@pytest.fixture
def mock_kafka_consumer():
    """Fixture qui retourne un mock du Consumer Kafka.

    Returns:
        Mock configuré pour simuler un Consumer Kafka
    """
    mock_consumer = MagicMock()
    mock_consumer.subscribe = Mock(return_value=None)
    mock_consumer.poll = Mock(return_value=None)
    mock_consumer.close = Mock(return_value=None)
    return mock_consumer


@pytest.fixture
def sample_view_event() -> Dict:
    """Fixture qui retourne un événement 'view' valide.

    Returns:
        Événement view complet et valide
    """
    return {
        'event_id': 'test-event-123',
        'event_type': 'view',
        'timestamp': 1704067200000,
        'user_id': '12345',
        'session_id': 'session-abc',
        'item_id': '9876',
        'category': 'Electronics',
        'device_type': 'desktop',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0',
    }


@pytest.fixture
def sample_transaction_event() -> Dict:
    """Fixture qui retourne un événement 'transaction' valide.

    Returns:
        Événement transaction complet et valide
    """
    return {
        'event_id': 'test-event-456',
        'event_type': 'transaction',
        'timestamp': 1704067200000,
        'user_id': '12345',
        'session_id': 'session-abc',
        'item_id': '9876',
        'category': 'Electronics',
        'price': 599.99,
        'quantity': 2,
        'device_type': 'mobile',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0',
    }


@pytest.fixture
def sample_search_event() -> Dict:
    """Fixture qui retourne un événement 'search' valide.

    Returns:
        Événement search complet et valide
    """
    return {
        'event_id': 'test-event-789',
        'event_type': 'search',
        'timestamp': 1704067200000,
        'user_id': '12345',
        'session_id': 'session-abc',
        'search_query': 'laptop',
        'device_type': 'tablet',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0',
    }


@pytest.fixture
def invalid_event() -> Dict:
    """Fixture qui retourne un événement invalide (champs manquants).

    Returns:
        Événement invalide pour tester la validation
    """
    return {
        'event_id': 'test-invalid',
        'timestamp': 1704067200000,
    }


@pytest.fixture
def kafka_config() -> Dict:
    """Fixture qui retourne la configuration Kafka pour tests.

    Returns:
        Configuration Kafka de test
    """
    return {
        'brokers': 'localhost:9092',
        'topics': KAFKA_TOPICS,
        'group_id': 'test-consumer-group',
    }


@pytest.fixture
def event_producer_instance(monkeypatch, mock_kafka_producer):
    """Fixture qui retourne une instance de KafkaEventProducer avec mock.

    Args:
        monkeypatch: Fixture pytest pour monkey patching
        mock_kafka_producer: Mock du producer Kafka

    Returns:
        Instance de KafkaEventProducer avec Producer mocké
    """
    def mock_producer_init(*args, **kwargs):
        return mock_kafka_producer

    monkeypatch.setattr(
        'confluent_kafka.Producer',
        mock_producer_init
    )

    producer = KafkaEventProducer(brokers='localhost:9092')
    return producer


@pytest.fixture
def event_consumer_instance(monkeypatch, mock_kafka_consumer):
    """Fixture qui retourne une instance de KafkaEventConsumer avec mock.

    Args:
        monkeypatch: Fixture pytest pour monkey patching
        mock_kafka_consumer: Mock du consumer Kafka

    Returns:
        Instance de KafkaEventConsumer avec Consumer mocké
    """
    def mock_consumer_init(*args, **kwargs):
        return mock_kafka_consumer

    monkeypatch.setattr(
        'confluent_kafka.Consumer',
        mock_consumer_init
    )

    consumer = KafkaEventConsumer(brokers='localhost:9092')
    return consumer


@pytest.fixture(scope='session')
def kafka_broker_url() -> str:
    """Fixture qui retourne l'URL du broker Kafka pour tests d'intégration.

    Returns:
        URL du broker Kafka de test
    """
    return KAFKA_BROKERS


@pytest.fixture(autouse=True)
def reset_logging():
    """Fixture auto-utilisée pour réinitialiser le logging entre les tests.

    Yields:
        None (cleanup après chaque test)
    """
    yield
    logging.getLogger().handlers = []


@pytest.fixture
def caplog_debug(caplog):
    """Fixture pour capturer les logs DEBUG.

    Args:
        caplog: Fixture pytest pour capturer les logs

    Returns:
        caplog configuré pour DEBUG
    """
    caplog.set_level(logging.DEBUG)
    return caplog
