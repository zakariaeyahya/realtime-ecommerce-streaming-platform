"""Unit tests for Recommendation Engine."""

import pytest
import math
from unittest.mock import Mock


class TestRecommendationEngine:
    """Test collaborative filtering engine."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        from processing.flink_jobs.utils.recommendation_engine import RecommendationEngine
        return RecommendationEngine(k_neighbors=10)

    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine.k_neighbors == 10
        assert engine.min_common_users == 3

    def test_build_item_vectors(self, engine):
        """Test building item vectors from interactions."""
        interactions = [
            {'user_id': 'u1', 'item_id': 'i1', 'event_type': 'view'},
            {'user_id': 'u2', 'item_id': 'i1', 'event_type': 'purchase'},
            {'user_id': 'u1', 'item_id': 'i2', 'event_type': 'addtocart'},
        ]
        vectors = engine.build_item_vectors(interactions)
        assert 'i1' in vectors
        assert 'i2' in vectors

    def test_cosine_similarity_computation(self, engine):
        """Test cosine similarity calculation."""
        vec_a = {'u1': 1.0, 'u2': 0.5}
        vec_b = {'u1': 1.0, 'u2': 0.5}
        sim = engine._cosine_similarity(vec_a, vec_b)
        assert 0 <= sim <= 1

    def test_recommend_for_user(self, engine):
        """Test generating recommendations."""
        interactions = [
            {'user_id': 'u1', 'item_id': 'i1', 'event_type': 'view'},
            {'user_id': 'u1', 'item_id': 'i2', 'event_type': 'view'},
            {'user_id': 'u2', 'item_id': 'i1', 'event_type': 'purchase'},
            {'user_id': 'u2', 'item_id': 'i3', 'event_type': 'view'},
        ]
        engine.build_item_vectors(interactions)
        engine.compute_similarities()

        recommendations = engine.recommend_for_user(['i1', 'i2'])
        assert isinstance(recommendations, list)

    def test_get_popular_items(self, engine):
        """Test getting popular items for cold-start."""
        interactions = [
            {'user_id': 'u1', 'item_id': 'i1', 'event_type': 'purchase'},
            {'user_id': 'u2', 'item_id': 'i1', 'event_type': 'purchase'},
            {'user_id': 'u3', 'item_id': 'i2', 'event_type': 'view'},
        ]
        engine.build_item_vectors(interactions)
        popular = engine.get_popular_items(5)
        assert len(popular) > 0
