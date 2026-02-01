"""Protocol for availability scrapers."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ryokan_check.domain.models import CheckResult


class AvailabilityScraper(Protocol):
    """Protocol for availability scrapers."""

    async def check_availability(self) -> "CheckResult":
        """Check room availability for configured dates."""
        ...

    async def __aenter__(self) -> "AvailabilityScraper":
        ...

    async def __aexit__(self, *args) -> None:
        ...
