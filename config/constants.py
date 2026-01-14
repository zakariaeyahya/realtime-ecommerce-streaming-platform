# This is a placeholder for config/constants.py update instructions
# Add the following to config/constants.py:

"""
# ============================================================================
# INVENTORY FORECASTING (Sprint 5)
# ============================================================================

INVENTORY_ALERT_THRESHOLD = 100
INVENTORY_FORECAST_DAYS = 7
INVENTORY_MODEL_PATH = 'processing/models/inventory_forecast_models.joblib'
INVENTORY_WINDOW_SIZE_SECONDS = 86400  # 24 hours
INVENTORY_FEATURE_COUNT = 50

PROPHET_SEASONALITY_MODE = 'multiplicative'
ARIMA_P, ARIMA_D, ARIMA_Q = 5, 1, 2
ENSEMBLE_PROPHET_WEIGHT = 0.6
ENSEMBLE_ARIMA_WEIGHT = 0.4

INVENTORY_FORECAST_ACCURACY_TARGET = 0.85
INVENTORY_MAX_LATENCY_MS = 2000

REDIS_INVENTORY_TTL_SECONDS = 604800  # 7 days
INVENTORY_DEFAULT_REORDER_POINT = 100
INVENTORY_DEFAULT_LEAD_TIME_DAYS = 7

KAFKA_INVENTORY_INPUT_TOPIC = 'inventory-changes'
KAFKA_INVENTORY_FORECAST_TOPIC = 'inventory-forecasts'
"""
