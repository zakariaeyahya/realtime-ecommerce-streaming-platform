"""FastAPI application for the e-commerce streaming analytics API.

Exposes REST endpoints for fraud detection scores, product recommendations,
and inventory forecasting results cached in Redis.
"""

import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import List

import redis
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# Ajout du repertoire racine au path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))

from config.constants import (
    FRAUD_THRESHOLD,
    INVENTORY_ALERT_THRESHOLD,
    KAFKA_BROKERS,
    REDIS_DB,
    REDIS_HOST,
    REDIS_KEY_FRAUD,
    REDIS_KEY_INVENTORY,
    REDIS_KEY_RECO,
    REDIS_PORT,
)
from serving.api.models import (
    FraudResponse,
    HealthResponse,
    InventoryResponse,
    RecommendationItem,
    RecommendationResponse,
    ServiceStatus,
)
from serving.consumers.kafka_consumers import (
    FraudConsumer,
    InventoryConsumer,
    RecoConsumer,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "api_requests_total", "Total API requests", ["endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", "Request latency", ["endpoint"]
)

# Module-level state
_start_time: float = 0.0
_redis_client: redis.Redis = None  # type: ignore[assignment]
_consumers: List = []


def _create_redis_client() -> redis.Redis:
    """Create and return a Redis client."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", REDIS_HOST),
        port=int(os.getenv("REDIS_PORT", str(REDIS_PORT))),
        db=int(os.getenv("REDIS_DB", str(REDIS_DB))),
        decode_responses=True,
    )


def _start_consumers(redis_client: redis.Redis) -> List:
    """Start Kafka consumers in background threads."""
    consumers = [
        FraudConsumer(redis_client=redis_client),
        RecoConsumer(redis_client=redis_client),
        InventoryConsumer(redis_client=redis_client),
    ]
    for consumer in consumers:
        try:
            consumer.start()
        except Exception:
            logger.exception("Failed to start consumer %s", consumer.group_id)
    return consumers


def _stop_consumers(consumers: List) -> None:
    """Stop all Kafka consumers."""
    for consumer in consumers:
        try:
            consumer.stop()
        except Exception:
            logger.exception("Failed to stop consumer %s", consumer.group_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    global _start_time, _redis_client, _consumers
    _start_time = time.time()
    _redis_client = _create_redis_client()
    logger.info("Redis connected: %s:%s", REDIS_HOST, REDIS_PORT)
    _consumers = _start_consumers(_redis_client)
    logger.info("API started with %d consumers", len(_consumers))
    yield
    _stop_consumers(_consumers)
    logger.info("API shutdown complete")


app = FastAPI(
    title="E-Commerce Streaming Analytics API",
    description="REST API for fraud detection, recommendations, and inventory forecasting",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API, Redis, and Kafka connectivity."""
    redis_status = ServiceStatus(connected=False)
    kafka_status = ServiceStatus(connected=False)

    try:
        start = time.time()
        _redis_client.ping()
        redis_status = ServiceStatus(
            connected=True, latency_ms=round((time.time() - start) * 1000, 2)
        )
    except Exception:
        logger.warning("Redis health check failed")

    try:
        from confluent_kafka import Producer

        brokers = os.getenv("KAFKA_BROKERS", KAFKA_BROKERS)
        start = time.time()
        p = Producer({"bootstrap.servers": brokers})
        p.list_topics(timeout=3)
        kafka_status = ServiceStatus(
            connected=True, latency_ms=round((time.time() - start) * 1000, 2)
        )
    except Exception:
        logger.warning("Kafka health check failed")

    overall = "healthy" if redis_status.connected else "degraded"
    uptime = round(time.time() - _start_time, 2)

    return HealthResponse(
        status=overall, redis=redis_status, kafka=kafka_status, uptime=uptime
    )


@app.get("/fraud/{user_id}", response_model=FraudResponse)
async def get_fraud_score(user_id: str) -> FraudResponse:
    """Get fraud detection score for a user."""
    with REQUEST_LATENCY.labels(endpoint="fraud").time():
        key = f"{REDIS_KEY_FRAUD}:{user_id}"
        raw = _redis_client.get(key)

        if raw is None:
            REQUEST_COUNT.labels(endpoint="fraud", status="404").inc()
            raise HTTPException(
                status_code=404,
                detail=f"No fraud data found for user {user_id}",
            )

        data = json.loads(raw)
        fraud_score = float(data.get("fraud_score", 0.0))
        threshold = float(os.getenv("FRAUD_THRESHOLD", str(FRAUD_THRESHOLD)))
        is_fraud = fraud_score >= threshold
        alert = f"ALERT: High fraud risk ({fraud_score:.2f})" if is_fraud else None

        REQUEST_COUNT.labels(endpoint="fraud", status="200").inc()
        return FraudResponse(
            user_id=user_id,
            fraud_score=fraud_score,
            is_fraud=is_fraud,
            amount=data.get("amount"),
            alert=alert,
            timestamp=data.get("timestamp"),
        )


@app.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(user_id: str) -> RecommendationResponse:
    """Get product recommendations for a user."""
    with REQUEST_LATENCY.labels(endpoint="recommendations").time():
        key = f"{REDIS_KEY_RECO}:{user_id}"
        raw = _redis_client.get(key)

        if raw is None:
            REQUEST_COUNT.labels(endpoint="recommendations", status="404").inc()
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for user {user_id}",
            )

        data = json.loads(raw)
        raw_items = data.get("recommendations", [])
        items = [
            RecommendationItem(
                item_id=str(r.get("item_id", r.get("product_id", ""))),
                score=float(r.get("score", 0.0)),
                category=r.get("category"),
            )
            for r in raw_items
        ]

        REQUEST_COUNT.labels(endpoint="recommendations", status="200").inc()
        return RecommendationResponse(
            user_id=user_id,
            recommendations=items,
            count=len(items),
            timestamp=data.get("timestamp"),
        )


@app.get("/inventory/{product_id}", response_model=InventoryResponse)
async def get_inventory(product_id: str) -> InventoryResponse:
    """Get inventory forecast for a product."""
    with REQUEST_LATENCY.labels(endpoint="inventory").time():
        key = f"{REDIS_KEY_INVENTORY}:{product_id}"
        raw = _redis_client.get(key)

        if raw is None:
            REQUEST_COUNT.labels(endpoint="inventory", status="404").inc()
            raise HTTPException(
                status_code=404,
                detail=f"No inventory data found for product {product_id}",
            )

        data = json.loads(raw)
        current_qty = int(data.get("current_quantity", 0))
        threshold = int(
            os.getenv("INVENTORY_ALERT_THRESHOLD", str(INVENTORY_ALERT_THRESHOLD))
        )
        needs_reorder = current_qty < threshold
        alert = (
            f"REORDER: Stock below threshold ({current_qty} < {threshold})"
            if needs_reorder
            else None
        )

        REQUEST_COUNT.labels(endpoint="inventory", status="200").inc()
        return InventoryResponse(
            product_id=product_id,
            current_quantity=current_qty,
            forecast_7days=data.get("forecast_7days"),
            needs_reorder=needs_reorder,
            alert=alert,
            timestamp=data.get("timestamp"),
        )


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(), media_type="text/plain; charset=utf-8"
    )
