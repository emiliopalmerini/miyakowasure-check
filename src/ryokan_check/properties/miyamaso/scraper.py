"""Playwright-based scraper for 489ban.net booking system (Miyamaso Takamiya)."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import TYPE_CHECKING

from playwright.async_api import Browser, Page, async_playwright

from ryokan_check.domain.models import CheckResult, RoomAvailability
from ryokan_check.domain.property import Property
from ryokan_check.properties.miyamaso.rooms import MiyamasoRoom

if TYPE_CHECKING:
    from ryokan_check.config import Config

BASE_URL = "https://reserve.489ban.net/client/zao-takamiya/4"
ROOM_LIST_URL = f"{BASE_URL}/plan/availability/room#content"


class BanScraper:
    """Scrapes availability from 489ban.net booking system (Miyamaso Takamiya).

    The 489ban.net system is entirely JavaScript-rendered, so Playwright is required.
    This scraper navigates directly to room detail pages to check availability.
    """

    def __init__(self, config: "Config") -> None:
        self.config = config
        self._browser: Browser | None = None
        self._playwright = None

    async def __aenter__(self) -> "BanScraper":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.config.headless)
        return self

    async def __aexit__(self, *args) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def check_availability(self) -> CheckResult:
        """Check availability for configured dates and rooms."""
        check_time = datetime.now().isoformat()

        if not self._browser:
            return CheckResult(
                property=Property.MIYAMASO,
                check_time=check_time,
                rooms_checked=[],
                error="Browser not initialized",
            )

        try:
            results: list[RoomAvailability] = []
            rooms_to_check = self.config.rooms_to_check(Property.MIYAMASO)

            for room in rooms_to_check:
                if not isinstance(room, MiyamasoRoom):
                    continue
                availability = await self._check_room_availability(room)
                if availability:
                    results.append(availability)

            return CheckResult(
                property=Property.MIYAMASO,
                check_time=check_time,
                rooms_checked=results,
            )

        except Exception as e:
            return CheckResult(
                property=Property.MIYAMASO,
                check_time=check_time,
                rooms_checked=[],
                error=str(e),
            )

    async def _check_room_availability(self, room: MiyamasoRoom) -> RoomAvailability | None:
        """Check availability for a specific room by navigating to its detail page."""
        date_str = self.config.check_in_date.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/plan/room/{room.room_id}/stay?date={date_str}&roomCount=1"

        page = await self._browser.new_page()
        page.set_default_timeout(60000)

        try:
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(3)  # Wait for JS to render

            content = await page.content()
            is_available, price = self._parse_room_page(content)

            return RoomAvailability(
                property=Property.MIYAMASO,
                room=room,
                check_in=self.config.check_in_date,
                check_out=self.config.check_out_date,
                available=is_available,
                price_per_person=price,
            )

        except Exception:
            return RoomAvailability(
                property=Property.MIYAMASO,
                room=room,
                check_in=self.config.check_in_date,
                check_out=self.config.check_out_date,
                available=False,
            )
        finally:
            await page.close()

    def _parse_room_page(self, content: str) -> tuple[bool, int | None]:
        """Parse room detail page content for availability and price.

        Returns:
            Tuple of (is_available, price_per_person)
        """
        is_available = False
        price: int | None = None

        content_lower = content.lower()

        # Check for unavailability markers
        unavailable_markers = [
            "sold out",
            "no vacancy",
            "満室",
            "完売",
            "予約できません",
            "this plan is sold out",
        ]
        for marker in unavailable_markers:
            if marker in content_lower:
                return False, None

        # Check for availability markers
        available_markers = [
            "details",
            "reservations",
            "予約",
            "詳細",
            "book now",
            "reserve",
        ]

        # Look for plan cards with prices - indicates availability
        # 489ban.net shows prices like "29,700 JPY" or "¥29,700"
        price_patterns = [
            r"([0-9,]+)\s*JPY",
            r"[¥￥]([0-9,]+)",
            r"([0-9,]+)\s*円",
        ]

        for pattern in price_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                try:
                    parsed_price = int(price_str)
                    # Reasonable ryokan price range per person
                    if 15000 <= parsed_price <= 150000:
                        price = parsed_price
                        is_available = True
                        break
                except ValueError:
                    pass

        # Also check for reservation/details buttons if no price found
        if not is_available:
            for marker in available_markers:
                if marker in content_lower:
                    # Check if it's a clickable button/link
                    button_patterns = [
                        rf'<button[^>]*>{marker}',
                        rf'<a[^>]*>{marker}',
                        rf'class="[^"]*btn[^"]*"[^>]*>{marker}',
                    ]
                    for btn_pattern in button_patterns:
                        if re.search(btn_pattern, content, re.IGNORECASE):
                            is_available = True
                            break
                    if is_available:
                        break

        return is_available, price


async def check_availability(config: "Config") -> CheckResult:
    """Convenience function to check availability at Miyamaso."""
    async with BanScraper(config) as scraper:
        return await scraper.check_availability()
