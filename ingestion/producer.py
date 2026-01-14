"""Kafka Producer pour événements e-commerce en temps réel.

Ce module implémente un producer Kafka qui génère des événements
synthétiques e-commerce et les envoie vers les topics Kafka.
"""
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from random import Random

from confluent_kafka import Producer
from faker import Faker

# Ajout du répertoire parent au path pour importer config
sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')
from config.constants import (
    KAFKA_BROKERS,
    KAFKA_TOPICS,
    PRODUCER_CONFIG,
    PRODUCER_EVENT_INTERVAL,
    PRODUCER_BATCH_SIZE,
    EVENT_TYPES,
    EVENT_TYPE_WEIGHTS,
    PRODUCT_CATEGORIES,
    PRICE_RANGES,
    FAKER_LOCALE,
    FAKER_SEED,
    LOG_LEVEL,
    LOG_FORMAT,
)

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
)
logger = logging.getLogger(__name__)


class KafkaEventProducer:
    """Producer Kafka pour événements e-commerce synthétiques."""

    def __init__(self, brokers: str = KAFKA_BROKERS, speed_multiplier: float = 1.0):
        """Initialise le producer Kafka.

        Args:
            brokers: Adresse des brokers Kafka (host:port)
            speed_multiplier: Multiplicateur de vitesse (1.0=normal, 10.0=10x plus rapide)
        """
        self.brokers = brokers
        self.speed_multiplier = speed_multiplier
        self.event_interval = PRODUCER_EVENT_INTERVAL / speed_multiplier

        producer_config = PRODUCER_CONFIG.copy()
        producer_config['bootstrap.servers'] = brokers

        try:
            self.producer = Producer(producer_config)
            logger.info(f"Producer Kafka initialisé: {brokers} (vitesse: {speed_multiplier}x)")
        except Exception as e:
            logger.error(f"Échec initialisation producer: {str(e)}")
            raise

        self.faker = Faker(FAKER_LOCALE)
        Faker.seed(FAKER_SEED)
        self.random = Random(FAKER_SEED)

        self.events_sent = 0
        self.events_failed = 0

    def _delivery_callback(self, err: Optional[Exception], msg) -> None:
        """Callback appelé après l'envoi d'un message.

        Args:
            err: Exception si erreur, None si succès
            msg: Message Kafka envoyé
        """
        if err is not None:
            logger.error(f"Échec envoi message: {err}")
            self.events_failed += 1
        else:
            logger.debug(
                f"Message envoyé: topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}"
            )
            self.events_sent += 1

    def _generate_event_id(self) -> str:
        """Génère un ID unique pour l'événement.

        Returns:
            UUID v4 sous forme de string
        """
        return str(uuid.uuid4())

    def _select_event_type(self) -> str:
        """Sélectionne aléatoirement un type d'événement selon les poids.

        Returns:
            Type d'événement ('view', 'addtocart', 'transaction', etc.)
        """
        return self.random.choices(
            population=EVENT_TYPES,
            weights=[EVENT_TYPE_WEIGHTS[t] for t in EVENT_TYPES],
            k=1
        )[0]

    def _generate_base_event(self) -> Dict:
        """Génère les champs communs à tous les événements.

        Returns:
            Dictionnaire avec les champs de base
        """
        return {
            'event_id': self._generate_event_id(),
            'timestamp': int(datetime.now().timestamp() * 1000),
            'user_id': str(self.faker.random_int(min=1000, max=50000)),
            'session_id': str(uuid.uuid4()),
            'device_type': self.random.choice(['desktop', 'mobile', 'tablet']),
            'ip_address': self.faker.ipv4(),
            'user_agent': self.faker.user_agent(),
        }

    def _generate_view_event(self) -> Dict:
        """Génère un événement 'view' (consultation produit).

        Returns:
            Événement view complet
        """
        category = self.random.choice(PRODUCT_CATEGORIES)
        event = self._generate_base_event()
        event.update({
            'event_type': 'view',
            'item_id': str(self.faker.random_int(min=1, max=10000)),
            'category': category,
        })
        return event

    def _generate_addtocart_event(self) -> Dict:
        """Génère un événement 'addtocart' (ajout au panier).

        Returns:
            Événement addtocart complet
        """
        category = self.random.choice(PRODUCT_CATEGORIES)
        price_range = PRICE_RANGES[category]
        event = self._generate_base_event()
        event.update({
            'event_type': 'addtocart',
            'item_id': str(self.faker.random_int(min=1, max=10000)),
            'category': category,
            'price': round(self.random.uniform(*price_range), 2),
            'quantity': self.random.randint(1, 5),
        })
        return event

    def _generate_transaction_event(self) -> Dict:
        """Génère un événement 'transaction' (achat).

        Returns:
            Événement transaction complet
        """
        category = self.random.choice(PRODUCT_CATEGORIES)
        price_range = PRICE_RANGES[category]
        event = self._generate_base_event()
        event.update({
            'event_type': 'transaction',
            'item_id': str(self.faker.random_int(min=1, max=10000)),
            'category': category,
            'price': round(self.random.uniform(*price_range), 2),
            'quantity': self.random.randint(1, 3),
        })
        return event

    def _generate_search_event(self) -> Dict:
        """Génère un événement 'search' (recherche).

        Returns:
            Événement search complet
        """
        search_terms = [
            'laptop', 'phone', 'shirt', 'shoes', 'book', 'headphones',
            'watch', 'camera', 'tablet', 'keyboard', 'mouse', 'monitor'
        ]
        event = self._generate_base_event()
        event.update({
            'event_type': 'search',
            'search_query': self.random.choice(search_terms),
        })
        return event

    def _generate_filter_event(self) -> Dict:
        """Génère un événement 'filter' (filtrage).

        Returns:
            Événement filter complet
        """
        filter_types = ['price', 'category', 'brand', 'rating']
        filter_values = {
            'price': ['0-50', '50-100', '100-500', '500+'],
            'category': PRODUCT_CATEGORIES,
            'brand': ['Apple', 'Samsung', 'Nike', 'Adidas', 'Sony'],
            'rating': ['1', '2', '3', '4', '5'],
        }
        filter_type = self.random.choice(filter_types)
        event = self._generate_base_event()
        event.update({
            'event_type': 'filter',
            'filter_type': filter_type,
            'filter_value': self.random.choice(filter_values[filter_type]),
        })
        return event

    def _generate_review_event(self) -> Dict:
        """Génère un événement 'review' (avis client).

        Returns:
            Événement review complet
        """
        category = self.random.choice(PRODUCT_CATEGORIES)
        event = self._generate_base_event()
        event.update({
            'event_type': 'review',
            'item_id': str(self.faker.random_int(min=1, max=10000)),
            'category': category,
            'rating': self.random.randint(1, 5),
            'review_text': self.faker.sentence(nb_words=10),
        })
        return event

    def generate_event(self) -> Dict:
        """Génère un événement aléatoire selon les poids configurés.

        Returns:
            Événement e-commerce complet
        """
        event_type = self._select_event_type()

        generators = {
            'view': self._generate_view_event,
            'addtocart': self._generate_addtocart_event,
            'transaction': self._generate_transaction_event,
            'search': self._generate_search_event,
            'filter': self._generate_filter_event,
            'review': self._generate_review_event,
        }

        generator = generators.get(event_type)
        if not generator:
            logger.warning(f"Type d'événement inconnu: {event_type}")
            return self._generate_view_event()

        return generator()

    def send_event(self, event: Dict, topic: str = 'events') -> bool:
        """Envoie un événement vers Kafka.

        Args:
            event: Événement à envoyer (dictionnaire)
            topic: Nom du topic (clé dans KAFKA_TOPICS)

        Returns:
            True si succès, False si échec
        """
        if 'user_id' not in event or 'event_type' not in event:
            logger.warning(f"Événement invalide (champs manquants): {event}")
            return False

        topic_name = KAFKA_TOPICS.get(topic)
        if not topic_name:
            logger.error(f"Topic inconnu: {topic}")
            return False

        try:
            value = json.dumps(event).encode('utf-8')
            key = str(event['user_id']).encode('utf-8')

            self.producer.produce(
                topic=topic_name,
                key=key,
                value=value,
                callback=self._delivery_callback,
            )
            self.producer.poll(0)
            return True

        except BufferError:
            logger.warning("Buffer plein, attente...")
            self.producer.flush()
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi: {str(e)}")
            return False

    def run(self, num_events: Optional[int] = None) -> None:
        """Lance la génération et l'envoi d'événements.

        Args:
            num_events: Nombre d'événements à générer (None = infini)
        """
        logger.info(f"Démarrage du producer (intervalle: {self.event_interval:.3f}s)")

        try:
            count = 0
            while True:
                if num_events and count >= num_events:
                    break

                event = self.generate_event()
                self.send_event(event)

                count += 1
                if count % 100 == 0:
                    logger.info(f"Événements envoyés: {self.events_sent}, échecs: {self.events_failed}")

                time.sleep(self.event_interval)

        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        finally:
            logger.info("Flush des messages en attente...")
            self.producer.flush()
            logger.info(
                f"Producer arrêté. Total: {self.events_sent} envoyés, {self.events_failed} échecs"
            )

    def close(self) -> None:
        """Ferme proprement le producer."""
        logger.info("Fermeture du producer...")
        self.producer.flush()


def main() -> None:
    """Point d'entrée principal du producer."""
    import argparse

    parser = argparse.ArgumentParser(description='Kafka Event Producer pour e-commerce')
    parser.add_argument('--brokers', default=KAFKA_BROKERS, help='Kafka brokers')
    parser.add_argument('--speed', type=float, default=1.0, help='Multiplicateur de vitesse')
    parser.add_argument('--num-events', type=int, default=None, help='Nombre d\'événements')

    args = parser.parse_args()

    producer = KafkaEventProducer(brokers=args.brokers, speed_multiplier=args.speed)
    producer.run(num_events=args.num_events)


if __name__ == '__main__':
    main()
