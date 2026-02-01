"""Notification services for availability alerts."""

import httpx

from miyakowasure_check.models import RoomAvailability


class NtfyNotifier:
    """Send notifications via ntfy.sh."""

    def __init__(self, topic: str, server: str = "https://ntfy.sh") -> None:
        self.topic = topic
        self.server = server.rstrip("/")
        self.url = f"{self.server}/{self.topic}"

    async def send(self, room: RoomAvailability) -> bool:
        """Send notification for available room. Returns True if successful."""
        message = room.notification_message()
        title = f"Miyakowasure: {room.room_type.display_name} Available!"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url,
                    content=message,
                    headers={
                        "Title": title,
                        "Priority": "high",
                        "Tags": "jp,hotel,onsen",
                        "Click": room.booking_url,
                    },
                    timeout=30.0,
                )
                return response.status_code == 200
            except httpx.RequestError:
                return False

    async def send_status(self, message: str, title: str = "Miyakowasure Status") -> bool:
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
