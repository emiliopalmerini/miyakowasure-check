"""Ports (interfaces) for hexagonal architecture."""

from ryokan_check.ports.room import RoomInfo
from ryokan_check.ports.scraper import AvailabilityScraper

__all__ = ["RoomInfo", "AvailabilityScraper"]
