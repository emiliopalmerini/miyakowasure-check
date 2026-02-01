"""Tests for data models."""

from datetime import date

import pytest

from miyakowasure_check.models import RoomAvailability, RoomType


class TestRoomType:
    def test_from_string_valid_inputs(self):
        assert RoomType.from_string("sakura") == RoomType.SAKURA_RIVER
        assert RoomType.from_string("SAKURA") == RoomType.SAKURA_RIVER
        assert RoomType.from_string("sakura-river") == RoomType.SAKURA_RIVER
        assert RoomType.from_string("momiji-vip") == RoomType.MOMIJI_VIP
        assert RoomType.from_string("vip") == RoomType.MOMIJI_VIP
        assert RoomType.from_string("twin") == RoomType.MOMIJI_TWIN
        assert RoomType.from_string("tsubaki-view") == RoomType.TSUBAKI_VIEW

    def test_from_string_invalid_inputs(self):
        assert RoomType.from_string("invalid") is None
        assert RoomType.from_string("") is None
        assert RoomType.from_string("random-room") is None

    def test_display_name(self):
        assert "SAKURA" in RoomType.SAKURA_RIVER.display_name
        assert "river" in RoomType.SAKURA_RIVER.display_name.lower()

    def test_max_guests(self):
        assert RoomType.MOMIJI_VIP.max_guests == 4
        assert RoomType.MOMIJI_TWIN.max_guests == 2
        assert RoomType.SAKURA_RIVER.max_guests == 3


class TestRoomAvailability:
    def test_booking_url_includes_room_id(self):
        room = RoomAvailability(
            room_type=RoomType.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        assert "00001" in room.booking_url
        assert "yadosys.com" in room.booking_url

    def test_notification_message_includes_details(self):
        room = RoomAvailability(
            room_type=RoomType.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
            price_per_person=25000,
            spots_left=2,
        )
        message = room.notification_message()
        assert "SAKURA" in message
        assert "2026-03-15" in message
        assert "25,000" in message
        assert "2 left" in message
        assert "yadosys.com" in message

    def test_notification_message_handles_missing_price(self):
        room = RoomAvailability(
            room_type=RoomType.SAKURA_RIVER,
            check_in=date(2026, 3, 15),
            check_out=date(2026, 3, 16),
            available=True,
        )
        message = room.notification_message()
        assert "TBD" in message
