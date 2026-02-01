"""Tests for notification state management."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from miyakowasure_check.models import RoomAvailability, RoomType
from miyakowasure_check.state import NotificationState


@pytest.fixture
def temp_state_file(tmp_path) -> Path:
    return tmp_path / "test-state.json"


@pytest.fixture
def sample_room() -> RoomAvailability:
    return RoomAvailability(
        room_type=RoomType.SAKURA_RIVER,
        check_in=date(2026, 3, 15),
        check_out=date(2026, 3, 16),
        available=True,
    )


class TestNotificationState:
    def test_should_notify_when_never_notified(self, temp_state_file, sample_room):
        state = NotificationState(state_file=temp_state_file)
        assert state.should_notify(sample_room) is True

    def test_should_not_notify_when_recently_notified(self, temp_state_file, sample_room):
        state = NotificationState(state_file=temp_state_file)
        state.mark_notified(sample_room)
        assert state.should_notify(sample_room) is False

    def test_should_notify_after_cooldown_expires(self, temp_state_file, sample_room):
        state = NotificationState(state_file=temp_state_file, cooldown_hours=24)

        old_time = datetime.now() - timedelta(hours=25)
        key = state._make_key(sample_room)
        state.notified[key] = old_time.isoformat()

        assert state.should_notify(sample_room) is True

    def test_state_persists_to_file(self, temp_state_file, sample_room):
        state1 = NotificationState(state_file=temp_state_file)
        state1.mark_notified(sample_room)

        state2 = NotificationState(state_file=temp_state_file)
        state2.load()
        assert state2.should_notify(sample_room) is False

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
            room_type=RoomType.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        room2 = RoomAvailability(
            room_type=RoomType.MOMIJI_VIP,
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
            room_type=RoomType.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        room2 = RoomAvailability(
            room_type=RoomType.SAKURA_RIVER,
            check_in=date(2026, 3, 20),
            check_out=date(2026, 3, 21),
            available=True,
        )

        state = NotificationState(state_file=temp_state_file)
        state.mark_notified(room1)

        assert state.should_notify(room1) is False
        assert state.should_notify(room2) is True
