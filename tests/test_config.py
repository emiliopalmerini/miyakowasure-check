"""Tests for configuration."""

from datetime import date

import pytest

# Import property modules to register them
import ryokan_check.properties.miyakowasure  # noqa: F401
import ryokan_check.properties.miyamaso  # noqa: F401

from ryokan_check.config import Config
from ryokan_check.domain.property import Property
from ryokan_check.properties.miyakowasure.rooms import MiyakowasureRoom
from ryokan_check.properties.miyamaso.rooms import MiyamasoRoom


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
        miyakowasure_rooms = config.rooms_to_check(Property.MIYAKOWASURE)
        assert len(miyakowasure_rooms) == len(MiyakowasureRoom)

    def test_rooms_to_check_with_filter(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            room_filter={Property.MIYAKOWASURE: [MiyakowasureRoom.SAKURA_RIVER]},
        )
        assert config.rooms_to_check(Property.MIYAKOWASURE) == [MiyakowasureRoom.SAKURA_RIVER]

    def test_rooms_to_check_per_property(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            room_filter={
                Property.MIYAKOWASURE: [MiyakowasureRoom.SAKURA_RIVER],
                Property.MIYAMASO: [MiyamasoRoom.HINAKURA],
            },
        )
        assert config.rooms_to_check(Property.MIYAKOWASURE) == [MiyakowasureRoom.SAKURA_RIVER]
        assert config.rooms_to_check(Property.MIYAMASO) == [MiyamasoRoom.HINAKURA]

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

    def test_validate_guests_for_property_warns_on_excess(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            guests=5,
            room_filter={Property.MIYAKOWASURE: [MiyakowasureRoom.MOMIJI_VIP]},
        )
        warnings = config.validate_guests_for_property(Property.MIYAKOWASURE)
        assert len(warnings) == 1
        assert "4 guests" in warnings[0]

    def test_validate_guests_for_property_no_warnings_when_valid(self):
        config = Config(
            check_in_date=date(2026, 3, 15),
            guests=2,
            room_filter={Property.MIYAKOWASURE: [MiyakowasureRoom.MOMIJI_VIP]},
        )
        warnings = config.validate_guests_for_property(Property.MIYAKOWASURE)
        assert len(warnings) == 0

    def test_state_file_for_property(self):
        config = Config(check_in_date=date(2026, 3, 15))
        miyakowasure_state = config.state_file_for(Property.MIYAKOWASURE)
        miyamaso_state = config.state_file_for(Property.MIYAMASO)

        assert "miyakowasure-state.json" in str(miyakowasure_state)
        assert "miyamaso-state.json" in str(miyamaso_state)
        assert miyakowasure_state != miyamaso_state

    def test_default_properties_includes_all(self):
        config = Config(check_in_date=date(2026, 3, 15))
        assert Property.MIYAKOWASURE in config.properties
        assert Property.MIYAMASO in config.properties
