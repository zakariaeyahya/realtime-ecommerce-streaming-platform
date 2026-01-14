"""
Feature Extractor - Extract user and item features for recommendations.

Features include:
- User behavior features (recency, frequency, monetary)
- Item features (category, price range, popularity)
- Contextual features (time of day, session length)
- Interaction features (event type weights)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract features for recommendation engine."""

    def __init__(self):
        """Initialize feature extractor."""
        self.user_profiles: Dict[str, Dict] = {}
        self.item_profiles: Dict[str, Dict] = {}

        logger.info("FeatureExtractor initialized")

    def extract_user_features(
        self,
        user_id: str,
        events: List[Dict]
    ) -> Dict:
        """Extract user behavior features.

        Args:
            user_id: User identifier
            events: User's interaction events

        Returns:
            Dict of user features
        """
        if not events:
            return self._get_default_user_features(user_id)

        features = {
            'user_id': user_id,
            'total_interactions': len(events),
        }

        event_types = defaultdict(int)
        items_viewed = set()
        categories = set()
        total_amount = 0.0

        for event in events:
            event_type = event.get('event_type', 'view')
            event_types[event_type] += 1

            item_id = event.get('item_id')
            if item_id:
                items_viewed.add(item_id)

            category = event.get('category')
            if category:
                categories.add(category)

            if event_type == 'transaction':
                total_amount += float(event.get('price', 0))

        features['view_count'] = event_types.get('view', 0)
        features['cart_count'] = event_types.get('addtocart', 0)
        features['purchase_count'] = event_types.get('transaction', 0)
        features['search_count'] = event_types.get('search', 0)

        features['unique_items'] = len(items_viewed)
        features['unique_categories'] = len(categories)
        features['total_spent'] = round(total_amount, 2)

        if events:
            timestamps = [
                e.get('timestamp', 0) for e in events if e.get('timestamp')
            ]
            if timestamps:
                features['first_activity'] = min(timestamps)
                features['last_activity'] = max(timestamps)

        features['conversion_rate'] = self._calculate_conversion_rate(event_types)

        self.user_profiles[user_id] = features
        logger.debug(f"Extracted {len(features)} features for user {user_id}")

        return features

    def _calculate_conversion_rate(self, event_types: Dict[str, int]) -> float:
        """Calculate user conversion rate.

        Args:
            event_types: Count of each event type

        Returns:
            Conversion rate (0-1)
        """
        views = event_types.get('view', 0)
        purchases = event_types.get('transaction', 0)

        if views == 0:
            return 0.0

        return round(purchases / views, 4)

    def _get_default_user_features(self, user_id: str) -> Dict:
        """Get default features for new users.

        Args:
            user_id: User identifier

        Returns:
            Default feature dict
        """
        return {
            'user_id': user_id,
            'total_interactions': 0,
            'view_count': 0,
            'cart_count': 0,
            'purchase_count': 0,
            'search_count': 0,
            'unique_items': 0,
            'unique_categories': 0,
            'total_spent': 0.0,
            'conversion_rate': 0.0,
            'is_new_user': True,
        }

    def extract_item_features(
        self,
        item_id: str,
        interactions: List[Dict]
    ) -> Dict:
        """Extract item features from interactions.

        Args:
            item_id: Item identifier
            interactions: All interactions involving this item

        Returns:
            Dict of item features
        """
        if not interactions:
            return self._get_default_item_features(item_id)

        features = {
            'item_id': item_id,
            'total_interactions': len(interactions),
        }

        event_types = defaultdict(int)
        unique_users = set()
        prices = []

        for interaction in interactions:
            event_type = interaction.get('event_type', 'view')
            event_types[event_type] += 1

            user_id = interaction.get('user_id')
            if user_id:
                unique_users.add(user_id)

            price = interaction.get('price')
            if price:
                prices.append(float(price))

        features['view_count'] = event_types.get('view', 0)
        features['cart_count'] = event_types.get('addtocart', 0)
        features['purchase_count'] = event_types.get('transaction', 0)

        features['unique_users'] = len(unique_users)

        if prices:
            features['avg_price'] = round(sum(prices) / len(prices), 2)
            features['min_price'] = min(prices)
            features['max_price'] = max(prices)
        else:
            features['avg_price'] = 0.0
            features['min_price'] = 0.0
            features['max_price'] = 0.0

        features['popularity_score'] = self._calculate_popularity(event_types)

        self.item_profiles[item_id] = features
        logger.debug(f"Extracted {len(features)} features for item {item_id}")

        return features

    def _calculate_popularity(self, event_types: Dict[str, int]) -> float:
        """Calculate item popularity score.

        Args:
            event_types: Count of each event type

        Returns:
            Popularity score (0-1)
        """
        views = event_types.get('view', 0)
        carts = event_types.get('addtocart', 0)
        purchases = event_types.get('transaction', 0)

        score = views * 0.1 + carts * 0.3 + purchases * 0.6
        return min(1.0, score / 100)

    def _get_default_item_features(self, item_id: str) -> Dict:
        """Get default features for new items.

        Args:
            item_id: Item identifier

        Returns:
            Default feature dict
        """
        return {
            'item_id': item_id,
            'total_interactions': 0,
            'view_count': 0,
            'cart_count': 0,
            'purchase_count': 0,
            'unique_users': 0,
            'avg_price': 0.0,
            'popularity_score': 0.0,
            'is_new_item': True,
        }

    def extract_session_features(self, events: List[Dict]) -> Dict:
        """Extract session-level features.

        Args:
            events: Events from a single session

        Returns:
            Session feature dict
        """
        if not events:
            return {'session_length': 0, 'is_empty': True}

        features = {
            'session_length': len(events),
            'is_empty': False,
        }

        timestamps = [e.get('timestamp', 0) for e in events if e.get('timestamp')]
        if len(timestamps) >= 2:
            duration = max(timestamps) - min(timestamps)
            features['duration_seconds'] = duration
        else:
            features['duration_seconds'] = 0

        event_types = [e.get('event_type', 'view') for e in events]
        features['has_purchase'] = 'transaction' in event_types
        features['has_cart'] = 'addtocart' in event_types

        unique_items = set(e.get('item_id') for e in events if e.get('item_id'))
        features['unique_items_viewed'] = len(unique_items)

        return features

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get cached user profile.

        Args:
            user_id: User identifier

        Returns:
            User profile or None
        """
        return self.user_profiles.get(user_id)

    def get_item_profile(self, item_id: str) -> Optional[Dict]:
        """Get cached item profile.

        Args:
            item_id: Item identifier

        Returns:
            Item profile or None
        """
        return self.item_profiles.get(item_id)
