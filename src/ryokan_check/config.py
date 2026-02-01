"""Configuration for ryokan availability checker."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from ryokan_check.domain.property import Property, get_property_config

if TYPE_CHECKING:
    from ryokan_check.ports.room import RoomInfo

# Default state directory
DEFAULT_STATE_DIR = Path.home() / ".ryokan-check"


@dataclass
class Config:
    """Application configuration."""

    check_in_date: date
    properties: list[Property] = field(default_factory=lambda: list(Property))
    nights: int = 1
    guests: int = 2
    room_filter: dict[Property, list["RoomInfo"]] = field(default_factory=dict)
    check_interval_minutes: int = 30
    ntfy_topic: str | None = None
    state_dir: Path = field(default_factory=lambda: DEFAULT_STATE_DIR)
    headless: bool = True

    def __post_init__(self) -> None:
        if self.nights < 1:
            raise ValueError("nights must be at least 1")
        if self.guests < 1:
            raise ValueError("guests must be at least 1")
        if self.check_interval_minutes < 15:
            raise ValueError("check_interval_minutes must be at least 15 (be respectful to the ryokan)")

    @property
    def check_out_date(self) -> date:
        """Calculate check-out date from check-in and nights."""
        return self.check_in_date + timedelta(days=self.nights)

    def rooms_to_check(self, prop: Property) -> list["RoomInfo"]:
        """Return rooms to check for a specific property."""
        if prop in self.room_filter and self.room_filter[prop]:
            return self.room_filter[prop]
        config = get_property_config(prop)
        return config.get_rooms()

    def state_file_for(self, prop: Property) -> Path:
        """Get state file path for a property."""
        config = get_property_config(prop)
        return self.state_dir / config.state_filename

    def validate_guests_for_property(self, prop: Property) -> list[str]:
        """Check if guest count is valid for property's rooms."""
        warnings = []
        for room in self.rooms_to_check(prop):
            if self.guests > room.max_guests:
                warnings.append(
                    f"{room.display_name} only allows {room.max_guests} guests, "
                    f"but you requested {self.guests}"
                )
        return warnings

    def validate_guests_for_rooms(self) -> list[str]:
        """Check if guest count is valid for all properties."""
        warnings = []
        for prop in self.properties:
            warnings.extend(self.validate_guests_for_property(prop))
        return warnings
