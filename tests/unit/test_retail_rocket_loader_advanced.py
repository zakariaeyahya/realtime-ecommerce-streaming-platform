"""Tests unitaires avances pour RetailRocketLoader.

Couvre: load(), parse_event() avec differents cas.
"""
import logging
import sys
import tempfile
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from ingestion.loaders.retail_rocket_loader import RetailRocketLoader

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_csv(tmp_path):
    """Cree un CSV temporaire Retail Rocket."""
    csv_content = (
        "Timestamp,VisitorID,Event,ItemID,TransactionID,Price,Quantity\n"
        "1433221200,1234,view,100,,, \n"
        "1433221300,1234,addtocart,100,,, \n"
        "1433221400,1234,transaction,100,TX001,29.99,2\n"
        "1433221500,5678,view,200,,, \n"
        "1433221600,5678,view,300,,, \n"
    )
    csv_file = tmp_path / "events.csv"
    csv_file.write_text(csv_content, encoding='utf-8')
    return str(csv_file)


@pytest.fixture
def loader(sample_csv):
    """Cree un loader avec le CSV temporaire."""
    return RetailRocketLoader(source_path=sample_csv)


class TestRetailRocketLoaderLoad:
    """Tests pour la methode load."""

    def test_load_all_events(self, loader):
        """Test chargement de tous les evenements."""
        events = list(loader.load())
        assert len(events) == 5

    def test_load_with_max_rows(self, loader):
        """Test chargement avec limite."""
        events = list(loader.load(max_rows=2))
        assert len(events) == 2

    def test_events_count_tracked(self, loader):
        """Test compteur d'evenements."""
        list(loader.load())
        assert loader.events_count == 5
        assert loader.errors_count == 0

    def test_load_nonexistent_file(self):
        """Test fichier inexistant."""
        loader = RetailRocketLoader(source_path="/fake/path.csv")
        events = list(loader.load())
        assert len(events) == 0

    def test_get_stats(self, loader):
        """Test statistiques du loader."""
        list(loader.load())
        stats = loader.get_stats()
        assert stats['events_count'] == 5
        assert stats['errors_count'] == 0
        assert stats['total'] == 5


class TestRetailRocketParseEvent:
    """Tests pour parse_event."""

    def test_parse_view_event(self, loader):
        """Test parsing d'un evenement view."""
        row = {
            'Timestamp': '1433221200',
            'VisitorID': '1234',
            'Event': 'view',
            'ItemID': '100',
        }
        event = loader.parse_event(row)
        assert event is not None
        assert event['event_type'] == 'view'
        assert event['user_id'] == '1234'
        assert event['item_id'] == '100'
        assert event['timestamp'] == 1433221200000

    def test_parse_transaction_with_price(self, loader):
        """Test parsing transaction avec prix et quantite."""
        row = {
            'Timestamp': '1433221400',
            'VisitorID': '1234',
            'Event': 'transaction',
            'ItemID': '100',
            'TransactionID': 'TX001',
            'Price': '29.99',
            'Quantity': '2',
        }
        event = loader.parse_event(row)
        assert event is not None
        assert event['event_type'] == 'transaction'
        assert event['price'] == 29.99
        assert event['quantity'] == 2
        assert event['transaction_id'] == 'TX001'

    def test_parse_addtocart_event(self, loader):
        """Test parsing d'un evenement addtocart."""
        row = {
            'Timestamp': '1433221300',
            'VisitorID': '1234',
            'Event': 'addtocart',
            'ItemID': '100',
        }
        event = loader.parse_event(row)
        assert event is not None
        assert event['event_type'] == 'addtocart'

    def test_parse_invalid_event_type(self, loader):
        """Test parsing d'un type invalide retourne None."""
        row = {
            'Timestamp': '1433221200',
            'VisitorID': '1234',
            'Event': 'invalid',
            'ItemID': '100',
        }
        event = loader.parse_event(row)
        assert event is None

    def test_parse_missing_timestamp(self, loader):
        """Test parsing sans timestamp retourne None."""
        row = {'VisitorID': '1234', 'Event': 'view', 'ItemID': '100'}
        event = loader.parse_event(row)
        assert event is None

    def test_parse_lowercase_columns(self, loader):
        """Test parsing avec colonnes en minuscules."""
        row = {
            'timestamp': '1433221200',
            'visitorid': '1234',
            'event': 'view',
            'itemid': '100',
        }
        event = loader.parse_event(row)
        assert event is not None
        assert event['event_type'] == 'view'

    def test_parse_invalid_price(self, loader):
        """Test parsing avec prix invalide."""
        row = {
            'Timestamp': '1433221400',
            'VisitorID': '1234',
            'Event': 'transaction',
            'ItemID': '100',
            'Price': 'not_a_price',
            'Quantity': '2',
        }
        event = loader.parse_event(row)
        assert event is not None
        assert 'price' not in event

    def test_parse_invalid_quantity(self, loader):
        """Test parsing avec quantite invalide."""
        row = {
            'Timestamp': '1433221400',
            'VisitorID': '1234',
            'Event': 'transaction',
            'ItemID': '100',
            'Quantity': 'abc',
        }
        event = loader.parse_event(row)
        assert event is not None
        assert 'quantity' not in event

    def test_event_id_format(self, loader):
        """Test format de l'event_id genere."""
        row = {
            'Timestamp': '1433221200',
            'VisitorID': '1234',
            'Event': 'view',
            'ItemID': '100',
        }
        event = loader.parse_event(row)
        assert event['event_id'] == 'rr-1433221200-1234'
