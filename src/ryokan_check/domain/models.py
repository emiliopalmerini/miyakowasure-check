"""Core domain models for availability checking."""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from ryokan_check.domain.property import Property, get_property_config

if TYPE_CHECKING:
    from ryokan_check.ports.room import RoomInfo


@dataclass
class RoomAvailability:
    """Represents availability status for a specific room and date."""

    property: Property
    room: "RoomInfo"
    check_in: date
    check_out: date
    available: bool
    price_per_person: int | None = None
    spots_left: int | None = None

    @property
    def booking_url(self) -> str:
        """Generate direct booking URL for this room."""
        config = get_property_config(self.property)
        return config.booking_url_template.format(
            room_id=self.room.room_id,
            date=self.check_in.isoformat(),
        )

    def notification_message(self) -> str:
        """Format availability as notification message."""
        config = get_property_config(self.property)
        price_str = f"{self.price_per_person:,}/person" if self.price_per_person else "Price TBD"
        spots_str = f" ({self.spots_left} left)" if self.spots_left else ""

        onsen_note = ""
        if self.room.has_private_onsen:
            onsen_note = "\nPrivate onsen bath in room!"

        return (
            f"Room available at {config.display_name}!{onsen_note}\n\n"
            f"Room: {self.room.display_name}\n"
            f"Date: {self.check_in} -> {self.check_out}\n"
            f"Price: {price_str}{spots_str}\n\n"
            f"Book now: {self.booking_url}"
        )


@dataclass
class CheckResult:
    """Result of an availability check."""

    property: Property
    check_time: str
    rooms_checked: list[RoomAvailability]
    error: str | None = None

    @property
    def available_rooms(self) -> list[RoomAvailability]:
        """Filter to only available rooms."""
        return [r for r in self.rooms_checked if r.available]
