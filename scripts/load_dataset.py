"""Script de chargement du dataset Retail Rocket.

Ce script charge le dataset Retail Rocket (events.csv) et envoie
les événements vers Kafka via le producer.
"""
import csv
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, 'D:\\bureau\\grand projet\\PROJET 1')
from ingestion.producer import KafkaEventProducer
from config.constants import (
    RETAIL_ROCKET_EVENTS_PATH,
    DATASET_MAX_ROWS,
    KAFKA_BROKERS,
    LOG_LEVEL,
    LOG_FORMAT,
)

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def load_retail_rocket_dataset(
    csv_path: str,
    max_rows: int = DATASET_MAX_ROWS,
    speed_multiplier: float = 1.0
) -> None:
    """Charge le dataset Retail Rocket et l'envoie vers Kafka.

    Args:
        csv_path: Chemin vers le fichier events.csv
        max_rows: Nombre maximum de lignes à charger
        speed_multiplier: Multiplicateur de vitesse d'envoi
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        logger.error(f"Fichier dataset non trouvé: {csv_path}")
        logger.info("Téléchargez le dataset Retail Rocket depuis:")
        logger.info("https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset")
        return

    producer = KafkaEventProducer(brokers=KAFKA_BROKERS, speed_multiplier=speed_multiplier)

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0

            logger.info(f"Chargement du dataset: {csv_path}")
            logger.info(f"Limite: {max_rows} lignes")

            for row in reader:
                if count >= max_rows:
                    break

                event = convert_retail_rocket_to_event(row)
                if event:
                    producer.send_event(event)
                    count += 1

                    if count % 1000 == 0:
                        logger.info(f"{count} événements chargés...")

                time.sleep(1.0 / speed_multiplier)

            producer.producer.flush()
            logger.info(f"Chargement terminé: {count} événements envoyés")

    except Exception as e:
        logger.error(f"Erreur lors du chargement: {str(e)}")
    finally:
        producer.close()


def convert_retail_rocket_to_event(row: dict) -> dict:
    """Convertit une ligne du dataset Retail Rocket en événement.

    Args:
        row: Ligne du CSV Retail Rocket

    Returns:
        Événement formaté ou None si invalide
    """
    try:
        event_type_mapping = {
            'view': 'view',
            'addtocart': 'addtocart',
            'transaction': 'transaction',
        }

        event_type = event_type_mapping.get(row.get('event', '').lower())
        if not event_type:
            return None

        event = {
            'event_id': f"rr-{row.get('timestamp', '')}-{row.get('visitorid', '')}",
            'event_type': event_type,
            'timestamp': int(row.get('timestamp', 0)),
            'user_id': str(row.get('visitorid', '')),
            'item_id': str(row.get('itemid', '')),
        }

        if event_type == 'transaction' and 'transactionid' in row:
            event['transaction_id'] = str(row['transactionid'])

        return event

    except Exception as e:
        logger.warning(f"Erreur conversion ligne: {str(e)}")
        return None


def main() -> None:
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Chargement dataset Retail Rocket')
    parser.add_argument('--csv', default=RETAIL_ROCKET_EVENTS_PATH, help='Chemin vers events.csv')
    parser.add_argument('--max-rows', type=int, default=DATASET_MAX_ROWS, help='Limite de lignes')
    parser.add_argument('--speed', type=float, default=1.0, help='Multiplicateur de vitesse')

    args = parser.parse_args()

    load_retail_rocket_dataset(
        csv_path=args.csv,
        max_rows=args.max_rows,
        speed_multiplier=args.speed
    )


if __name__ == '__main__':
    main()
