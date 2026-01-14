"""Tests for data loaders."""

import pytest
from pathlib import Path
from ingestion.loaders import RetailRocketLoader, InstacartLoader, OlistLoader


class TestRetailRocketLoader:
    """Test RetailRocketLoader."""

    def test_should_load_retail_rocket_events(self):
        """Test loading Retail Rocket CSV file."""
        # Test placeholder
        pass

    def test_should_parse_view_event(self):
        """Test parsing view event."""
        pass

    def test_should_parse_transaction_event(self):
        """Test parsing transaction event."""
        pass


class TestInstacartLoader:
    """Test InstacartLoader."""

    def test_should_load_instacart_orders(self):
        """Test loading Instacart orders."""
        pass


class TestOlistLoader:
    """Test OlistLoader."""

    def test_should_load_olist_orders(self):
        """Test loading Olist orders."""
        pass
