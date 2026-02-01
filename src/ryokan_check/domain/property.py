"""Property enum and configuration registry."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ryokan_check.ports.room import RoomInfo


class Property(Enum):
    """Supported ryokan properties."""

    MIYAKOWASURE = "miyakowasure"
    MIYAMASO = "miyamaso"

    @classmethod
    def from_string(cls, s: str) -> "Property | None":
        """Parse property from string (supports aliases)."""
        aliases = {
            "miyakowasure": cls.MIYAKOWASURE,
            "miyamaso": cls.MIYAMASO,
            "takamiya": cls.MIYAMASO,
        }
        return aliases.get(s.lower().strip())

    @property
    def display_name(self) -> str:
        """Human-readable property name."""
        names = {
            self.MIYAKOWASURE: "Natsuse Onsen Miyakowasure",
            self.MIYAMASO: "Miyamaso Takamiya (Zao Onsen)",
        }
        return names[self]


@dataclass
class PropertyConfig:
    """Configuration for a specific property."""

    property: Property
    display_name: str
    base_url: str
    booking_url_template: str
    room_enum: type  # The room enum class
    scraper_class: type  # The scraper class
    state_filename: str

    def get_rooms(self) -> list["RoomInfo"]:
        """Return all room types for this property."""
        return list(self.room_enum)

    def parse_room(self, s: str) -> "RoomInfo | None":
        """Parse room string for this property."""
        return self.room_enum.from_string(s)


# Registry populated at module load by property modules
PROPERTY_CONFIGS: dict[Property, PropertyConfig] = {}


def register_property(config: PropertyConfig) -> None:
    """Register a property configuration."""
    PROPERTY_CONFIGS[config.property] = config


def get_property_config(prop: Property) -> PropertyConfig:
    """Get configuration for a property."""
    if prop not in PROPERTY_CONFIGS:
        raise ValueError(f"Property {prop.value} not registered. Import its module first.")
    return PROPERTY_CONFIGS[prop]


def get_all_properties() -> list[Property]:
    """Get all registered properties."""
    return list(PROPERTY_CONFIGS.keys())
