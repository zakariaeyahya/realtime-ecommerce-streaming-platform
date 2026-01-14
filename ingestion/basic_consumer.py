"""Kafka Consumer pour événements e-commerce en temps réel.

Ce module implémente un consumer Kafka qui lit les événements e-commerce
depuis les topics Kafka et les traite.
"""
import json
import logging
import sys
from typing import Dict, List, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

# Ajout du répertoire parent au path pour importer config
sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')
from config.constants import (
    KAFKA_BROKERS,
    KAFKA_TOPICS,
    CONSUMER_CONFIG,
    CONSUMER_POLL_TIMEOUT,
    REQUIRED_EVENT_FIELDS,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
)
logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    """Consumer Kafka pour événements e-commerce."""

    def __init__(
        self,
        brokers: str = KAFKA_BROKERS,
        group_id: str = 'ecommerce-consumer-group',
        topics: Optional[List[str]] = None
    ):
        """Initialise le consumer Kafka.

        Args:
            brokers: Adresse des brokers Kafka (host:port)
            group_id: Groupe de consommateurs Kafka
            topics: Liste des topics à consommer (clés dans KAFKA_TOPICS)
        """
        self.brokers = brokers
        self.group_id = group_id

        consumer_config = CONSUMER_CONFIG.copy()
        consumer_config['bootstrap.servers'] = brokers
        consumer_config['group.id'] = group_id

        try:
            self.consumer = Consumer(consumer_config)
            logger.info(f"Consumer Kafka initialisé: {brokers} (groupe: {group_id})")
        except Exception as e:
            logger.error(f"Échec initialisation consumer: {str(e)}")
            raise

        self.topics = topics or ['events']
        self.topic_names = [KAFKA_TOPICS[t] for t in self.topics if t in KAFKA_TOPICS]

        if not self.topic_names:
            logger.error(f"Aucun topic valide trouvé dans: {self.topics}")
            raise ValueError("Au moins un topic valide est requis")

        self.messages_consumed = 0
        self.messages_invalid = 0

    def subscribe(self) -> None:
        """S'abonne aux topics configurés."""
        try:
            self.consumer.subscribe(self.topic_names)
            logger.info(f"Abonné aux topics: {', '.join(self.topic_names)}")
        except Exception as e:
            logger.error(f"Échec lors de l'abonnement: {str(e)}")
            raise

    def _validate_event(self, event: Dict) -> bool:
        """Valide la structure d'un événement.

        Args:
            event: Événement à valider

        Returns:
            True si valide, False sinon
        """
        if 'event_type' not in event:
            logger.warning("Événement sans event_type")
            return False

        event_type = event['event_type']
        required_fields = REQUIRED_EVENT_FIELDS.get(event_type)

        if not required_fields:
            logger.warning(f"Type d'événement inconnu: {event_type}")
            return False

        missing_fields = [f for f in required_fields if f not in event]
        if missing_fields:
            logger.warning(
                f"Champs manquants pour événement {event_type}: {', '.join(missing_fields)}"
            )
            return False

        return True

    def _process_message(self, message) -> None:
        """Traite un message Kafka.

        Args:
            message: Message Kafka reçu
        """
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                logger.debug(
                    f"Fin de partition: {message.topic()}[{message.partition()}] "
                    f"à offset {message.offset()}"
                )
            else:
                logger.error(f"Erreur consumer: {message.error()}")
            return

        try:
            value = message.value().decode('utf-8')
            event = json.loads(value)

            if not self._validate_event(event):
                self.messages_invalid += 1
                return

            self.messages_consumed += 1

            logger.info(
                f"Événement reçu: type={event.get('event_type')} "
                f"user_id={event.get('user_id')} "
                f"topic={message.topic()} "
                f"partition={message.partition()} "
                f"offset={message.offset()}"
            )

            if self.messages_consumed % 100 == 0:
                logger.info(
                    f"Statistiques: {self.messages_consumed} consommés, "
                    f"{self.messages_invalid} invalides"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Erreur décodage JSON: {str(e)}")
            self.messages_invalid += 1
        except Exception as e:
            logger.error(f"Erreur traitement message: {str(e)}")
            self.messages_invalid += 1

    def run(self) -> None:
        """Lance la consommation des messages."""
        self.subscribe()
        logger.info(f"Démarrage du consumer (poll timeout: {CONSUMER_POLL_TIMEOUT}s)")

        try:
            while True:
                message = self.consumer.poll(timeout=CONSUMER_POLL_TIMEOUT)

                if message is None:
                    continue

                self._process_message(message)

        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        except KafkaException as e:
            logger.error(f"Exception Kafka: {str(e)}")
        finally:
            self.close()

    def close(self) -> None:
        """Ferme proprement le consumer."""
        logger.info("Fermeture du consumer...")
        try:
            self.consumer.close()
            logger.info(
                f"Consumer fermé. Total: {self.messages_consumed} consommés, "
                f"{self.messages_invalid} invalides"
            )
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {str(e)}")


def main() -> None:
    """Point d'entrée principal du consumer."""
    import argparse

    parser = argparse.ArgumentParser(description='Kafka Event Consumer pour e-commerce')
    parser.add_argument('--brokers', default=KAFKA_BROKERS, help='Kafka brokers')
    parser.add_argument(
        '--group-id',
        default='ecommerce-consumer-group',
        help='Consumer group ID'
    )
    parser.add_argument(
        '--topics',
        nargs='+',
        default=['events'],
        help='Topics à consommer (ex: events inventory)'
    )

    args = parser.parse_args()

    consumer = KafkaEventConsumer(
        brokers=args.brokers,
        group_id=args.group_id,
        topics=args.topics
    )
    consumer.run()


if __name__ == '__main__':
    main()
