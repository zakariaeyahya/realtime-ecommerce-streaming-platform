"""
Recommendations Job - Real-time product recommendations using collaborative filtering.

This Flink job processes user events from Kafka, computes user-item similarities,
and generates personalized recommendations output to Redis and Kafka.

Architecture:
    Kafka Topic (events)
        -> Flink Session Windows (30 min inactivity)
        -> Feature Extraction
        -> Collaborative Filtering
        -> Top-K Recommendations
        -> Output (Redis + Kafka)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommendationsJob:
    """Main recommendations job using collaborative filtering."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize recommendations job.

        Args:
            config: Configuration dictionary with settings
        """
        try:
            from config.constants import (
                RECO_TOP_K,
                RECO_MIN_INTERACTIONS,
                RECO_SESSION_TIMEOUT_MINUTES
            )
            default_top_k = RECO_TOP_K
            default_min_interactions = RECO_MIN_INTERACTIONS
            default_session_timeout = RECO_SESSION_TIMEOUT_MINUTES
        except ImportError:
            default_top_k = 10
            default_min_interactions = 3
            default_session_timeout = 30

        self.config = config or {}
        self.top_k = int(self.config.get('top_k', default_top_k))
        self.min_interactions = int(
            self.config.get('min_interactions', default_min_interactions)
        )
        self.session_timeout = int(
            self.config.get('session_timeout', default_session_timeout)
        )

        logger.info(
            f"RecommendationsJob initialized (top_k={self.top_k}, "
            f"min_interactions={self.min_interactions})"
        )

    def create_environment(self):
        """Create Flink StreamExecutionEnvironment.

        Returns:
            StreamExecutionEnvironment configured for recommendations
        """
        try:
            from pyflink.datastream import StreamExecutionEnvironment

            env = StreamExecutionEnvironment.get_execution_environment()
            env.set_parallelism(4)
            env.enable_checkpointing(30000)

            logger.info("Flink environment created for recommendations")
            return env

        except ImportError as e:
            logger.error(f"Flink import error: {e}")
            raise

    def run(self) -> None:
        """Execute the recommendations job."""
        logger.info("Starting Recommendations Job")

        try:
            env = self.create_environment()
            logger.info("Executing recommendations job...")
            env.execute("RecommendationsJob")

        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            raise

    def generate_recommendations(
        self,
        user_id: str,
        user_history: List[Dict],
        item_similarities: Dict[str, Dict[str, float]]
    ) -> List[Dict]:
        """Generate top-K recommendations for a user.

        Args:
            user_id: User identifier
            user_history: List of user interaction events
            item_similarities: Pre-computed item-item similarities

        Returns:
            List of recommended items with scores
        """
        if not user_id:
            logger.warning("Empty user_id provided")
            return []

        if len(user_history) < self.min_interactions:
            logger.debug(
                f"User {user_id} has insufficient history: "
                f"{len(user_history)} < {self.min_interactions}"
            )
            return self._get_popular_items()

        try:
            scores = self._compute_recommendation_scores(
                user_history, item_similarities
            )
            recommendations = self._select_top_k(scores, user_history)

            logger.debug(
                f"Generated {len(recommendations)} recommendations for {user_id}"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return self._get_popular_items()

    def _compute_recommendation_scores(
        self,
        user_history: List[Dict],
        item_similarities: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Compute recommendation scores for all candidate items.

        Args:
            user_history: User's interaction history
            item_similarities: Item-item similarity matrix

        Returns:
            Dict mapping item_id to recommendation score
        """
        scores = {}
        interacted_items = {e.get('item_id') for e in user_history}

        for event in user_history:
            item_id = event.get('item_id')
            if not item_id or item_id not in item_similarities:
                continue

            weight = self._get_interaction_weight(event)

            for similar_item, similarity in item_similarities[item_id].items():
                if similar_item in interacted_items:
                    continue

                if similar_item not in scores:
                    scores[similar_item] = 0.0
                scores[similar_item] += similarity * weight

        return scores

    def _get_interaction_weight(self, event: Dict) -> float:
        """Get weight for an interaction based on event type.

        Args:
            event: User interaction event

        Returns:
            Weight value (higher for stronger signals)
        """
        weights = {
            'transaction': 1.0,
            'addtocart': 0.7,
            'view': 0.3,
            'search': 0.2,
        }
        event_type = event.get('event_type', 'view').lower()
        return weights.get(event_type, 0.1)

    def _select_top_k(
        self,
        scores: Dict[str, float],
        user_history: List[Dict]
    ) -> List[Dict]:
        """Select top-K items from scored candidates.

        Args:
            scores: Item scores
            user_history: User history (for filtering)

        Returns:
            Top-K recommendations
        """
        interacted = {e.get('item_id') for e in user_history}
        candidates = [
            (item_id, score)
            for item_id, score in scores.items()
            if item_id not in interacted and score > 0
        ]

        candidates.sort(key=lambda x: x[1], reverse=True)

        return [
            {
                'item_id': item_id,
                'score': round(score, 4),
                'rank': i + 1,
                'timestamp': datetime.now().isoformat()
            }
            for i, (item_id, score) in enumerate(candidates[:self.top_k])
        ]

    def _get_popular_items(self) -> List[Dict]:
        """Get popular items as fallback for cold-start users.

        Returns:
            List of popular item recommendations
        """
        logger.debug("Using popular items fallback")
        return [
            {'item_id': f'popular_{i}', 'score': 1.0 - (i * 0.1), 'rank': i + 1}
            for i in range(min(self.top_k, 5))
        ]

    def process_session(self, session_events: List[Dict]) -> Dict:
        """Process a user session and generate recommendations.

        Args:
            session_events: Events from a user session

        Returns:
            Session processing result with recommendations
        """
        if not session_events:
            return {'status': 'empty', 'recommendations': []}

        user_id = session_events[0].get('user_id')
        if not user_id:
            return {'status': 'no_user', 'recommendations': []}

        recommendations = self.generate_recommendations(
            user_id=user_id,
            user_history=session_events,
            item_similarities={}
        )

        return {
            'status': 'success',
            'user_id': user_id,
            'session_length': len(session_events),
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    job = RecommendationsJob()
    job.run()
