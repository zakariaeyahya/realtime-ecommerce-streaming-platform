"""Unit tests for the FastAPI serving layer.

Tests all API endpoints with mocked Redis and Kafka dependencies.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ajout du repertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_redis():
    """Create a mock Redis client with get/ping/setex methods."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    return mock


@pytest.fixture
def client(mock_redis):
    """Create a FastAPI test client with mocked dependencies."""
    with patch("serving.api.main._create_redis_client", return_value=mock_redis), \
         patch("serving.api.main._start_consumers", return_value=[]), \
         patch("serving.api.main._stop_consumers"):
        from serving.api.main import app

        from fastapi.testclient import TestClient
        with TestClient(app) as test_client:
            # Inject mock redis into module state
            import serving.api.main as main_module
            main_module._redis_client = mock_redis
            yield test_client


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_redis_up(self, client, mock_redis):
        """Health returns healthy when Redis is connected."""
        mock_redis.ping.return_value = True
        with patch("confluent_kafka.Producer") as mock_producer_cls:
            mock_prod = MagicMock()
            mock_producer_cls.return_value = mock_prod
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis"]["connected"] is True
        assert "uptime" in data

    def test_health_redis_down(self, client, mock_redis):
        """Health returns degraded when Redis is down."""
        mock_redis.ping.side_effect = ConnectionError("Redis down")
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["redis"]["connected"] is False


class TestFraudEndpoint:
    """Tests for GET /fraud/{user_id}."""

    def test_fraud_score_found(self, client, mock_redis):
        """Returns fraud score when data exists in Redis."""
        fraud_data = {
            "user_id": "user_1002",
            "fraud_score": 0.92,
            "amount": 1500.0,
            "timestamp": "2024-01-15T10:30:00",
        }
        mock_redis.get.return_value = json.dumps(fraud_data)

        response = client.get("/fraud/user_1002")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_1002"
        assert data["fraud_score"] == 0.92
        assert data["is_fraud"] is True
        assert data["alert"] is not None
        assert "ALERT" in data["alert"]

    def test_fraud_score_low(self, client, mock_redis):
        """Low fraud score returns is_fraud=False."""
        fraud_data = {
            "user_id": "user_1001",
            "fraud_score": 0.15,
            "amount": 50.0,
            "timestamp": "2024-01-15T10:30:00",
        }
        mock_redis.get.return_value = json.dumps(fraud_data)

        response = client.get("/fraud/user_1001")

        assert response.status_code == 200
        data = response.json()
        assert data["is_fraud"] is False
        assert data["alert"] is None

    def test_fraud_not_found(self, client, mock_redis):
        """Returns 404 when no fraud data in cache."""
        mock_redis.get.return_value = None

        response = client.get("/fraud/unknown_user")

        assert response.status_code == 404
        assert "No fraud data found" in response.json()["detail"]


class TestRecommendationsEndpoint:
    """Tests for GET /recommendations/{user_id}."""

    def test_recommendations_found(self, client, mock_redis):
        """Returns recommendations when data exists."""
        reco_data = {
            "user_id": "user_1001",
            "recommendations": [
                {"item_id": "item_100", "score": 0.95, "category": "Electronics"},
                {"item_id": "item_200", "score": 0.87, "category": "Books"},
            ],
            "timestamp": "2024-01-15T10:30:00",
        }
        mock_redis.get.return_value = json.dumps(reco_data)

        response = client.get("/recommendations/user_1001")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_1001"
        assert data["count"] == 2
        assert len(data["recommendations"]) == 2
        assert data["recommendations"][0]["item_id"] == "item_100"

    def test_recommendations_empty(self, client, mock_redis):
        """Returns empty list when user has no recommendations."""
        reco_data = {
            "user_id": "user_1001",
            "recommendations": [],
            "timestamp": "2024-01-15T10:30:00",
        }
        mock_redis.get.return_value = json.dumps(reco_data)

        response = client.get("/recommendations/user_1001")

        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_recommendations_not_found(self, client, mock_redis):
        """Returns 404 when no recommendations in cache."""
        mock_redis.get.return_value = None

        response = client.get("/recommendations/unknown_user")

        assert response.status_code == 404


class TestInventoryEndpoint:
    """Tests for GET /inventory/{product_id}."""

    def test_inventory_found(self, client, mock_redis):
        """Returns inventory data when available."""
        inv_data = {
            "product_id": "SKU0001",
            "current_quantity": 250,
            "forecast_7days": [240, 230, 220, 210, 200, 190, 180],
            "timestamp": "2024-01-15T10:30:00",
        }
        mock_redis.get.return_value = json.dumps(inv_data)

        response = client.get("/inventory/SKU0001")

        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "SKU0001"
        assert data["current_quantity"] == 250
        assert data["needs_reorder"] is False
        assert data["alert"] is None

    def test_inventory_low_stock(self, client, mock_redis):
        """Returns reorder alert when stock is low."""
        inv_data = {
            "product_id": "SKU0002",
            "current_quantity": 50,
            "forecast_7days": [45, 40, 35, 30, 25, 20, 15],
            "timestamp": "2024-01-15T10:30:00",
        }
        mock_redis.get.return_value = json.dumps(inv_data)

        response = client.get("/inventory/SKU0002")

        assert response.status_code == 200
        data = response.json()
        assert data["needs_reorder"] is True
        assert data["alert"] is not None
        assert "REORDER" in data["alert"]

    def test_inventory_not_found(self, client, mock_redis):
        """Returns 404 when no inventory data in cache."""
        mock_redis.get.return_value = None

        response = client.get("/inventory/unknown_sku")

        assert response.status_code == 404


class TestMetricsEndpoint:
    """Tests for GET /metrics."""

    def test_metrics_returns_prometheus_format(self, client):
        """Metrics endpoint returns Prometheus text format."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
