"""Base loader abstract class."""

import logging
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Optional

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    """Abstract base class for all data loaders."""

    def __init__(self, source_path: str):
        """Initialize loader.

        Args:
            source_path: Path to data source (CSV, database, etc.)
        """
        self.source_path = source_path
        self.events_count = 0
        self.errors_count = 0
        logger.info(f"Loader initialized: {self.__class__.__name__} from {source_path}")

    @abstractmethod
    def load(self, max_rows: Optional[int] = None) -> Iterator[Dict]:
        """Load and parse events from source.

        Args:
            max_rows: Maximum number of rows to load (None = all)

        Yields:
            Standardized event dictionaries
        """
        pass

    @abstractmethod
    def parse_event(self, row: Dict) -> Optional[Dict]:
        """Parse a single row into standard event format.

        Args:
            row: Raw data row

        Returns:
            Standardized event or None if invalid
        """
        pass

    def get_stats(self) -> Dict:
        """Get loader statistics.

        Returns:
            Dict with events_count and errors_count
        """
        return {
            'events_count': self.events_count,
            'errors_count': self.errors_count,
            'total': self.events_count + self.errors_count,
        }
