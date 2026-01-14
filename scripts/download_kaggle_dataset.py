#!/usr/bin/env python3
"""
Script pour télécharger automatiquement les datasets Kaggle.

Supporte:
- Retail Rocket (2.7M événements - RECOMMANDÉ)
- Instacart (3M+ commandes)
- Olist (99k commandes)

Credentials: Lire depuis .env (KAGGLE_USERNAME et KAGGLE_API_TOKEN)

Usage:
    python scripts/download_kaggle_dataset.py --dataset retail_rocket
    python scripts/download_kaggle_dataset.py --dataset instacart
    python scripts/download_kaggle_dataset.py --dataset olist
"""

import os
import sys
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import argparse
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env (racine du projet)
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

# Debug: Vérifier que le fichier existe
if not env_file.exists():
    print(f"ERREUR: Fichier .env non trouvé à {env_file}")
    sys.exit(1)

# Parser manuellement le fichier .env
def load_env_file(env_path: Path) -> None:
    """Parser et charger les variables depuis .env."""
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                os.environ[key] = value

# Charger depuis le fichier .env
load_env_file(env_file)
load_dotenv(env_file, override=True)  # Fallback

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Vérifier immédiatement que .env est chargé
logger.debug(f"Fichier .env trouvé: {env_file.exists()}")
logger.debug(f"Contenu de .env (premières lignes):")
if env_file.exists():
    with open(env_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 10:  # Premières 10 lignes
                logger.debug(f"  {line.rstrip()}")
            if 'KAGGLE' in line:
                logger.debug(f"  >>> {line.rstrip()}")

# ============================================================================
# CONFIGURATION DATASETS
# ============================================================================

DATASETS = {
    "retail_rocket": {
        "kaggle_id": "retailrocket/ecommerce-dataset",
        "output_dir": "data/raw/retail_rocket",
        "files": ["events.csv"],
        "description": "2.7M e-commerce events (PRIORITAIRE)",
        "size": "~500 MB",
    },
    "instacart": {
        "kaggle_id": "psparks/instacart-market-basket-analysis",
        "output_dir": "data/raw/instacart",
        "files": [
            "orders.csv",
            "products.csv",
            "order_products__prior.csv",
            "order_products__train.csv",
            "aisles.csv",
            "departments.csv",
        ],
        "description": "3M+ orders with multiple files",
        "size": "~1 GB",
    },
    "olist": {
        "kaggle_id": "olistbr/brazilian-ecommerce",
        "output_dir": "data/raw/olist",
        "files": [
            "olist_orders_dataset.csv",
            "olist_orders_items_dataset.csv",
            "olist_customers_dataset.csv",
            "olist_products_dataset.csv",
            "olist_sellers_dataset.csv",
            "olist_order_reviews_dataset.csv",
            "olist_order_payments_dataset.csv",
        ],
        "description": "99k Brazilian e-commerce orders",
        "size": "~200 MB",
    },
}


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================


def check_kaggle_installed() -> bool:
    """Vérifier que le package kaggle est installé."""
    try:
        import kaggle
        logger.info("✅ Package kaggle détecté")
        return True
    except ImportError:
        logger.error("❌ Package kaggle non trouvé")
        logger.error("   Installer avec: pip install kaggle")
        return False


def check_kaggle_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Vérifier les credentials Kaggle depuis .env."""
    # Lire directement depuis le fichier .env
    username = None
    token = None

    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('KAGGLE_USERNAME='):
                username = line.split('=', 1)[1]
            elif line.startswith('KAGGLE_API_TOKEN='):
                token = line.split('=', 1)[1]

    logger.debug(f"DEBUG: KAGGLE_USERNAME (from file) = {username}")
    logger.debug(f"DEBUG: KAGGLE_API_TOKEN (from file) = {token}")

    if not username or not token:
        logger.error("❌ Credentials Kaggle manquants dans .env")
        logger.error(f"   KAGGLE_USERNAME: {username}")
        logger.error(f"   KAGGLE_API_TOKEN: {token}")
        logger.error("   Vérifier que .env contient:")
        logger.error("   KAGGLE_USERNAME=votre_username")
        logger.error("   KAGGLE_API_TOKEN=votre_token")
        return None, None

    logger.info(f"✅ Credentials Kaggle trouvés pour: {username}")
    return username, token


def download_dataset(dataset_name: str, username: str, token: str) -> bool:
    """Télécharger un dataset depuis Kaggle."""
    if dataset_name not in DATASETS:
        logger.error(f"❌ Dataset '{dataset_name}' inconnu")
        logger.info(f"   Datasets disponibles: {', '.join(DATASETS.keys())}")
        return False

    config = DATASETS[dataset_name]
    logger.info(f"\n📥 Téléchargement: {dataset_name}")
    logger.info(f"   Description: {config['description']}")
    logger.info(f"   Taille: {config['size']}")

    try:
        import kaggle

        # Configurer les credentials Kaggle
        os.environ['KAGGLE_USERNAME'] = username
        os.environ['KAGGLE_API_KEY'] = token

        # Créer le répertoire temporaire
        temp_dir = Path("temp_kaggle_download")
        temp_dir.mkdir(exist_ok=True)

        logger.info(f"   Dossier temp: {temp_dir}")

        # Télécharger
        logger.info(f"   Téléchargement de: {config['kaggle_id']}")
        kaggle.api.dataset_download_files(
            config['kaggle_id'],
            path=str(temp_dir),
            unzip=True
        )

        logger.info("✅ Téléchargement réussi")
        return extract_and_organize(dataset_name, temp_dir)

    except Exception as e:
        logger.error(f"❌ Erreur lors du téléchargement: {str(e)}")
        return False


def extract_and_organize(dataset_name: str, temp_dir: Path) -> bool:
    """Extraire et organiser les fichiers téléchargés."""
    config = DATASETS[dataset_name]
    output_dir = Path(config['output_dir'])

    try:
        logger.info(f"\n📂 Organisation des fichiers...")
        logger.info(f"   Destination: {output_dir}")

        # Créer le répertoire de destination
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copier les fichiers nécessaires
        files_copied = 0
        for file_name in config['files']:
            source_file = temp_dir / file_name

            # Chercher le fichier (peut être dans un sous-dossier)
            if not source_file.exists():
                # Chercher récursivement
                for root, dirs, files in os.walk(temp_dir):
                    if file_name in files:
                        source_file = Path(root) / file_name
                        break

            if source_file.exists():
                dest_file = output_dir / file_name
                shutil.copy2(source_file, dest_file)
                logger.info(f"   ✅ Copié: {file_name}")
                files_copied += 1
            else:
                logger.warning(f"   ⚠️  Fichier non trouvé: {file_name}")

        # Nettoyer le dossier temporaire
        logger.info(f"\n🧹 Nettoyage du dossier temporaire...")
        shutil.rmtree(temp_dir)
        logger.info("✅ Dossier temporaire supprimé")

        # Vérifier
        logger.info(f"\n✅ {files_copied} fichiers copiés vers {output_dir}/")
        verify_files(output_dir, config['files'])

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'organisation: {str(e)}")
        return False


def verify_files(output_dir: Path, expected_files: list) -> None:
    """Vérifier que tous les fichiers sont présents."""
    logger.info(f"\n🔍 Vérification des fichiers...")

    total_size = 0
    for file_name in expected_files:
        file_path = output_dir / file_name
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            total_size += file_path.stat().st_size
            logger.info(f"   ✅ {file_name}: {size_mb:.2f} MB")
        else:
            logger.warning(f"   ❌ Manquant: {file_name}")

    total_size_mb = total_size / (1024 * 1024)
    logger.info(f"\n📊 Taille totale: {total_size_mb:.2f} MB")


def list_datasets() -> None:
    """Lister les datasets disponibles."""
    logger.info("\n📚 Datasets disponibles:\n")
    for name, config in DATASETS.items():
        logger.info(f"  • {name}")
        logger.info(f"    Description: {config['description']}")
        logger.info(f"    Taille: {config['size']}")
        logger.info(f"    Fichiers: {len(config['files'])} fichiers")
        logger.info(f"    Destination: {config['output_dir']}")
        logger.info("")


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Télécharger automatiquement les datasets Kaggle"
    )
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()),
        help="Dataset à télécharger (retail_rocket, instacart, olist)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lister les datasets disponibles"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("🤖 Téléchargeur Automatique de Datasets Kaggle")
    logger.info("=" * 70)

    # Lister les datasets
    if args.list:
        list_datasets()
        return 0

    # Vérifier les prérequis
    if not check_kaggle_installed():
        return 1

    username, token = check_kaggle_credentials()
    if not username or not token:
        return 1

    # Télécharger le dataset
    if args.dataset:
        if download_dataset(args.dataset, username, token):
            logger.info("\n✅ SUCCÈS - Dataset téléchargé et organisé")
            logger.info(f"   Destination: {DATASETS[args.dataset]['output_dir']}/")
            return 0
        else:
            logger.error("\n❌ ERREUR - Téléchargement échoué")
            return 1
    else:
        logger.error("❌ Erreur: Spécifier --dataset ou --list")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
