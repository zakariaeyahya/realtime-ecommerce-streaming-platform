"""Tests d'integration pour Producer/Consumer Kafka.

Tests end-to-end necessitant une instance Kafka reelle.
"""
import json
import logging
import sys
import time
from pathlib import Path

import pytest

# Ajout du repertoire parent au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from ingestion.producer import KafkaEventProducer
from ingestion.basic_consumer import KafkaEventConsumer
from config.constants import KAFKA_TOPICS

# Configuration logging visible avec pytest -v -s
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestKafkaIntegration:
    """Tests d'integration Producer/Consumer."""

    def test_should_send_and_receive_event_end_to_end(self, kafka_broker_url):
        """Test complet: generation -> envoi -> reception."""
        logger.info("=" * 60)
        logger.info("TEST E2E: Debut du test end-to-end")
        logger.info("Broker Kafka: %s", kafka_broker_url)
        logger.info("Topics configures: %s", KAFKA_TOPICS)

        # --- Phase 1: Creation du Producer ---
        logger.info("-" * 40)
        logger.info("PHASE 1: Creation du Producer...")
        try:
            producer = KafkaEventProducer(brokers=kafka_broker_url)
            logger.info("Producer cree avec succes (broker=%s)", kafka_broker_url)
        except Exception as e:
            logger.error("ECHEC creation Producer: %s", e)
            raise

        # --- Phase 2: Creation du Consumer ---
        logger.info("-" * 40)
        logger.info("PHASE 2: Creation du Consumer...")
        try:
            consumer = KafkaEventConsumer(
                brokers=kafka_broker_url, group_id='test-e2e-group'
            )
            logger.info(
                "Consumer cree avec succes (broker=%s, group=test-e2e-group)",
                kafka_broker_url,
            )
        except Exception as e:
            logger.error("ECHEC creation Consumer: %s", e)
            raise

        # --- Phase 3: Generation d'un evenement ---
        logger.info("-" * 40)
        logger.info("PHASE 3: Generation d'un evenement...")
        event = producer.generate_event()
        logger.info("Evenement genere: type=%s, user_id=%s, event_id=%s",
                     event.get('event_type'), event.get('user_id'), event.get('event_id'))
        logger.debug("Contenu complet de l'evenement: %s", json.dumps(event, indent=2))

        # --- Phase 4: Envoi vers Kafka ---
        logger.info("-" * 40)
        logger.info("PHASE 4: Envoi de l'evenement vers Kafka...")
        success = producer.send_event(event)
        logger.info("Resultat send_event: %s", success)
        assert success is True, "L'envoi de l'evenement a echoue"

        logger.info("Flush du producer (attente confirmation broker)...")
        remaining = producer.producer.flush(timeout=10)
        logger.info("Flush termine. Messages restants dans le buffer: %s", remaining)

        # --- Phase 5: Consommation depuis Kafka ---
        logger.info("-" * 40)
        logger.info("PHASE 5: Consommation de l'evenement depuis Kafka...")
        consumer.subscribe()
        logger.info("Consumer abonne aux topics. Poll en cours (timeout=10s)...")

        message = consumer.consumer.poll(timeout=10.0)

        if message is None:
            logger.error("AUCUN message recu apres 10s de poll!")
            logger.error("Verifier: Kafka est-il accessible? Le topic existe-t-il?")
        elif message.error():
            logger.error("Erreur dans le message recu: %s", message.error())
        else:
            logger.info("Message recu! topic=%s, partition=%s, offset=%s",
                         message.topic(), message.partition(), message.offset())
            received_event = json.loads(message.value().decode('utf-8'))
            logger.info("Evenement recu: type=%s, user_id=%s",
                         received_event.get('event_type'), received_event.get('user_id'))
            logger.debug("Contenu recu complet: %s", json.dumps(received_event, indent=2))

        assert message is not None, "Aucun message recu depuis Kafka (timeout)"
        assert message.error() is None, f"Erreur Kafka: {message.error()}"

        received_event = json.loads(message.value().decode('utf-8'))
        valid_types = ['view', 'addtocart', 'transaction', 'search', 'filter', 'review']
        assert received_event['event_type'] in valid_types, (
            f"Type invalide: {received_event['event_type']}"
        )

        # --- Cleanup ---
        logger.info("-" * 40)
        logger.info("CLEANUP: Fermeture producer et consumer...")
        consumer.close()
        producer.close()
        logger.info("TEST E2E: SUCCES")
        logger.info("=" * 60)

    def test_should_handle_high_throughput(self, kafka_broker_url):
        """Test de performance: envoi de 1000 evenements."""
        logger.info("=" * 60)
        logger.info("TEST THROUGHPUT: Debut du test de debit")
        logger.info("Broker Kafka: %s", kafka_broker_url)

        # --- Creation Producer ---
        logger.info("Creation du Producer (speed_multiplier=100x)...")
        try:
            producer = KafkaEventProducer(
                brokers=kafka_broker_url, speed_multiplier=100.0
            )
            logger.info("Producer cree avec succes")
        except Exception as e:
            logger.error("ECHEC creation Producer: %s", e)
            raise

        # --- Envoi de 1000 evenements ---
        num_events = 1000
        logger.info("Envoi de %d evenements...", num_events)
        start_time = time.time()
        errors = 0

        for i in range(num_events):
            event = producer.generate_event()
            success = producer.send_event(event)
            if not success:
                errors += 1

            if (i + 1) % 200 == 0:
                elapsed_so_far = time.time() - start_time
                rate = (i + 1) / elapsed_so_far if elapsed_so_far > 0 else 0
                logger.info(
                    "Progression: %d/%d envoyes (%.0f evt/s, %d erreurs)",
                    i + 1, num_events, rate, errors,
                )

        # --- Flush ---
        logger.info("Flush du producer...")
        remaining = producer.producer.flush(timeout=30)
        elapsed = time.time() - start_time

        # --- Resultats ---
        rate = num_events / elapsed if elapsed > 0 else 0
        logger.info("-" * 40)
        logger.info("RESULTATS THROUGHPUT:")
        logger.info("  Evenements envoyes: %d", num_events)
        logger.info("  Erreurs d'envoi:    %d", errors)
        logger.info("  Messages restants:  %d", remaining)
        logger.info("  Temps total:        %.2fs", elapsed)
        logger.info("  Debit:              %.0f evt/s", rate)
        logger.info("-" * 40)

        assert elapsed < 10.0, f"Trop lent: {elapsed:.2f}s (limite: 10s)"
        assert errors == 0, f"{errors} erreurs d'envoi sur {num_events}"

        # --- Cleanup ---
        producer.close()
        logger.info("TEST THROUGHPUT: SUCCES")
        logger.info("=" * 60)
