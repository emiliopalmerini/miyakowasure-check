"""Tests for configuration."""

from datetime import date

import pytest

from miyakowasure_check.config import Config
from miyakowasure_check.models import RoomType


class TestConfig:
    def test_check_out_date_calculation(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            nights=2,
        )
        assert config.check_out_date == date(2026, 3, 17)

    def test_single_night_checkout(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            nights=1,
        )
        assert config.check_out_date == date(2026, 3, 16)

    def test_rooms_to_check_defaults_to_all(self):
        config = Config(check_in_date=date(2026, 3, 15))
        assert len(config.rooms_to_check) == len(RoomType)

    def test_rooms_to_check_with_filter(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            room_filter=[RoomType.SAKURA_RIVER],
        )
        assert config.rooms_to_check == [RoomType.SAKURA_RIVER]

    def test_rejects_interval_below_15_minutes(self):
        with pytest.raises(ValueError, match="at least 15"):
            Config(
                check_in_date=date(2026, 3, 15),
                check_interval_minutes=10,
            )

    def test_rejects_zero_guests(self):
        with pytest.raises(ValueError, match="at least 1"):
            Config(
                check_in_date=date(2026, 3, 15),
                guests=0,
            )

    def test_rejects_zero_nights(self):
        with pytest.raises(ValueError, match="at least 1"):
            Config(
                check_in_date=date(2026, 3, 15),
                nights=0,
            )

    def test_validate_guests_for_rooms_warns_on_excess(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            guests=5,
            room_filter=[RoomType.MOMIJI_VIP],
        )
        warnings = config.validate_guests_for_rooms()
        assert len(warnings) == 1
        assert "4 guests" in warnings[0]

    def test_validate_guests_for_rooms_no_warnings_when_valid(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            guests=2,
            room_filter=[RoomType.MOMIJI_VIP],
        )
        warnings = config.validate_guests_for_rooms()
        assert len(warnings) == 0
