"""Data models for Miyakowasure availability checker."""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class RoomType(Enum):
    """Room types available at Miyakowasure."""

    TSUBAKI_VIEW = "00008"
    MOMIJI_VIP = "00006"
    MOMIJI_TWIN = "00007"
    MOMIJI_RIVER = "00005"
    SAKURA_RIVER = "00001"
    TSUBAKI_TOILET = "00002"

    @classmethod
    def from_string(cls, s: str) -> "RoomType | None":
        """Parse room type from user-friendly string."""
        mapping = {
            "tsubaki-view": cls.TSUBAKI_VIEW,
            "tsubaki_view": cls.TSUBAKI_VIEW,
            "momiji-vip": cls.MOMIJI_VIP,
            "momiji_vip": cls.MOMIJI_VIP,
            "vip": cls.MOMIJI_VIP,
            "momiji-twin": cls.MOMIJI_TWIN,
            "momiji_twin": cls.MOMIJI_TWIN,
            "twin": cls.MOMIJI_TWIN,
            "momiji-river": cls.MOMIJI_RIVER,
            "momiji_river": cls.MOMIJI_RIVER,
            "momiji": cls.MOMIJI_RIVER,
            "sakura-river": cls.SAKURA_RIVER,
            "sakura_river": cls.SAKURA_RIVER,
            "sakura": cls.SAKURA_RIVER,
            "tsubaki-toilet": cls.TSUBAKI_TOILET,
            "tsubaki_toilet": cls.TSUBAKI_TOILET,
            "tsubaki": cls.TSUBAKI_TOILET,
        }
        return mapping.get(s.lower().strip())

    @property
    def display_name(self) -> str:
        """Human-readable room name."""
        names = {
            self.TSUBAKI_VIEW: "TSUBAKI-KAN (Room with a view)",
            self.MOMIJI_VIP: "MOMIJI-KAN VIP ROOM",
            self.MOMIJI_TWIN: "MOMIJI-KAN Western twin bed",
            self.MOMIJI_RIVER: "MOMIJI-KAN (river view)",
            self.SAKURA_RIVER: "SAKURA-KAN (river view)",
            self.TSUBAKI_TOILET: "TSUBAKI-KAN (private toilet)",
        }
        return names[self]

    @property
    def max_guests(self) -> int:
        """Maximum number of guests for this room."""
        limits = {
            self.TSUBAKI_VIEW: 3,
            self.MOMIJI_VIP: 4,
            self.MOMIJI_TWIN: 2,
            self.MOMIJI_RIVER: 2,
            self.SAKURA_RIVER: 3,
            self.TSUBAKI_TOILET: 2,
        }
        return limits[self]


ROOM_INFO: dict[RoomType, dict] = {
    RoomType.TSUBAKI_VIEW: {
        "name": "TSUBAKI-KAN (Room with a view)",
        "max_guests": 3,
        "base_price": 29000,
    },
    RoomType.MOMIJI_VIP: {
        "name": "MOMIJI-KAN VIP ROOM",
        "max_guests": 4,
        "base_price": 30000,
    },
    RoomType.MOMIJI_TWIN: {
        "name": "MOMIJI-KAN Western twin bed",
        "max_guests": 2,
        "base_price": 27000,
    },
    RoomType.MOMIJI_RIVER: {
        "name": "MOMIJI-KAN (river view)",
        "max_guests": 2,
        "base_price": 27000,
    },
    RoomType.SAKURA_RIVER: {
        "name": "SAKURA-KAN (river view)",
        "max_guests": 3,
        "base_price": 25000,
    },
    RoomType.TSUBAKI_TOILET: {
        "name": "TSUBAKI-KAN (private toilet)",
        "max_guests": 2,
        "base_price": 19500,
    },
}


@dataclass
class RoomAvailability:
    """Represents availability status for a specific room and date."""

    room_type: RoomType
    check_in: date
    check_out: date
    available: bool
    price_per_person: int | None = None
    spots_left: int | None = None

    @property
    def booking_url(self) -> str:
        """Generate direct booking URL for this room."""
        base = "https://www3.yadosys.com/reserve/en/room/list/147/fgeggchbebhjhbeogefegpdn"
        return f"{base}/{self.room_type.value}"

    def notification_message(self) -> str:
        """Format availability as notification message."""
        price_str = f"¥{self.price_per_person:,}/person" if self.price_per_person else "Price TBD"
        spots_str = f" ({self.spots_left} left)" if self.spots_left else ""
        return (
            f"Room available at Miyakowasure!\n\n"
            f"Room: {self.room_type.display_name}\n"
            f"Date: {self.check_in} → {self.check_out}\n"
            f"Price: {price_str}{spots_str}\n\n"
            f"Book now: {self.booking_url}"
        )


@dataclass
class CheckResult:
    """Result of an availability check."""

    check_time: str
    rooms_checked: list[RoomAvailability]
    error: str | None = None

    @property
    def available_rooms(self) -> list[RoomAvailability]:
        """Filter to only available rooms."""
        return [r for r in self.rooms_checked if r.available]
