"""Pydantic models for API responses.

Defines the response schemas for fraud detection, recommendations,
inventory forecasting, and health check endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class FraudResponse(BaseModel):
    """Response model for fraud detection endpoint."""

    user_id: str
    fraud_score: float = Field(ge=0.0, le=1.0)
    is_fraud: bool
    amount: Optional[float] = None
    alert: Optional[str] = None
    timestamp: Optional[str] = None


class RecommendationItem(BaseModel):
    """Single recommended item."""

    item_id: str
    score: float = Field(ge=0.0, le=1.0)
    category: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for recommendations endpoint."""

    user_id: str
    recommendations: List[RecommendationItem]
    count: int
    timestamp: Optional[str] = None


class InventoryResponse(BaseModel):
    """Response model for inventory forecasting endpoint."""

    product_id: str
    current_quantity: int
    forecast_7days: Optional[List[int]] = None
    needs_reorder: bool
    alert: Optional[str] = None
    timestamp: Optional[str] = None


class ServiceStatus(BaseModel):
    """Status of an individual service."""

    connected: bool
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    redis: ServiceStatus
    kafka: ServiceStatus
    uptime: float
