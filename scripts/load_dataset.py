"""Script de chargement du dataset Retail Rocket.

Ce script charge le dataset Retail Rocket (events.csv) et envoie
les événements vers Kafka via le producer.
"""
import csv
import logging
import sys
import time
from pathlib import Path

# Ajout du répertoire parent au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    logger.info("=" * 70)
    logger.info("DÉBUT CHARGEMENT DATASET RETAIL ROCKET")
    logger.info("=" * 70)

    csv_file = Path(csv_path)
    logger.debug(f"Chemin fourni: {csv_path}")
    logger.debug(f"Chemin absolu: {csv_file.absolute()}")
    logger.debug(f"Existe: {csv_file.exists()}")

    if not csv_file.exists():
        logger.error(f"❌ ERREUR: Fichier dataset non trouvé: {csv_path}")
        logger.info("📥 Téléchargez le dataset Retail Rocket depuis:")
        logger.info("   https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset")
        logger.info("📁 Placez le fichier events.csv dans: data/retail_rocket/")
        return

    logger.info(f"✅ Fichier trouvé: {csv_file.name}")

    try:
        logger.info(f"🔌 Connexion à Kafka: {KAFKA_BROKERS}")
        producer = KafkaEventProducer(brokers=KAFKA_BROKERS, speed_multiplier=speed_multiplier)
        logger.info("✅ Producer Kafka initialisé")

    except Exception as e:
        logger.error(f"❌ ERREUR: Impossible de créer le Producer Kafka")
        logger.error(f"   Raison: {str(e)}")
        logger.error(f"   Vérifiez que Kafka tourne: docker-compose ps")
        return

    events_sent = 0
    events_failed = 0
    rows_processed = 0

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                logger.error("❌ ERREUR: Fichier CSV vide ou invalide")
                return

            logger.info(f"📋 Colonnes détectées: {reader.fieldnames}")
            logger.info(f"🚀 Démarrage du chargement (max {max_rows} lignes, vitesse {speed_multiplier}x)")

            for row in reader:
                rows_processed += 1

                if rows_processed > max_rows:
                    logger.info(f"⏹️  Limite atteinte ({max_rows} lignes)")
                    break

                try:
                    event = convert_retail_rocket_to_event(row)
                    if event:
                        success = producer.send_event(event)
                        if success:
                            events_sent += 1
                        else:
                            events_failed += 1
                            logger.warning(f"⚠️  Événement {events_sent + events_failed} non envoyé")
                    else:
                        logger.debug(f"⏭️  Ligne {rows_processed} ignorée (événement None)")

                    # Logs de progression
                    if events_sent % 1000 == 0 and events_sent > 0:
                        logger.info(f"📊 Progression: {events_sent} envoyés, {events_failed} échoués, {rows_processed} lignes lues")

                except Exception as e:
                    events_failed += 1
                    logger.error(f"❌ Erreur ligne {rows_processed}: {str(e)}")

                time.sleep(1.0 / speed_multiplier)

            # Flush final
            logger.info("💾 Flush des messages en attente...")
            producer.producer.flush()
            logger.info("✅ Flush terminé")

            logger.info("=" * 70)
            logger.info("✅ CHARGEMENT TERMINÉ")
            logger.info("=" * 70)
            logger.info(f"📈 Résultats:")
            logger.info(f"   • Lignes traitées: {rows_processed}")
            logger.info(f"   • Événements envoyés: {events_sent}")
            logger.info(f"   • Événements échoués: {events_failed}")
            logger.info(f"   • Taux de succès: {(events_sent / max(1, events_sent + events_failed)) * 100:.1f}%")

    except FileNotFoundError as e:
        logger.error(f"❌ ERREUR: Fichier non trouvé: {str(e)}")
    except csv.Error as e:
        logger.error(f"❌ ERREUR: Erreur CSV: {str(e)}")
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE lors du chargement: {str(e)}")
        logger.exception("Traceback complet:")
    finally:
        logger.info("🔌 Fermeture du Producer Kafka...")
        producer.close()
        logger.info("✅ Producer fermé")


