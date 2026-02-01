"""Protocol for room type information across all properties."""

from typing import Protocol, Self


class RoomInfo(Protocol):
    """Protocol for room type information across all properties."""

    @property
    def room_id(self) -> str:
        """Unique ID used by the booking system."""
        ...

    @property
    def display_name(self) -> str:
        """Human-readable room name."""
        ...

    @property
    def max_guests(self) -> int:
        """Maximum number of guests."""
        ...

    @property
    def has_private_onsen(self) -> bool:
        """Whether room has private hot spring bath."""
        ...

    @classmethod
    def from_string(cls, s: str) -> Self | None:
        """Parse room from user-friendly string."""
        ...
