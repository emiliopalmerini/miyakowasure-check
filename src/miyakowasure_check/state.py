"""State management for tracking notifications."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from miyakowasure_check.models import RoomAvailability


@dataclass
class NotificationState:
    """Tracks which room+date combos have been notified to avoid spam."""

    state_file: Path
    notified: dict[str, str] = field(default_factory=dict)
    cooldown_hours: int = 24

    def _make_key(self, room: RoomAvailability) -> str:
        """Create unique key for room+date combo."""
        return f"{room.room_type.value}:{room.check_in}:{room.check_out}"

    def load(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.notified = data.get("notified", {})
                self._cleanup_expired()
            except (json.JSONDecodeError, KeyError):
                self.notified = {}

    def save(self) -> None:
        """Save state to file."""
        self._cleanup_expired()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"notified": self.notified}, indent=2))

    def _cleanup_expired(self) -> None:
        """Remove entries older than cooldown period."""
        cutoff = datetime.now() - timedelta(hours=self.cooldown_hours)
        self.notified = {
            k: v
            for k, v in self.notified.items()
            if datetime.fromisoformat(v) > cutoff
        }

    def should_notify(self, room: RoomAvailability) -> bool:
        """Check if we should send a notification for this room."""
        key = self._make_key(room)
        if key not in self.notified:
            return True

        last_notified = datetime.fromisoformat(self.notified[key])
        return datetime.now() - last_notified > timedelta(hours=self.cooldown_hours)

    def mark_notified(self, room: RoomAvailability) -> None:
        """Mark a room as notified."""
        key = self._make_key(room)
        self.notified[key] = datetime.now().isoformat()
        self.save()
