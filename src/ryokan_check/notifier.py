"""Notification services for availability alerts."""

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ryokan_check.domain.models import RoomAvailability
    from ryokan_check.domain.property import PropertyConfig


class NtfyNotifier:
    """Send notifications via ntfy.sh."""

    def __init__(self, topic: str, server: str = "https://ntfy.sh") -> None:
        self.topic = topic
        self.server = server.rstrip("/")
        self.url = f"{self.server}/{self.topic}"

    async def send(self, room: "RoomAvailability", prop_config: "PropertyConfig") -> bool:
        """Send notification for available room. Returns True if successful."""
        message = room.notification_message()

        # Property-aware title with onsen highlight
        if room.room.has_private_onsen:
            title = f"{prop_config.display_name}: {room.room.display_name} (Private Onsen!)"
            priority = "urgent"
            tags = "jp,hotel,onsen,fire"
        else:
            title = f"{prop_config.display_name}: {room.room.display_name} Available!"
            priority = "high"
            tags = "jp,hotel,onsen"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url,
                    content=message,
                    headers={
                        "Title": title,
                        "Priority": priority,
                        "Tags": tags,
                        "Click": room.booking_url,
                    },
                    timeout=30.0,
                )
                return response.status_code == 200
            except httpx.RequestError:
                return False

    async def send_status(self, message: str, title: str = "Ryokan Status") -> bool:
        """Send a status/info notification."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url,
                    content=message,
                    headers={
                        "Title": title,
                        "Priority": "default",
                        "Tags": "info",
                    },
                    timeout=30.0,
                )
                return response.status_code == 200
            except httpx.RequestError:
                return False
