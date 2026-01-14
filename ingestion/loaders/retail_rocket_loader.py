"""Retail Rocket dataset loader."""

import csv
import logging
from pathlib import Path
from typing import Iterator, Dict, Optional

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class RetailRocketLoader(BaseLoader):
    """Load and parse Retail Rocket dataset from CSV.

    Dataset format:
    - VisitorID: User identifier
    - ItemID: Product identifier
    - Event: view|addtocart|transaction
    - Timestamp: Unix timestamp (seconds)
    - TransactionID: Transaction ID (for event=transaction)
    - Price: Optional price
    - Quantity: Optional quantity
    """

    def load(self, max_rows: Optional[int] = None) -> Iterator[Dict]:
        """Load events from CSV file.

        Args:
            max_rows: Maximum rows to load

        Yields:
            Standardized event dictionaries
        """
        csv_path = Path(self.source_path)

        if not csv_path.exists():
            logger.error(f"File not found: {csv_path}")
            return

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for i, row in enumerate(reader):
                    if max_rows and i >= max_rows:
                        break

                    event = self.parse_event(row)
                    if event:
                        self.events_count += 1
                        yield event
                    else:
                        self.errors_count += 1

                    if (i + 1) % 10000 == 0:
                        logger.info(f"Processed {i + 1} rows...")

            logger.info(f"Finished loading: {self.events_count} events, {self.errors_count} errors")

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            self.errors_count += 1

    def parse_event(self, row: Dict) -> Optional[Dict]:
        """Convert CSV row to standard event format.

        Args:
            row: CSV row dictionary

        Returns:
            Standardized event or None if invalid
        """
        try:
            # Handle lowercase and uppercase column names
            event_type = (row.get('Event') or row.get('event') or '').lower()
            timestamp = row.get('Timestamp') or row.get('timestamp') or 0
            visitor_id = row.get('VisitorID') or row.get('visitorid') or ''
            item_id = row.get('ItemID') or row.get('itemid') or ''
            transaction_id = row.get('TransactionID') or row.get('transactionid') or ''
            price = row.get('Price') or row.get('price')
            quantity = row.get('Quantity') or row.get('quantity')

            if event_type not in ['view', 'addtocart', 'transaction']:
                return None

            if not timestamp or not visitor_id or not item_id:
                return None

            event = {
                'event_id': f"rr-{timestamp}-{visitor_id}",
                'event_type': event_type,
                'timestamp': int(timestamp) * 1000,  # Convert to milliseconds
                'user_id': str(visitor_id),
                'item_id': str(item_id),
            }

            if event_type == 'transaction' and transaction_id:
                event['transaction_id'] = str(transaction_id)

            if price:
                try:
                    event['price'] = float(price)
                except ValueError:
                    pass

            if quantity:
                try:
                    event['quantity'] = int(quantity)
                except ValueError:
                    pass

            return event

        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None
