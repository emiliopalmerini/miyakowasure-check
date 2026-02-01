"""Playwright-based scraper for Yadosys booking system."""

import asyncio
import re
from datetime import date, datetime

from playwright.async_api import Browser, Page, async_playwright

from miyakowasure_check.config import PLAN_LIST_URL, Config
from miyakowasure_check.models import CheckResult, RoomAvailability, RoomType


class YadosysScraper:
    """Scrapes availability from Yadosys booking system."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._browser: Browser | None = None

    async def __aenter__(self) -> "YadosysScraper":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.config.headless)
        return self

    async def __aexit__(self, *args) -> None:
        if self._browser:
            await self._browser.close()
        await self._playwright.stop()

    async def check_availability(self) -> CheckResult:
        """Check availability for configured dates and rooms."""
        check_time = datetime.now().isoformat()

        if not self._browser:
            return CheckResult(check_time=check_time, rooms_checked=[], error="Browser not initialized")

        try:
            page = await self._browser.new_page()
            page.set_default_timeout(60000)

            await page.goto(PLAN_LIST_URL, wait_until="networkidle")
            await asyncio.sleep(2)

            await self._fill_search_form(page)
            await self._submit_and_wait(page)

            rooms = await self._parse_availability(page)
            await page.close()

            return CheckResult(check_time=check_time, rooms_checked=rooms)

        except Exception as e:
            return CheckResult(check_time=check_time, rooms_checked=[], error=str(e))

    async def _fill_search_form(self, page: Page) -> None:
        """Fill in the search form with target dates and guest count."""
        check_in = self.config.check_in_date

        year_select = page.locator('select[name*="year"], select[id*="year"]').first
        month_select = page.locator('select[name*="month"], select[id*="month"]').first
        day_select = page.locator('select[name*="day"], select[id*="day"]').first

        if await year_select.count() > 0:
            await year_select.select_option(str(check_in.year))
        if await month_select.count() > 0:
            await month_select.select_option(str(check_in.month))
        if await day_select.count() > 0:
            await day_select.select_option(str(check_in.day))

        nights_select = page.locator('select[name*="night"], select[name*="stay"]').first
        if await nights_select.count() > 0:
            await nights_select.select_option(str(self.config.nights))

        male_input = page.locator('select[name*="male"], input[name*="male"]').first
        female_input = page.locator('select[name*="female"], input[name*="female"]').first

        if await male_input.count() > 0:
            if await male_input.evaluate("el => el.tagName") == "SELECT":
                await male_input.select_option(str(self.config.guests))
            else:
                await male_input.fill(str(self.config.guests))

        if await female_input.count() > 0:
            if await female_input.evaluate("el => el.tagName") == "SELECT":
                await female_input.select_option("0")
            else:
                await female_input.fill("0")

    async def _submit_and_wait(self, page: Page) -> None:
        """Submit search form and wait for results."""
        submit_btn = page.locator(
            'input[type="submit"], button[type="submit"], '
            'input[value*="Search"], input[value*="検索"], '
            'button:has-text("Search"), button:has-text("検索")'
        ).first

        if await submit_btn.count() > 0:
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

    async def _parse_availability(self, page: Page) -> list[RoomAvailability]:
        """Parse room availability from the results page."""
        results: list[RoomAvailability] = []
        rooms_to_check = self.config.rooms_to_check

        content = await page.content()

        for room_type in rooms_to_check:
            availability = await self._check_room_availability(page, content, room_type)
            if availability:
                results.append(availability)

        return results

    async def _check_room_availability(
        self, page: Page, content: str, room_type: RoomType
    ) -> RoomAvailability | None:
        """Check availability for a specific room type."""
        room_name = room_type.display_name
        room_id = room_type.value

        is_available = False
        price: int | None = None
        spots_left: int | None = None

        room_section = page.locator(f'[href*="{room_id}"], [data-room*="{room_id}"]').first
        if await room_section.count() == 0:
            room_section = page.locator(f'text="{room_name}"').first

        has_room = await room_section.count() > 0

        unavailable_markers = ["×", "満室", "sold out", "unavailable", "no vacancy"]
        available_markers = ["○", "◎", "空室", "available", "vacancy"]

        content_lower = content.lower()
        room_name_lower = room_name.lower()

        if room_name_lower in content_lower or room_id in content:
            for marker in unavailable_markers:
                pattern = f"{room_name}.*?{re.escape(marker)}|{re.escape(marker)}.*?{room_name}"
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    is_available = False
                    break
            else:
                for marker in available_markers:
                    if marker in content:
                        is_available = True
                        break

            price_patterns = [
                rf"{room_name}.*?[¥￥]([0-9,]+)",
                rf"[¥￥]([0-9,]+).*?{room_name}",
                r"[¥￥]([0-9,]+)",
            ]
            for pattern in price_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    price_str = match.group(1).replace(",", "")
                    try:
                        price = int(price_str)
                        if 10000 <= price <= 100000:
                            break
                    except ValueError:
                        pass

            spots_pattern = r"(\d+)\s*(?:rooms?|left|remaining|組|室)"
            match = re.search(spots_pattern, content, re.IGNORECASE)
            if match:
                spots_left = int(match.group(1))

            if not is_available and price and price > 10000:
                is_available = True

        return RoomAvailability(
            room_type=room_type,
            check_in=self.config.check_in_date,
            check_out=self.config.check_out_date,
            available=is_available,
            price_per_person=price,
            spots_left=spots_left,
        )


async def check_availability(config: Config) -> CheckResult:
    """Convenience function to check availability."""
    async with YadosysScraper(config) as scraper:
        return await scraper.check_availability()
