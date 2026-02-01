"""Tests for data models."""

from datetime import date

import pytest

# Import property modules to register them
import ryokan_check.properties.miyakowasure  # noqa: F401
import ryokan_check.properties.miyamaso  # noqa: F401

from ryokan_check.domain.models import RoomAvailability
from ryokan_check.domain.property import Property
from ryokan_check.properties.miyakowasure.rooms import MiyakowasureRoom
from ryokan_check.properties.miyamaso.rooms import MiyamasoRoom


class TestMiyakowasureRoom:
    def test_from_string_valid_inputs(self):
        assert MiyakowasureRoom.from_string("sakura") == MiyakowasureRoom.SAKURA_RIVER
        assert MiyakowasureRoom.from_string("SAKURA") == MiyakowasureRoom.SAKURA_RIVER
        assert MiyakowasureRoom.from_string("sakura-river") == MiyakowasureRoom.SAKURA_RIVER
        assert MiyakowasureRoom.from_string("momiji-vip") == MiyakowasureRoom.MOMIJI_VIP
        assert MiyakowasureRoom.from_string("vip") == MiyakowasureRoom.MOMIJI_VIP
        assert MiyakowasureRoom.from_string("twin") == MiyakowasureRoom.MOMIJI_TWIN
        assert MiyakowasureRoom.from_string("tsubaki-view") == MiyakowasureRoom.TSUBAKI_VIEW

    def test_from_string_invalid_inputs(self):
        assert MiyakowasureRoom.from_string("invalid") is None
        assert MiyakowasureRoom.from_string("") is None
        assert MiyakowasureRoom.from_string("random-room") is None

    def test_display_name(self):
        assert "SAKURA" in MiyakowasureRoom.SAKURA_RIVER.display_name
        assert "river" in MiyakowasureRoom.SAKURA_RIVER.display_name.lower()

    def test_max_guests(self):
        assert MiyakowasureRoom.MOMIJI_VIP.max_guests == 4
        assert MiyakowasureRoom.MOMIJI_TWIN.max_guests == 2
        assert MiyakowasureRoom.SAKURA_RIVER.max_guests == 3

    def test_has_private_onsen(self):
        # Miyakowasure has shared onsen only
        for room in MiyakowasureRoom:
            assert room.has_private_onsen is False


class TestMiyamasoRoom:
    def test_from_string_valid_inputs(self):
        assert MiyamasoRoom.from_string("hinakura") == MiyamasoRoom.HINAKURA
        assert MiyamasoRoom.from_string("HINAKURA") == MiyamasoRoom.HINAKURA
        assert MiyamasoRoom.from_string("rian") == MiyamasoRoom.RIAN_SANSUI_MAISONETTE
        assert MiyamasoRoom.from_string("rian-maisonette") == MiyamasoRoom.RIAN_SANSUI_MAISONETTE
        assert MiyamasoRoom.from_string("rian-japanese") == MiyamasoRoom.RIAN_SANSUI_JAPANESE

    def test_from_string_invalid_inputs(self):
        assert MiyamasoRoom.from_string("invalid") is None
        assert MiyamasoRoom.from_string("") is None
        assert MiyamasoRoom.from_string("sakura") is None  # Not a Miyamaso room

    def test_parse_multiple_rian(self):
        rooms = MiyamasoRoom.parse_multiple("rian")
        assert len(rooms) == 2
        assert MiyamasoRoom.RIAN_SANSUI_MAISONETTE in rooms
        assert MiyamasoRoom.RIAN_SANSUI_JAPANESE in rooms

    def test_parse_multiple_specific(self):
        rooms = MiyamasoRoom.parse_multiple("hinakura")
        assert rooms == [MiyamasoRoom.HINAKURA]

    def test_has_private_onsen(self):
        # All Miyamaso rooms we monitor have private onsen
        for room in MiyamasoRoom:
            assert room.has_private_onsen is True

    def test_max_guests(self):
        assert MiyamasoRoom.HINAKURA.max_guests == 4
        assert MiyamasoRoom.RIAN_SANSUI_MAISONETTE.max_guests == 4


class TestRoomAvailability:
    def test_booking_url_miyakowasure(self):
        room = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        assert "00001" in room.booking_url
        assert "yadosys.com" in room.booking_url

    def test_booking_url_miyamaso(self):
        room = RoomAvailability(
            property=Property.MIYAMASO,
            room=MiyamasoRoom.HINAKURA,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        assert "25112" in room.booking_url
        assert "489ban.net" in room.booking_url
        assert "2026-03-15" in room.booking_url

    def test_notification_message_includes_property_name(self):
        room = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
            price_per_person=25000,
        )
        message = room.notification_message()
        assert "Miyakowasure" in message
        assert "SAKURA" in message
        assert "25,000" in message

    def test_notification_message_includes_onsen_note(self):
        room = RoomAvailability(
            property=Property.MIYAMASO,
            room=MiyamasoRoom.HINAKURA,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        message = room.notification_message()
        assert "Private onsen" in message
        assert "HINAKURA" in message

    def test_notification_message_handles_missing_price(self):
        room = RoomAvailability(
            property=Property.MIYAKOWASURE,
            room=MiyakowasureRoom.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        message = room.notification_message()
        assert "TBD" in message
