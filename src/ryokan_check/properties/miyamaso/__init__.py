"""Miyamaso Takamiya property module."""

from ryokan_check.domain.property import Property, PropertyConfig, register_property
from ryokan_check.properties.miyamaso.rooms import MiyamasoRoom
from ryokan_check.properties.miyamaso.scraper import BanScraper

MIYAMASO_CONFIG = PropertyConfig(
    property=Property.MIYAMASO,
    display_name="Miyamaso Takamiya (Zao Onsen)",
    base_url="https://reserve.489ban.net/client/zao-takamiya/4",
    booking_url_template="https://reserve.489ban.net/client/zao-takamiya/4/plan/room/{room_id}/stay?date={date}&roomCount=1",
    room_enum=MiyamasoRoom,
    scraper_class=BanScraper,
    state_filename="miyamaso-state.json",
)

register_property(MIYAMASO_CONFIG)

__all__ = ["MiyamasoRoom", "BanScraper", "MIYAMASO_CONFIG"]
