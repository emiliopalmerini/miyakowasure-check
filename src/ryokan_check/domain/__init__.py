"""Domain models and property registry."""

from ryokan_check.domain.models import CheckResult, RoomAvailability
from ryokan_check.domain.property import Property, PropertyConfig, get_property_config

__all__ = [
    "RoomAvailability",
    "CheckResult",
    "Property",
    "PropertyConfig",
    "get_property_config",
]
