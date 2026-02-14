"""Tests unitaires pour les validateurs de schemas.

Couvre: load_avro_schema, validate_event, validate_inventory_change,
get_schema_fields, get_required_fields.
"""
import logging
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from ingestion.schemas import (
    load_avro_schema,
    get_event_schema,
    get_inventory_schema,
    validate_event,
    validate_inventory_change,
    get_schema_fields,
    get_required_fields,
)

logger = logging.getLogger(__name__)


class TestLoadAvroSchema:
    """Tests pour le chargement des schemas Avro."""

    def test_load_event_schema(self):
        """Test chargement du schema event."""
        schema = load_avro_schema("event_schema")
        assert isinstance(schema, dict)
        assert "fields" in schema

    def test_load_inventory_schema(self):
        """Test chargement du schema inventory."""
        schema = load_avro_schema("inventory_schema")
        assert isinstance(schema, dict)
        assert "fields" in schema

    def test_load_nonexistent_schema_raises(self):
        """Test erreur si schema inexistant."""
        with pytest.raises(FileNotFoundError):
            load_avro_schema("nonexistent_schema")

    def test_get_event_schema(self):
        """Test raccourci get_event_schema."""
        schema = get_event_schema()
        assert isinstance(schema, dict)

    def test_get_inventory_schema(self):
        """Test raccourci get_inventory_schema."""
        schema = get_inventory_schema()
        assert isinstance(schema, dict)


class TestValidateEvent:
    """Tests pour la validation des evenements."""

    def test_valid_view_event(self):
        """Test evenement view valide."""
        event = {
            'event_id': 'e1',
            'event_type': 'view',
            'timestamp': 1704067200000,
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
        }
        is_valid, errors = validate_event(event)
        assert is_valid is True
        assert errors == []

    def test_valid_transaction_event(self):
        """Test evenement transaction valide."""
        event = {
            'event_id': 'e2',
            'event_type': 'transaction',
            'timestamp': 1704067200000,
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
            'price': 99.99,
            'quantity': 2,
        }
        is_valid, errors = validate_event(event)
        assert is_valid is True

    def test_missing_required_field(self):
        """Test champs obligatoires manquants."""
        event = {'event_type': 'view', 'timestamp': 123}
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("event_id" in e or "user_id" in e for e in errors)

    def test_invalid_event_type(self):
        """Test type d'evenement invalide."""
        event = {
            'event_id': 'e1',
            'event_type': 'invalid_type',
            'timestamp': 123,
            'user_id': 'u1',
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("Invalid event_type" in e for e in errors)

    def test_non_numeric_timestamp(self):
        """Test timestamp non numerique."""
        event = {
            'event_id': 'e1',
            'event_type': 'view',
            'timestamp': 'not_a_number',
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("timestamp" in e for e in errors)

    def test_negative_price(self):
        """Test prix negatif."""
        event = {
            'event_id': 'e1',
            'event_type': 'transaction',
            'timestamp': 123,
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
            'price': -10.0,
            'quantity': 1,
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("price" in e for e in errors)

    def test_negative_quantity(self):
        """Test quantite negative."""
        event = {
            'event_id': 'e1',
            'event_type': 'transaction',
            'timestamp': 123,
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
            'price': 10.0,
            'quantity': -1,
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("quantity" in e for e in errors)

    def test_invalid_rating(self):
        """Test rating hors limites."""
        event = {
            'event_id': 'e1',
            'event_type': 'review',
            'timestamp': 123,
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
            'rating': 10,
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("rating" in e for e in errors)

    def test_invalid_device_type(self):
        """Test device_type invalide."""
        event = {
            'event_id': 'e1',
            'event_type': 'view',
            'timestamp': 123,
            'user_id': 'u1',
            'item_id': 'i1',
            'category': 'Electronics',
            'device_type': 'smartwatch',
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False
        assert any("device_type" in e for e in errors)

    def test_none_field_treated_as_missing(self):
        """Test champ None traite comme manquant."""
        event = {
            'event_id': None,
            'event_type': 'view',
            'timestamp': 123,
            'user_id': 'u1',
        }
        is_valid, errors = validate_event(event)
        assert is_valid is False


class TestValidateInventoryChange:
    """Tests pour la validation des changements d'inventaire."""

    def test_valid_inventory_change(self):
        """Test changement valide."""
        change = {
            'change_id': 'c1',
            'timestamp': 123,
            'item_id': 'i1',
            'change_type': 'stock_in',
            'quantity_before': 100,
            'quantity_change': 50,
            'quantity_after': 150,
        }
        is_valid, errors = validate_inventory_change(change)
        assert is_valid is True
        assert errors == []

    def test_missing_required_field(self):
        """Test champs obligatoires manquants."""
        change = {'change_id': 'c1', 'timestamp': 123}
        is_valid, errors = validate_inventory_change(change)
        assert is_valid is False

    def test_invalid_change_type(self):
        """Test type de changement invalide."""
        change = {
            'change_id': 'c1',
            'timestamp': 123,
            'item_id': 'i1',
            'change_type': 'invalid',
            'quantity_before': 100,
            'quantity_change': 50,
            'quantity_after': 150,
        }
        is_valid, errors = validate_inventory_change(change)
        assert is_valid is False
        assert any("change_type" in e for e in errors)

    def test_quantity_mismatch(self):
        """Test incoherence before + change != after."""
        change = {
            'change_id': 'c1',
            'timestamp': 123,
            'item_id': 'i1',
            'change_type': 'stock_in',
            'quantity_before': 100,
            'quantity_change': 50,
            'quantity_after': 999,
        }
        is_valid, errors = validate_inventory_change(change)
        assert is_valid is False
        assert any("quantity_after" in e for e in errors)

    def test_negative_unit_cost(self):
        """Test cout unitaire negatif."""
        change = {
            'change_id': 'c1',
            'timestamp': 123,
            'item_id': 'i1',
            'change_type': 'stock_in',
            'quantity_before': 100,
            'quantity_change': 50,
            'quantity_after': 150,
            'unit_cost': -5.0,
        }
        is_valid, errors = validate_inventory_change(change)
        assert is_valid is False
        assert any("unit_cost" in e for e in errors)

    def test_stock_out_change(self):
        """Test sortie de stock valide."""
        change = {
            'change_id': 'c2',
            'timestamp': 456,
            'item_id': 'i2',
            'change_type': 'stock_out',
            'quantity_before': 200,
            'quantity_change': -30,
            'quantity_after': 170,
        }
        is_valid, errors = validate_inventory_change(change)
        assert is_valid is True


class TestSchemaHelpers:
    """Tests pour get_schema_fields et get_required_fields."""

    def test_get_schema_fields_event(self):
        """Test extraction des noms de champs."""
        fields = get_schema_fields("event_schema")
        assert isinstance(fields, list)
        assert len(fields) > 0

    def test_get_schema_fields_inventory(self):
        """Test extraction des noms de champs inventory."""
        fields = get_schema_fields("inventory_schema")
        assert isinstance(fields, list)
        assert len(fields) > 0

    def test_get_required_fields_event(self):
        """Test extraction des champs obligatoires."""
        required = get_required_fields("event_schema")
        assert isinstance(required, list)

    def test_get_required_fields_inventory(self):
        """Test extraction des champs obligatoires inventory."""
        required = get_required_fields("inventory_schema")
        assert isinstance(required, list)
