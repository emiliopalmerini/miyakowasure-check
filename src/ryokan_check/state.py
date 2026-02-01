"""State management for tracking notifications."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryokan_check.domain.models import RoomAvailability


@dataclass
class NotificationState:
    """Tracks which room+date combos have been notified to avoid spam."""

    state_file: Path
    notified: dict[str, str] = field(default_factory=dict)
    cooldown_hours: int = 24

    def _make_key(self, room: "RoomAvailability") -> str:
        """Create unique key for property+room+date combo."""
        return f"{room.property.value}:{room.room.room_id}:{room.check_in}:{room.check_out}"

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

    def should_notify(self, room: "RoomAvailability") -> bool:
        """Check if we should send a notification for this room."""
        key = self._make_key(room)
        if key not in self.notified:
            return True

        last_notified = datetime.fromisoformat(self.notified[key])
        return datetime.now() - last_notified > timedelta(hours=self.cooldown_hours)

    def mark_notified(self, room: "RoomAvailability") -> None:
        """Mark a room as notified."""
        key = self._make_key(room)
        self.notified[key] = datetime.now().isoformat()
        self.save()


def migrate_old_state_file(state_dir: Path) -> None:
    """Migrate old single state file to new per-property structure."""
    old_file = Path.home() / ".miyakowasure-state.json"
    new_file = state_dir / "miyakowasure-state.json"

    if old_file.exists() and not new_file.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(old_file.read_text())
            # Old format used room_id:check_in:check_out as key
            # New format uses property:room_id:check_in:check_out
            if "notified" in data:
                migrated = {}
                for key, value in data["notified"].items():
                    # Prefix with miyakowasure property
                    new_key = f"miyakowasure:{key}"
                    migrated[new_key] = value
                data["notified"] = migrated
            new_file.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, IOError):
            pass
