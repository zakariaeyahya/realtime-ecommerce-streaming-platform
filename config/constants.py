"""Configuration centralisée pour Sprint 1 - E-Commerce Real-Time Platform.

Ce module contient toutes les constantes et configurations externalisées.
Aucune valeur ne doit être hardcodée dans le code métier.
"""
import os
from typing import Dict, List
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# ============================================================================
# KAFKA CONFIGURATION
# ============================================================================

KAFKA_BROKERS: str = os.getenv('KAFKA_BROKERS', 'localhost:9092')
KAFKA_SCHEMA_REGISTRY_URL: str = os.getenv('KAFKA_SCHEMA_REGISTRY_URL', 'http://localhost:8081')

KAFKA_TOPICS: Dict[str, str] = {
    'events': 'raw-events',
    'inventory': 'inventory-changes',
    'fraud_scores': 'fraud-scores',
    'recommendations': 'recommendations',
    'metrics': 'business-metrics',
}

KAFKA_TOPIC_CONFIGS: Dict[str, Dict[str, int]] = {
    'raw-events': {
        'partitions': 3,
        'replication_factor': 1,
        'retention_ms': 604800000,  # 7 jours
    },
    'inventory-changes': {
        'partitions': 2,
        'replication_factor': 1,
        'retention_ms': 2592000000,  # 30 jours
    },
    'fraud-scores': {
        'partitions': 2,
        'replication_factor': 1,
        'retention_ms': 604800000,  # 7 jours
    },
    'recommendations': {
        'partitions': 2,
        'replication_factor': 1,
        'retention_ms': 86400000,  # 24 heures
    },
    'business-metrics': {
        'partitions': 1,
        'replication_factor': 1,
        'retention_ms': 2592000000,  # 30 jours
    },
}

# ============================================================================
# PRODUCER CONFIGURATION
# ============================================================================

PRODUCER_CONFIG: Dict[str, any] = {
    'bootstrap.servers': KAFKA_BROKERS,
    'acks': 'all',
    'retries': 3,
    'max.in.flight.requests.per.connection': 1,
    'compression.type': 'snappy',
    'linger.ms': 10,
    'batch.size': 16384,
}

PRODUCER_BATCH_SIZE: int = int(os.getenv('PRODUCER_BATCH_SIZE', '100'))
PRODUCER_RETRIES: int = int(os.getenv('PRODUCER_RETRIES', '3'))
PRODUCER_SPEED: float = float(os.getenv('PRODUCER_SPEED', '1.0'))
PRODUCER_EVENT_INTERVAL: float = 1.0 / PRODUCER_SPEED  # Secondes entre événements

# ============================================================================
# CONSUMER CONFIGURATION
# ============================================================================

CONSUMER_CONFIG: Dict[str, any] = {
    'bootstrap.servers': KAFKA_BROKERS,
    'group.id': os.getenv('CONSUMER_GROUP_ID', 'ecommerce-consumer-group'),
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 5000,
    'session.timeout.ms': 30000,
    'max.poll.interval.ms': 300000,
}

CONSUMER_POLL_TIMEOUT: float = 1.0  # Secondes

# ============================================================================
# SCHEMA PATHS
# ============================================================================

SCHEMA_DIR: str = os.path.join(os.path.dirname(__file__), '..', 'ingestion', 'schema')
EVENT_SCHEMA_PATH: str = os.path.join(SCHEMA_DIR, 'event_schema.avsc')
INVENTORY_SCHEMA_PATH: str = os.path.join(SCHEMA_DIR, 'inventory_schema.avsc')

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# DATA GENERATION CONFIGURATION
# ============================================================================

FAKER_LOCALE: str = 'fr_FR'
FAKER_SEED: int = int(os.getenv('FAKER_SEED', '42'))

# Types d'événements e-commerce
EVENT_TYPES: List[str] = [
    'view',
    'addtocart',
    'transaction',
    'search',
    'filter',
    'review',
]

# Poids de probabilité pour chaque type d'événement
EVENT_TYPE_WEIGHTS: Dict[str, float] = {
    'view': 0.50,         # 50% des événements
    'addtocart': 0.20,    # 20% des événements
    'transaction': 0.10,  # 10% des événements
    'search': 0.10,       # 10% des événements
    'filter': 0.07,       # 7% des événements
    'review': 0.03,       # 3% des événements
}

# Catégories de produits
PRODUCT_CATEGORIES: List[str] = [
    'Electronics',
    'Clothing',
    'Books',
    'Home & Garden',
    'Sports & Outdoors',
    'Beauty & Health',
    'Toys & Games',
    'Automotive',
    'Food & Beverages',
    'Office Supplies',
]

# Fourchettes de prix par catégorie (min, max)
PRICE_RANGES: Dict[str, tuple] = {
    'Electronics': (50, 2000),
    'Clothing': (10, 300),
    'Books': (5, 50),
    'Home & Garden': (15, 500),
    'Sports & Outdoors': (20, 800),
    'Beauty & Health': (5, 200),
    'Toys & Games': (10, 150),
    'Automotive': (20, 1000),
    'Food & Beverages': (2, 100),
    'Office Supplies': (5, 300),
}

# ============================================================================
# REDIS CONFIGURATION (Pour Sprints futurs)
# ============================================================================

REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD: str = os.getenv('REDIS_PASSWORD', '')

# ============================================================================
# DATABASE CONFIGURATION (Pour Sprints futurs)
# ============================================================================

DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/ecommerce')
DATABASE_POOL_SIZE: int = int(os.getenv('DATABASE_POOL_SIZE', '10'))

# ============================================================================
# MONITORING CONFIGURATION
# ============================================================================

METRICS_ENABLED: bool = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
METRICS_PORT: int = int(os.getenv('METRICS_PORT', '9090'))

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================

DATASET_DIR: str = os.path.join(os.path.dirname(__file__), '..', 'data')
RETAIL_ROCKET_EVENTS_PATH: str = os.path.join(DATASET_DIR, 'events.csv')
RETAIL_ROCKET_ITEMS_PATH: str = os.path.join(DATASET_DIR, 'item_properties.csv')

# Limite de lignes à charger depuis le dataset (None = tout)
DATASET_MAX_ROWS: int = int(os.getenv('DATASET_MAX_ROWS', '100000'))

# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

# Taille maximale d'un événement en bytes
MAX_EVENT_SIZE: int = 1024 * 100  # 100 KB

# Champs obligatoires pour chaque type d'événement
REQUIRED_EVENT_FIELDS: Dict[str, List[str]] = {
    'view': ['event_type', 'timestamp', 'user_id', 'item_id'],
    'addtocart': ['event_type', 'timestamp', 'user_id', 'item_id'],
    'transaction': ['event_type', 'timestamp', 'user_id', 'item_id', 'price', 'quantity'],
    'search': ['event_type', 'timestamp', 'user_id', 'search_query'],
    'filter': ['event_type', 'timestamp', 'user_id', 'filter_type', 'filter_value'],
    'review': ['event_type', 'timestamp', 'user_id', 'item_id', 'rating'],
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

MAX_RETRY_ATTEMPTS: int = 3
RETRY_BACKOFF_MULTIPLIER: float = 2.0
RETRY_BASE_DELAY: float = 1.0  # Secondes

# ============================================================================
# FRAUD DETECTION (Pour Sprint 4)
# ============================================================================

FRAUD_THRESHOLD: float = float(os.getenv('FRAUD_THRESHOLD', '0.85'))

# ============================================================================
# ENVIRONMENT
# ============================================================================

ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
