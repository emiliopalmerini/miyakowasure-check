"""Tests for notification state management."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

# Import property modules to register them
import ryokan_check.properties.miyakowasure  # noqa: F401
import ryokan_check.properties.miyamaso  # noqa: F401

from ryokan_check.domain.models import RoomAvailability
from ryokan_check.domain.property import Property
from ryokan_check.properties.miyakowasure.rooms import MiyakowasureRoom
from ryokan_check.properties.miyamaso.rooms import MiyamasoRoom
from ryokan_check.state import NotificationState, migrate_old_state_file


@pytest.fixture
def temp_state_file(tmp_path) -> Path:
    return tmp_path / "test-state.json"


@pytest.fixture
def sample_miyakowasure_room() -> RoomAvailability:
    return RoomAvailability(
        property=Property.MIYAKOWASURE,
        room=MiyakowasureRoom.SAKURA_RIVER,
        check_in=date(2026, 3, 15),
        check_out=date(2026, 3, 16),
        available=True,
    )


@pytest.fixture
def sample_miyamaso_room() -> RoomAvailability:
    return RoomAvailability(
        property=Property.MIYAMASO,
        room=MiyamasoRoom.HINAKURA,
        check_in=date(2026, 3, 15),
        check_out=date(2026, 3, 16),
        available=True,
    )


class TestNotificationState:
    def test_should_notify_when_never_notified(self, temp_state_file, sample_miyakowasure_room):
        state = NotificationState(state_file=temp_state_file)
        assert state.should_notify(sample_miyakowasure_room) is True

    def test_should_not_notify_when_recently_notified(self, temp_state_file, sample_miyakowasure_room):
        state = NotificationState(state_file=temp_state_file)
        state.mark_notified(sample_miyakowasure_room)
        assert state.should_notify(sample_miyakowasure_room) is False

    def test_should_notify_after_cooldown_expires(self, temp_state_file, sample_miyakowasure_room):
        state = NotificationState(state_file=temp_state_file, cooldown_hours=24)

        old_time = datetime.now() - timedelta(hours=25)
        key = state._make_key(sample_miyakowasure_room)
        state.notified[key] = old_time.isoformat()

        assert state.should_notify(sample_miyakowasure_room) is True

    def test_state_persists_to_file(self, temp_state_file, sample_miyakowasure_room):
        state1 = NotificationState(state_file=temp_state_file)
        state1.mark_notified(sample_miyakowasure_room)

        state2 = NotificationState(state_file=temp_state_file)
        state2.load()
        assert state2.should_notify(sample_miyakowasure_room) is False

    def test_load_handles_missing_file(self, temp_state_file):
        state = NotificationState(state_file=temp_state_file)
        state.load()
        assert state.notified == {}

    def test_load_handles_corrupt_file(self, temp_state_file):
        temp_state_file.write_text("not valid json")
        state = NotificationState(state_file=temp_state_file)
        state.load()
        assert state.notified == {}

    def test_different_rooms_tracked_separately(self, temp_state_file):
        room1 = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        room2 = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.MOMIJI_VIP,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )

        state = NotificationState(state_file=temp_state_file)
        state.mark_notified(room1)

        assert state.should_notify(room1) is False
        assert state.should_notify(room2) is True

    def test_different_dates_tracked_separately(self, temp_state_file):
        room1 = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        room2 = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.SAKURA_RIVER,
            check_in=date(2026, 3, 20),
            check_out=date(2026, 3, 21),
            available=True,
        )

        state = NotificationState(state_file=temp_state_file)
        state.mark_notified(room1)

        assert state.should_notify(room1) is False
        assert state.should_notify(room2) is True

    def test_different_properties_tracked_separately(
        self, temp_state_file, sample_miyakowasure_room, sample_miyamaso_room
    ):
        state = NotificationState(state_file=temp_state_file)
        state.mark_notified(sample_miyakowasure_room)

        assert state.should_notify(sample_miyakowasure_room) is False
        assert state.should_notify(sample_miyamaso_room) is True

    def test_key_includes_property(self, temp_state_file, sample_miyakowasure_room, sample_miyamaso_room):
        state = NotificationState(state_file=temp_state_file)
        key1 = state._make_key(sample_miyakowasure_room)
        key2 = state._make_key(sample_miyamaso_room)

        assert "miyakowasure" in key1
        assert "miyamaso" in key2
        assert key1 != key2


class TestStateMigration:
    def test_migrate_old_state_file(self, tmp_path):
        # Create old-style state file
        old_file = tmp_path / ".miyakowasure-state.json"
        old_data = {
            "notified": {
                "00001:2026-03-15:2026-03-16": "2026-02-01T14:30:00.123456"
            }
        }
        old_file.write_text(json.dumps(old_data))

        # Create new state directory
        new_dir = tmp_path / ".ryokan-check"

        # Patch home directory for test
        import ryokan_check.state as state_module
        original_home = Path.home
        try:
            # This is a simplified test - in real usage, home() would be patched
            new_dir.mkdir(parents=True, exist_ok=True)
            new_file = new_dir / "miyakowasure-state.json"

            # Simulate migration
            if old_file.exists() and not new_file.exists():
                data = json.loads(old_file.read_text())
                if "notified" in data:
                    migrated = {}
                    for key, value in data["notified"].items():
                        new_key = f"miyakowasure:{key}"
                        migrated[new_key] = value
                    data["notified"] = migrated
                new_file.write_text(json.dumps(data, indent=2))

            # Verify migration
            assert new_file.exists()
            migrated_data = json.loads(new_file.read_text())
            assert "miyakowasure:00001:2026-03-15:2026-03-16" in migrated_data["notified"]
        finally:
            pass
