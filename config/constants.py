# ============================================================================
# KAFKA CONFIGURATION
# ============================================================================
KAFKA_BROKERS = "localhost:9092"
KAFKA_TOPICS = {
    "events": "raw-events",
    "fraud_scores": "fraud-scores",
    "recommendations": "recommendations",
    "inventory": "inventory-changes",
}

# ============================================================================
# KAFKA PRODUCER CONFIGURATION (Sprint 1)
# ============================================================================
PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA_BROKERS,
    'acks': 'all',  # Exactly-once semantics
    'retries': 3,
    'max.in.flight.requests.per.connection': 5,
    'queue.buffering.max.messages': 100000,
    'queue.buffering.max.kbytes': 1048576,  # 1GB buffer
}

PRODUCER_EVENT_INTERVAL = 0.1  # Intervalle entre événements (secondes)
PRODUCER_BATCH_SIZE = 1000  # Nombre d'événements par batch

# ============================================================================
# EVENT TYPES AND CATEGORIES
# ============================================================================
EVENT_TYPES = ['view', 'addtocart', 'transaction', 'search', 'filter', 'review']
EVENT_TYPE_WEIGHTS = {
    'view': 0.50,        # 50% des événements
    'addtocart': 0.15,   # 15%
    'transaction': 0.10, # 10%
    'search': 0.15,      # 15%
    'filter': 0.05,      # 5%
    'review': 0.05,      # 5%
}

PRODUCT_CATEGORIES = [
    'Electronics', 'Fashion', 'Home', 'Sports', 'Books',
    'Beauty', 'Toys', 'Food', 'Furniture', 'Automotive'
]

PRICE_RANGES = {
    'Electronics': (50, 2000),
    'Fashion': (20, 500),
    'Home': (30, 1500),
    'Sports': (25, 800),
    'Books': (5, 50),
    'Beauty': (10, 300),
    'Toys': (10, 200),
    'Food': (5, 100),
    'Furniture': (100, 3000),
    'Automotive': (50, 5000),
}

# ============================================================================
# KAFKA CONSUMER CONFIGURATION (Sprint 1)
# ============================================================================
CONSUMER_CONFIG = {
    'bootstrap.servers': KAFKA_BROKERS,
    'group.id': 'ecommerce-consumer-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
}

CONSUMER_POLL_TIMEOUT = 1.0  # Timeout pour consumer.poll() en secondes

# ============================================================================
# EVENT VALIDATION
# ============================================================================
REQUIRED_EVENT_FIELDS = {
    'view': ['event_id', 'event_type', 'timestamp', 'user_id', 'item_id', 'category'],
    'addtocart': ['event_id', 'event_type', 'timestamp', 'user_id', 'item_id', 'price', 'quantity'],
    'transaction': ['event_id', 'event_type', 'timestamp', 'user_id', 'item_id', 'price', 'quantity'],
    'search': ['event_id', 'event_type', 'timestamp', 'user_id', 'search_query'],
    'filter': ['event_id', 'event_type', 'timestamp', 'user_id', 'filter_type', 'filter_value'],
    'review': ['event_id', 'event_type', 'timestamp', 'user_id', 'item_id', 'rating'],
}

# ============================================================================
# FAKER CONFIGURATION
# ============================================================================
FAKER_LOCALE = 'en_US'
FAKER_SEED = 42

# ============================================================================
# FRAUD DETECTION (Sprint 3)
# ============================================================================
FRAUD_THRESHOLD = 0.85
FRAUD_MIN_FEATURES = 90
FRAUD_MODEL_PATH = "processing/models/fraud_model.pkl"

# ============================================================================
# INVENTORY FORECASTING (Sprint 5)
# ============================================================================
INVENTORY_ALERT_THRESHOLD = 100
INVENTORY_FORECAST_DAYS = 7
INVENTORY_MODEL_PATH = "processing/models/inventory_forecast_models.joblib"
INVENTORY_WINDOW_SIZE_SECONDS = 86400  # 24 hours
INVENTORY_FEATURE_COUNT = 50

PROPHET_SEASONALITY_MODE = "multiplicative"
ARIMA_P, ARIMA_D, ARIMA_Q = 5, 1, 2
ENSEMBLE_PROPHET_WEIGHT = 0.6
ENSEMBLE_ARIMA_WEIGHT = 0.4

INVENTORY_FORECAST_ACCURACY_TARGET = 0.85
INVENTORY_MAX_LATENCY_MS = 2000

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_INVENTORY_TTL_SECONDS = 604800  # 7 days
REDIS_CACHE_TTL_FRAUD = 86400  # 24h

# ============================================================================
# FLINK CONFIGURATION
# ============================================================================
FLINK_PARALLELISM = 4
FLINK_CHECKPOINT_INTERVAL_MS = 30000
FLINK_STATE_BACKEND = "rocksdb"
FLINK_WINDOW_SIZE_SECONDS = 300  # 5 minutes

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================
RETAIL_ROCKET_EVENTS_PATH = "data/raw/retail_rocket/events.csv"
DATASET_MAX_ROWS = 10000  # Limiter pour les tests, augmenter pour prod
DATASET_BATCH_SIZE = 1000  # Nombre d'événements avant flush

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# DEFAULTS
# ============================================================================
INVENTORY_DEFAULT_REORDER_POINT = 100
INVENTORY_DEFAULT_LEAD_TIME_DAYS = 7

# ============================================================================
# API CONFIGURATION (Sprint 7)
# ============================================================================
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 1

# Redis key prefixes
REDIS_KEY_FRAUD = "fraud"
REDIS_KEY_RECO = "reco"
REDIS_KEY_INVENTORY = "inventory"
REDIS_CACHE_TTL_RECO = 3600  # 1h
