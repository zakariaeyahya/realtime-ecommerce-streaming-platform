"""
Schema validators for e-commerce events and inventory changes.

Loads Avro schemas from .avsc files and provides Python validation
functions for Kafka messages before serialization/after deserialization.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.constants import EVENT_TYPES, REQUIRED_EVENT_FIELDS

logger = logging.getLogger(__name__)

SCHEMA_DIR = Path(__file__).parent / "schema"

VALID_EVENT_TYPES = EVENT_TYPES
VALID_CHANGE_TYPES = ["stock_in", "stock_out", "adjustment", "reservation", "release"]
VALID_DEVICE_TYPES = ["desktop", "mobile", "tablet"]


def load_avro_schema(schema_name: str) -> Dict[str, Any]:
    """Load an Avro schema from the schema directory.

    Args:
        schema_name: Name of the schema file (without .avsc extension).

    Returns:
        Parsed schema as a dictionary.

    Raises:
        FileNotFoundError: If schema file does not exist.
    """
    schema_path = SCHEMA_DIR / f"{schema_name}.avsc"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    logger.debug("Loaded schema: %s (%d fields)", schema_name, len(schema.get("fields", [])))
    return schema


def get_event_schema() -> Dict[str, Any]:
    """Load the e-commerce event Avro schema."""
    return load_avro_schema("event_schema")


def get_inventory_schema() -> Dict[str, Any]:
    """Load the inventory change Avro schema."""
    return load_avro_schema("inventory_schema")


def validate_event(event: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate an e-commerce event against schema rules.

    Args:
        event: Event dictionary to validate.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: List[str] = []

    for field in ("event_id", "event_type", "timestamp", "user_id"):
        if field not in event or event[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    event_type = event["event_type"]
    if event_type not in VALID_EVENT_TYPES:
        errors.append(f"Invalid event_type: {event_type}")
        return False, errors

    required = REQUIRED_EVENT_FIELDS.get(event_type, [])
    for field in required:
        if field not in event or event[field] is None:
            errors.append(f"Missing field '{field}' for event_type '{event_type}'")

    if not isinstance(event.get("timestamp"), (int, float)):
        errors.append("timestamp must be numeric")

    if "price" in event and event["price"] is not None:
        if not isinstance(event["price"], (int, float)) or event["price"] < 0:
            errors.append("price must be a non-negative number")

    if "quantity" in event and event["quantity"] is not None:
        if not isinstance(event["quantity"], int) or event["quantity"] < 0:
            errors.append("quantity must be a non-negative integer")

    if "rating" in event and event["rating"] is not None:
        if not isinstance(event["rating"], int) or not 1 <= event["rating"] <= 5:
            errors.append("rating must be an integer between 1 and 5")

    if "device_type" in event and event["device_type"] is not None:
        if event["device_type"] not in VALID_DEVICE_TYPES:
            errors.append(f"Invalid device_type: {event['device_type']}")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning("Event validation failed (%d errors): %s", len(errors), errors)
    return is_valid, errors


def validate_inventory_change(change: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate an inventory change event against schema rules.

    Args:
        change: Inventory change dictionary to validate.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: List[str] = []

    for field in ("change_id", "timestamp", "item_id", "change_type",
                  "quantity_before", "quantity_change", "quantity_after"):
        if field not in change or change[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    if change["change_type"] not in VALID_CHANGE_TYPES:
        errors.append(f"Invalid change_type: {change['change_type']}")

    for qty_field in ("quantity_before", "quantity_change", "quantity_after"):
        if not isinstance(change.get(qty_field), int):
            errors.append(f"{qty_field} must be an integer")

    if isinstance(change.get("quantity_before"), int) and isinstance(change.get("quantity_change"), int):
        expected_after = change["quantity_before"] + change["quantity_change"]
        if isinstance(change.get("quantity_after"), int) and change["quantity_after"] != expected_after:
            errors.append(
                f"quantity_after ({change['quantity_after']}) != "
                f"quantity_before ({change['quantity_before']}) + "
                f"quantity_change ({change['quantity_change']})"
            )

    if "unit_cost" in change and change["unit_cost"] is not None:
        if not isinstance(change["unit_cost"], (int, float)) or change["unit_cost"] < 0:
            errors.append("unit_cost must be a non-negative number")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning("Inventory validation failed (%d errors): %s", len(errors), errors)
    return is_valid, errors


def get_schema_fields(schema_name: str) -> List[str]:
    """Get field names from an Avro schema.

    Args:
        schema_name: Name of the schema file (without .avsc extension).

    Returns:
        List of field names defined in the schema.
    """
    schema = load_avro_schema(schema_name)
    return [field["name"] for field in schema.get("fields", [])]


def get_required_fields(schema_name: str) -> List[str]:
    """Get required (non-nullable) field names from an Avro schema.

    Args:
        schema_name: Name of the schema file (without .avsc extension).

    Returns:
        List of required field names (those without null union type).
    """
    schema = load_avro_schema(schema_name)
    required = []
    for field in schema.get("fields", []):
        field_type = field["type"]
        if isinstance(field_type, list) and "null" in field_type:
            continue
        required.append(field["name"])
    return required
