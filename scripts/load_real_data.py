#!/usr/bin/env python
"""Script to load real datasets into Kafka."""

import sys
import os
import argparse
import logging
from pathlib import Path

# Ajouter le répertoire racine au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.producer import KafkaEventProducer
from ingestion.loaders import RetailRocketLoader, InstacartLoader, OlistLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_retail_rocket(producer: KafkaEventProducer, csv_path: str, max_events: int, speed: float) -> None:
    """Charger les données Retail Rocket."""
    logger.info(f"Chargement Retail Rocket depuis {csv_path}")

    loader = RetailRocketLoader(csv_path)
    count = 0

    for event in loader.load(max_rows=max_events):
        if event:
            producer.send_event(topic='events', event=event)
            count += 1
            if count % 100 == 0:
                logger.debug(f"Envoyé {count} événements...")

    logger.info(f"✅ {count} événements chargés depuis Retail Rocket")


def load_instacart(producer: KafkaEventProducer, orders_path: str, max_events: int, speed: float) -> None:
    """Charger les données Instacart."""
    logger.info(f"Chargement Instacart depuis {orders_path}")

    loader = InstacartLoader(orders_path)
    count = 0

    for event in loader.load(max_rows=max_events):
        if event:
            producer.send_event(topic='events', event=event)
            count += 1
            if count % 100 == 0:
                logger.debug(f"Envoyé {count} événements...")

    logger.info(f"✅ {count} événements chargés depuis Instacart")


def load_olist(producer: KafkaEventProducer, orders_path: str, max_events: int, speed: float) -> None:
    """Charger les données Olist."""
    logger.info(f"Chargement Olist depuis {orders_path}")

    loader = OlistLoader(orders_path)
    count = 0

    for event in loader.load(max_rows=max_events):
        if event:
            producer.send_event(topic='events', event=event)
            count += 1
            if count % 100 == 0:
                logger.debug(f"Envoyé {count} événements...")

    logger.info(f"✅ {count} événements chargés depuis Olist")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Charger les données réelles dans Kafka')
    parser.add_argument('--source', choices=['retail_rocket', 'instacart', 'olist'],
                       default='retail_rocket', help='Source de données')
    parser.add_argument('--csv', help='Chemin vers le fichier CSV')
    parser.add_argument('--orders', help='Chemin vers orders.csv (Instacart/Olist)')
    parser.add_argument('--events', type=int, default=None, help='Nombre d\'événements à charger (défaut: tous)')
    parser.add_argument('--speed', type=float, default=1.0, help='Multiplicateur de vitesse')
    parser.add_argument('--brokers', default='localhost:9092', help='Serveur Kafka')

    args = parser.parse_args()

    try:
        # Initialiser le producer
        producer = KafkaEventProducer(brokers=args.brokers)
        logger.info(f"🚀 Démarrage du chargement des données")
        logger.info(f"   Source: {args.source}")
        logger.info(f"   Événements: {args.events}")
        logger.info(f"   Vitesse: {args.speed}x")

        # Charger selon la source
        if args.source == 'retail_rocket':
            if not args.csv:
                logger.error("❌ --csv est requis pour retail_rocket")
                return 1
            load_retail_rocket(producer, args.csv, args.events, args.speed)

        elif args.source == 'instacart':
            if not args.orders:
                logger.error("❌ --orders est requis pour instacart")
                return 1
            load_instacart(producer, args.orders, args.events, args.speed)

        elif args.source == 'olist':
            if not args.orders:
                logger.error("❌ --orders est requis pour olist")
                return 1
            load_olist(producer, args.orders, args.events, args.speed)

        logger.info("✅ SUCCÈS - Toutes les données ont été chargées")
        return 0

    except Exception as e:
        logger.error(f"❌ ERREUR - {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
