"""Miyakowasure property module."""

from ryokan_check.domain.property import Property, PropertyConfig, register_property
from ryokan_check.properties.miyakowasure.rooms import MiyakowasureRoom
from ryokan_check.properties.miyakowasure.scraper import YadosysScraper

MIYAKOWASURE_CONFIG = PropertyConfig(
    property=Property.MIYAKOWASURE,
    display_name="Natsuse Onsen Miyakowasure",
    base_url="https://www3.yadosys.com/reserve/en",
    booking_url_template="https://www3.yadosys.com/reserve/en/room/list/147/fgeggchbebhjhbeogefegpdn/{room_id}",
    room_enum=MiyakowasureRoom,
    scraper_class=YadosysScraper,
    state_filename="miyakowasure-state.json",
)

register_property(MIYAKOWASURE_CONFIG)

__all__ = ["MiyakowasureRoom", "YadosysScraper", "MIYAKOWASURE_CONFIG"]
