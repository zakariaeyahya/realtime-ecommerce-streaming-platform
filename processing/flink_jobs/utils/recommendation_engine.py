"""
Recommendation Engine - Collaborative filtering algorithms.

Implements:
- Item-based collaborative filtering
- Cosine similarity computation
- K-nearest neighbors for items
- Cold-start handling with popularity fallback
"""

import logging
import math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Collaborative filtering recommendation engine."""

    def __init__(self, k_neighbors: int = 50, min_common_users: int = 3):
        """Initialize recommendation engine.

        Args:
            k_neighbors: Number of neighbors for KNN
            min_common_users: Minimum common users for similarity
        """
        self.k_neighbors = k_neighbors
        self.min_common_users = min_common_users
        self.item_vectors: Dict[str, Dict[str, float]] = {}
        self.item_similarities: Dict[str, Dict[str, float]] = {}
        self.item_popularity: Dict[str, int] = defaultdict(int)

        logger.info(
            f"RecommendationEngine initialized (k={k_neighbors}, "
            f"min_common={min_common_users})"
        )

    def build_item_vectors(
        self,
        interactions: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """Build item vectors from user interactions.

        Args:
            interactions: List of user-item interactions

        Returns:
            Dict mapping item_id to user rating vectors
        """
        logger.info(f"Building item vectors from {len(interactions)} interactions")

        item_users: Dict[str, Dict[str, float]] = defaultdict(dict)

        for interaction in interactions:
            item_id = interaction.get('item_id')
            user_id = interaction.get('user_id')
            rating = self._get_implicit_rating(interaction)

            if item_id and user_id:
                if user_id not in item_users[item_id]:
                    item_users[item_id][user_id] = 0.0
                item_users[item_id][user_id] += rating
                self.item_popularity[item_id] += 1

        self.item_vectors = dict(item_users)
        logger.info(f"Built vectors for {len(self.item_vectors)} items")
        return self.item_vectors

    def _get_implicit_rating(self, interaction: Dict) -> float:
        """Convert interaction to implicit rating.

        Args:
            interaction: User-item interaction event

        Returns:
            Implicit rating value
        """
        event_type = interaction.get('event_type', 'view').lower()
        ratings = {
            'transaction': 5.0,
            'addtocart': 3.0,
            'view': 1.0,
            'search': 0.5,
        }
        return ratings.get(event_type, 1.0)

    def compute_similarities(self) -> Dict[str, Dict[str, float]]:
        """Compute item-item similarities using cosine similarity.

        Returns:
            Dict mapping item pairs to similarity scores
        """
        logger.info("Computing item similarities")

        items = list(self.item_vectors.keys())
        n_items = len(items)

        for i, item_a in enumerate(items):
            if i % 100 == 0:
                logger.debug(f"Processing item {i}/{n_items}")

            similarities = {}
            for item_b in items:
                if item_a == item_b:
                    continue

                sim = self._cosine_similarity(
                    self.item_vectors[item_a],
                    self.item_vectors[item_b]
                )

                if sim > 0:
                    similarities[item_b] = sim

            top_similar = sorted(
                similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )[:self.k_neighbors]

            self.item_similarities[item_a] = dict(top_similar)

        logger.info(f"Computed similarities for {len(self.item_similarities)} items")
        return self.item_similarities

    def _cosine_similarity(
        self,
        vec_a: Dict[str, float],
        vec_b: Dict[str, float]
    ) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec_a: First vector as user->rating dict
            vec_b: Second vector as user->rating dict

        Returns:
            Cosine similarity (0-1)
        """
        common_users = set(vec_a.keys()) & set(vec_b.keys())

        if len(common_users) < self.min_common_users:
            return 0.0

        dot_product = sum(vec_a[u] * vec_b[u] for u in common_users)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_similar_items(
        self,
        item_id: str,
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """Get most similar items for a given item.

        Args:
            item_id: Source item ID
            top_n: Number of similar items to return

        Returns:
            List of (item_id, similarity) tuples
        """
        if item_id not in self.item_similarities:
            logger.debug(f"No similarities found for item {item_id}")
            return []

        similarities = self.item_similarities[item_id]
        sorted_items = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_items[:top_n]

    def get_popular_items(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most popular items for cold-start fallback.

        Args:
            top_n: Number of items to return

        Returns:
            List of (item_id, count) tuples
        """
        sorted_items = sorted(
            self.item_popularity.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_items[:top_n]

    def recommend_for_user(
        self,
        user_history: List[str],
        top_n: int = 10
    ) -> List[Dict]:
        """Generate recommendations for a user based on history.

        Args:
            user_history: List of item IDs user interacted with
            top_n: Number of recommendations

        Returns:
            List of recommendation dicts
        """
        if not user_history:
            logger.debug("Empty user history, using popularity fallback")
            popular = self.get_popular_items(top_n)
            return [
                {'item_id': item_id, 'score': count / 1000, 'source': 'popular'}
                for item_id, count in popular
            ]

        scores: Dict[str, float] = defaultdict(float)
        history_set = set(user_history)

        for item_id in user_history:
            similar = self.get_similar_items(item_id, self.k_neighbors)
            for similar_item, similarity in similar:
                if similar_item not in history_set:
                    scores[similar_item] += similarity

        sorted_scores = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {'item_id': item_id, 'score': round(score, 4), 'source': 'cf'}
            for item_id, score in sorted_scores
        ]

    def save_model(self, path: str) -> bool:
        """Save model to disk.

        Args:
            path: Output path

        Returns:
            True if successful
        """
        try:
            import pickle
            from pathlib import Path

            model_data = {
                'item_vectors': self.item_vectors,
                'item_similarities': self.item_similarities,
                'item_popularity': dict(self.item_popularity),
                'k_neighbors': self.k_neighbors,
                'min_common_users': self.min_common_users,
            }

            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self, path: str) -> bool:
        """Load model from disk.

        Args:
            path: Model path

        Returns:
            True if successful
        """
        try:
            import pickle
            from pathlib import Path

            if not Path(path).exists():
                logger.warning(f"Model file not found: {path}")
                return False

            with open(path, 'rb') as f:
                model_data = pickle.load(f)

            self.item_vectors = model_data['item_vectors']
            self.item_similarities = model_data['item_similarities']
            self.item_popularity = defaultdict(int, model_data['item_popularity'])
            self.k_neighbors = model_data['k_neighbors']
            self.min_common_users = model_data['min_common_users']

            logger.info(f"Model loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
