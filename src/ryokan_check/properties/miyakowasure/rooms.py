"""Room types at Miyakowasure ryokan."""

from enum import Enum


class MiyakowasureRoom(Enum):
    """Room types available at Miyakowasure."""

    TSUBAKI_VIEW = "00008"
    MOMIJI_VIP = "00006"
    MOMIJI_TWIN = "00007"
    MOMIJI_RIVER = "00005"
    SAKURA_RIVER = "00001"
    TSUBAKI_TOILET = "00002"

    @classmethod
    def from_string(cls, s: str) -> "MiyakowasureRoom | None":
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
    def room_id(self) -> str:
        """Unique ID used by Yadosys booking system."""
        return self.value

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

    @property
    def has_private_onsen(self) -> bool:
        """Miyakowasure has shared onsen only."""
        return False

    @property
    def base_price(self) -> int:
        """Base price per person."""
        prices = {
            self.TSUBAKI_VIEW: 29000,
            self.MOMIJI_VIP: 30000,
            self.MOMIJI_TWIN: 27000,
            self.MOMIJI_RIVER: 27000,
            self.SAKURA_RIVER: 25000,
            self.TSUBAKI_TOILET: 19500,
        }
        return prices[self]
