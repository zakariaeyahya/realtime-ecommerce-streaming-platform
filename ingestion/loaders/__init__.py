"""Loaders pour intégrer les sources de données réelles.

Ce module fournit des classes pour charger les données depuis:
- Retail Rocket: 2.7M événements e-commerce
- Instacart: 3M+ commandes et produits
- Olist: 99k commandes brésiliennes
"""

from .base_loader import BaseLoader
from .retail_rocket_loader import RetailRocketLoader
from .instacart_loader import InstacartLoader
from .olist_loader import OlistLoader

__all__ = [
    'BaseLoader',
    'RetailRocketLoader',
    'InstacartLoader',
    'OlistLoader',
]
