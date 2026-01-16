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
# DEFAULTS
# ============================================================================
INVENTORY_DEFAULT_REORDER_POINT = 100
INVENTORY_DEFAULT_LEAD_TIME_DAYS = 7
