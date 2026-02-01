"""Configuration for Miyakowasure availability checker."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from miyakowasure_check.models import RoomType


@dataclass
class Config:
    """Application configuration."""

    check_in_date: date
    nights: int = 1
    guests: int = 2
    room_filter: list[RoomType] = field(default_factory=list)
    check_interval_minutes: int = 30
    ntfy_topic: str | None = None
    state_file: Path = field(default_factory=lambda: Path.home() / ".miyakowasure-state.json")
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
        from datetime import timedelta

        return self.check_in_date + timedelta(days=self.nights)

    @property
    def rooms_to_check(self) -> list[RoomType]:
        """Return rooms to check (all if no filter specified)."""
        if self.room_filter:
            return self.room_filter
        return list(RoomType)

    def validate_guests_for_rooms(self) -> list[str]:
        """Check if guest count is valid for requested rooms."""
        warnings = []
        for room in self.rooms_to_check:
            if self.guests > room.max_guests:
                warnings.append(
                    f"{room.display_name} only allows {room.max_guests} guests, "
                    f"but you requested {self.guests}"
                )
        return warnings


BASE_URL = "https://www3.yadosys.com/reserve/en"
ROOM_LIST_URL = f"{BASE_URL}/room/list/147/fgeggchbebhjhbeogefegpdn/all"
PLAN_LIST_URL = f"{BASE_URL}/plan/list/147/fgeggchbebhjhbeogefegpdn/all"
