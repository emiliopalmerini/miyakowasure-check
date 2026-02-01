"""Tests for property enum and registry."""

import pytest

# Import property modules to register them
import ryokan_check.properties.miyakowasure  # noqa: F401
import ryokan_check.properties.miyamaso  # noqa: F401

from ryokan_check.domain.property import (
    Property,
    PropertyConfig,
    get_property_config,
    get_all_properties,
)


class TestProperty:
    def test_from_string_miyakowasure(self):
        assert Property.from_string("miyakowasure") == Property.MIYAKOWASURE
        assert Property.from_string("MIYAKOWASURE") == Property.MIYAKOWASURE
        assert Property.from_string("  miyakowasure  ") == Property.MIYAKOWASURE

    def test_from_string_miyamaso_aliases(self):
        assert Property.from_string("miyamaso") == Property.MIYAMASO
        assert Property.from_string("takamiya") == Property.MIYAMASO
        assert Property.from_string("TAKAMIYA") == Property.MIYAMASO

    def test_from_string_invalid(self):
        assert Property.from_string("invalid") is None
        assert Property.from_string("") is None
        assert Property.from_string("random") is None

    def test_display_name(self):
        assert "Miyakowasure" in Property.MIYAKOWASURE.display_name
        assert "Miyamaso" in Property.MIYAMASO.display_name
        assert "Zao" in Property.MIYAMASO.display_name


class TestPropertyConfig:
    def test_miyakowasure_config_registered(self):
        config = get_property_config(Property.MIYAKOWASURE)
        assert config.display_name == "Natsuse Onsen Miyakowasure"
        assert "yadosys.com" in config.base_url

    def test_miyamaso_config_registered(self):
        config = get_property_config(Property.MIYAMASO)
        assert "Miyamaso" in config.display_name
        assert "489ban.net" in config.base_url

    def test_get_rooms_miyakowasure(self):
        config = get_property_config(Property.MIYAKOWASURE)
        rooms = config.get_rooms()
        assert len(rooms) == 6  # 6 Miyakowasure rooms

    def test_get_rooms_miyamaso(self):
        config = get_property_config(Property.MIYAMASO)
        rooms = config.get_rooms()
        assert len(rooms) == 3  # 3 Miyamaso rooms (Hinakura + 2 Rian Sansui)

    def test_parse_room_miyakowasure(self):
        config = get_property_config(Property.MIYAKOWASURE)
        room = config.parse_room("sakura")
        assert room is not None
        assert "SAKURA" in room.display_name

    def test_parse_room_miyamaso(self):
        config = get_property_config(Property.MIYAMASO)
        room = config.parse_room("hinakura")
        assert room is not None
        assert "HINAKURA" in room.display_name

    def test_parse_room_cross_property_fails(self):
        # Miyakowasure rooms shouldn't parse in Miyamaso
        miyamaso_config = get_property_config(Property.MIYAMASO)
        assert miyamaso_config.parse_room("sakura") is None

        # Miyamaso rooms shouldn't parse in Miyakowasure
        miyakowasure_config = get_property_config(Property.MIYAKOWASURE)
        assert miyakowasure_config.parse_room("hinakura") is None

    def test_miyamaso_rooms_have_private_onsen(self):
        config = get_property_config(Property.MIYAMASO)
        for room in config.get_rooms():
            assert room.has_private_onsen is True

    def test_miyakowasure_rooms_no_private_onsen(self):
        config = get_property_config(Property.MIYAKOWASURE)
        for room in config.get_rooms():
            assert room.has_private_onsen is False

    def test_all_properties_registered(self):
        properties = get_all_properties()
        assert Property.MIYAKOWASURE in properties
        assert Property.MIYAMASO in properties

    def test_state_filenames_unique(self):
        miyakowasure = get_property_config(Property.MIYAKOWASURE)
        miyamaso = get_property_config(Property.MIYAMASO)
        assert miyakowasure.state_filename != miyamaso.state_filename
