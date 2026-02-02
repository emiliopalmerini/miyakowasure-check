"""Notification services for availability alerts."""

from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import aiosmtplib

if TYPE_CHECKING:
    from ryokan_check.domain.models import RoomAvailability
    from ryokan_check.domain.property import PropertyConfig


@dataclass
class EmailConfig:
    """SMTP email configuration."""

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_address: str
    to_address: str
    use_tls: bool = True


class EmailNotifier:
    """Send notifications via email using SMTP."""

    def __init__(self, config: EmailConfig) -> None:
        self.config = config

    async def send(self, room: "RoomAvailability", prop_config: "PropertyConfig") -> bool:
        """Send notification for available room. Returns True if successful."""
        message = room.notification_message()

        # Property-aware subject with onsen highlight
        if room.room.has_private_onsen:
            subject = f"{prop_config.display_name}: {room.room.display_name} (Private Onsen!)"
        else:
            subject = f"{prop_config.display_name}: {room.room.display_name} Available!"

        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.from_address
        msg["To"] = self.config.to_address

        # Plain text version
        text_body = f"{message}\n\nBook now: {room.booking_url}"
        msg.attach(MIMEText(text_body, "plain"))

        # HTML version
        html_body = f"""
        <html>
        <body>
            <h2>{subject}</h2>
            <p>{message}</p>
            <p><a href="{room.booking_url}">Book now</a></p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.smtp_user,
                password=self.config.smtp_password,
                start_tls=self.config.use_tls,
            )
            return True
        except aiosmtplib.SMTPException:
            return False

    async def send_status(self, message: str, title: str = "Ryokan Status") -> bool:
        """Send a status/info notification."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = self.config.from_address
        msg["To"] = self.config.to_address

        msg.attach(MIMEText(message, "plain"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.smtp_user,
                password=self.config.smtp_password,
                start_tls=self.config.use_tls,
            )
            return True
        except aiosmtplib.SMTPException:
            return False