def convert_retail_rocket_to_event(row: dict) -> dict:
    """Convertit une ligne du dataset Retail Rocket en événement.

    Args:
        row: Ligne du CSV Retail Rocket

    Returns:
        Événement formaté ou None si invalide
    """
    try:
        # Mapping des types d'événements Retail Rocket
        event_type_mapping = {
            'view': 'view',
            'addtocart': 'addtocart',
            'transaction': 'transaction',
        }

        # Récupérer et valider le type d'événement
        raw_event_type = row.get('event', '').lower()
        logger.debug(f"Type événement brut: '{raw_event_type}'")

        event_type = event_type_mapping.get(raw_event_type)
        if not event_type:
            logger.debug(f"Type événement non mappé: '{raw_event_type}' → ignoré")
            return None

        # Construire l'événement
        visitor_id = row.get('visitorid', '')
        item_id = row.get('itemid', '')
        timestamp = row.get('timestamp', '')

        if not visitor_id or not item_id or not timestamp:
            logger.debug(f"Champs manquants: visitor_id={visitor_id}, item_id={item_id}, timestamp={timestamp}")
            return None

        event = {
            'event_id': f"rr-{timestamp}-{visitor_id}",
            'event_type': event_type,
            'timestamp': int(timestamp),
            'user_id': str(visitor_id),
            'item_id': str(item_id),
        }

        # Ajouter la transaction ID si présente
        if event_type == 'transaction' and 'transactionid' in row:
            event['transaction_id'] = str(row['transactionid'])

        logger.debug(f"Événement créé: {event}")
        return event

    except ValueError as e:
        logger.warning(f"⚠️  Erreur conversion (valeur invalide): {str(e)}")
        logger.debug(f"   Ligne problématique: {row}")
        return None
    except KeyError as e:
        logger.warning(f"⚠️  Clé manquante dans le CSV: {str(e)}")
        logger.debug(f"   Clés disponibles: {list(row.keys())}")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur conversion inattendue: {str(e)}")
        logger.exception("Traceback complet:")
        return None


def main() -> None:
    """Point d'entrée principal."""
    import argparse

    logger.info("Initialisation du script de chargement dataset...")

    parser = argparse.ArgumentParser(
        description='Chargement dataset Retail Rocket vers Kafka',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Charger 1000 événements
  python scripts/load_dataset.py --max-rows 1000

  # Charger rapidement (10x speed)
  python scripts/load_dataset.py --speed 10.0

  # Utiliser un CSV custom
  python scripts/load_dataset.py --csv /path/to/events.csv
        """
    )
    parser.add_argument(
        '--csv',
        default=RETAIL_ROCKET_EVENTS_PATH,
        help=f'Chemin vers events.csv (défaut: {RETAIL_ROCKET_EVENTS_PATH})'
    )
    parser.add_argument(
        '--max-rows',
        type=int,
        default=DATASET_MAX_ROWS,
        help=f'Limite de lignes à charger (défaut: {DATASET_MAX_ROWS})'
    )
    parser.add_argument(
        '--speed',
        type=float,
        default=1.0,
        help='Multiplicateur de vitesse (1.0=normal, 10.0=10x plus rapide)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activer les logs DEBUG'
    )

    args = parser.parse_args()

    # Activer les logs DEBUG si demandé
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("🔍 Mode DEBUG activé")

    logger.info(f"Configuration:")
    logger.info(f"  • CSV: {args.csv}")
    logger.info(f"  • Max lignes: {args.max_rows}")
    logger.info(f"  • Vitesse: {args.speed}x")
    logger.info(f"  • Kafka: {KAFKA_BROKERS}")

    try:
        load_retail_rocket_dataset(
            csv_path=args.csv,
            max_rows=args.max_rows,
            speed_multiplier=args.speed
        )
        logger.info("✅ Script terminé avec succès")
    except KeyboardInterrupt:
        logger.warning("⏹️  Script interrompu par l'utilisateur (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
        logger.exception("Traceback complet:")


if __name__ == '__main__':
    main()
