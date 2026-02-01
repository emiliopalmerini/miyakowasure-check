"""CLI interface for Ryokan availability checker."""

import asyncio
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ryokan_check.config import Config
from ryokan_check.domain.models import CheckResult
from ryokan_check.domain.property import Property, get_property_config
from ryokan_check.notifier import NtfyNotifier
from ryokan_check.state import NotificationState, migrate_old_state_file

# Import property modules to trigger registration
import ryokan_check.properties.miyakowasure  # noqa: F401
import ryokan_check.properties.miyamaso  # noqa: F401

app = typer.Typer(
    name="ryokan-check",
    help="Monitor room availability at Japanese ryokan.",
    no_args_is_help=True,
)
console = Console()


def parse_properties(value: str) -> list[Property]:
    """Parse property argument (can be comma-separated or 'all')."""
    if value.lower() == "all":
        return list(Property)

    properties = []
    for p in value.split(","):
        prop = Property.from_string(p.strip())
        if prop:
            if prop not in properties:
                properties.append(prop)
        else:
            console.print(f"[red]Unknown property: {p}[/red]")
            console.print("Valid options: miyakowasure, miyamaso, takamiya, all")
            raise typer.Exit(1)
    return properties


def parse_rooms_for_property(room_str: str, prop: Property) -> list:
    """Parse room filter for a specific property."""
    from ryokan_check.properties.miyamaso.rooms import MiyamasoRoom

    config = get_property_config(prop)
    rooms = []

    for r in room_str.split(","):
        r_stripped = r.strip()
        # For Miyamaso, handle 'rian' specially to return both variants
        if prop == Property.MIYAMASO and r_stripped.lower() in ("rian", "rian-sansui", "sansui"):
            rooms.extend(MiyamasoRoom.parse_multiple(r_stripped))
        else:
            room = config.parse_room(r_stripped)
            if room:
                if room not in rooms:
                    rooms.append(room)
            else:
                console.print(f"[red]Unknown room '{r}' for {prop.value}[/red]")
                valid = [str(rm.room_id) for rm in config.get_rooms()]
                console.print(f"Valid room IDs: {', '.join(valid)}")
                raise typer.Exit(1)
    return rooms


def log(message: str) -> None:
    """Log a timestamped message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[dim]{timestamp}[/dim] {message}")


async def run_check_loop(config: Config) -> None:
    """Main check loop for all configured properties."""
    # Migrate old state file if needed
    migrate_old_state_file(config.state_dir)

    # Load state for each property
    states: dict[Property, NotificationState] = {}
    for prop in config.properties:
        state = NotificationState(state_file=config.state_file_for(prop))
        state.load()
        states[prop] = state

    notifier = NtfyNotifier(config.ntfy_topic) if config.ntfy_topic else None

    log(f"Starting availability checker for {config.check_in_date} ({config.nights} night(s))")
    log(f"Properties: {', '.join(p.value for p in config.properties)}")
    log(f"Guests: {config.guests}")
    log(f"Check interval: {config.check_interval_minutes} minutes")
    if notifier:
        log(f"Notifications via ntfy.sh topic: {config.ntfy_topic}")
    else:
        log("[yellow]No notification method configured - will only log to console[/yellow]")

    warnings = config.validate_guests_for_rooms()
    for warning in warnings:
        log(f"[yellow]Warning: {warning}[/yellow]")

    check_count = 0
    while True:
        check_count += 1
        log(f"[bold]Check #{check_count}[/bold]")

        for prop in config.properties:
            await _check_single_property(config, prop, states[prop], notifier)

        log(f"Next check in {config.check_interval_minutes} minutes...")
        await asyncio.sleep(config.check_interval_minutes * 60)


async def _check_single_property(
    config: Config,
    prop: Property,
    state: NotificationState,
    notifier: NtfyNotifier | None,
) -> CheckResult:
    """Check availability for a single property."""
    prop_config = get_property_config(prop)
    scraper_class = prop_config.scraper_class

    log(f"[bold cyan]{prop_config.display_name}[/bold cyan]")

    async with scraper_class(config) as scraper:
        result = await scraper.check_availability()

    if result.error:
        log(f"  [red]Error: {result.error}[/red]")
        return result

    available = result.available_rooms
    if available:
        log(f"  [green]Found {len(available)} available room(s)![/green]")
        for room in available:
            onsen_badge = " [bold magenta](Private Onsen!)[/bold magenta]" if room.room.has_private_onsen else ""
            log(f"  - {room.room.display_name}{onsen_badge}")
            if room.price_per_person:
                log(f"    Price: {room.price_per_person:,}/person")
            if room.spots_left:
                log(f"    Spots left: {room.spots_left}")

            if notifier and state.should_notify(room):
                success = await notifier.send(room, prop_config)
                if success:
                    state.mark_notified(room)
                    log("    [green]Notification sent![/green]")
                else:
                    log("    [red]Failed to send notification[/red]")
            elif notifier:
                log("    [dim]Already notified within 24h[/dim]")
    else:
        log("  [dim]No rooms available[/dim]")

    # Display table
    if result.rooms_checked:
        table = Table(title=f"{prop_config.display_name} Status", show_header=True)
        table.add_column("Room")
        table.add_column("Status")
        table.add_column("Price")
        table.add_column("Private Onsen")
        for room in result.rooms_checked:
            status = "[green]Available[/green]" if room.available else "[red]Unavailable[/red]"
            price = f"{room.price_per_person:,}" if room.price_per_person else "-"
            onsen = "[green]Yes[/green]" if room.room.has_private_onsen else "[dim]No[/dim]"
            table.add_row(room.room.display_name, status, price, onsen)
        console.print(table)

    return result


async def _single_check_all(config: Config) -> list[CheckResult]:
    """Run a single availability check for all properties."""
    log(f"Single check for {config.check_in_date} ({config.nights} night(s))")

    results = []
    for prop in config.properties:
        prop_config = get_property_config(prop)
        scraper_class = prop_config.scraper_class

        async with scraper_class(config) as scraper:
            result = await scraper.check_availability()
            results.append(result)

        if result.error:
            log(f"[red]Error for {prop.value}: {result.error}[/red]")
        elif result.rooms_checked:
            table = Table(title=f"{prop_config.display_name} Availability", show_header=True)
            table.add_column("Room")
            table.add_column("Status")
            table.add_column("Price")
            table.add_column("Private Onsen")
            for room in result.rooms_checked:
                status = "[green]Available[/green]" if room.available else "[red]Unavailable[/red]"
                price = f"{room.price_per_person:,}" if room.price_per_person else "-"
                onsen = "[green]Yes[/green]" if room.room.has_private_onsen else "[dim]No[/dim]"
                table.add_row(room.room.display_name, status, price, onsen)
            console.print(table)

    return results


@app.command()
def check(
    check_date: Annotated[
        str,
        typer.Option(
            "--date", "-d",
            help="Check-in date (YYYY-MM-DD)",
        ),
    ],
    property: Annotated[
        str,
        typer.Option(
            "--property", "-p",
            help="Property to check (miyakowasure, miyamaso, takamiya, all)",
        ),
    ] = "all",
    nights: Annotated[
        int,
        typer.Option(
            "--nights", "-n",
            help="Number of nights",
        ),
    ] = 1,
    guests: Annotated[
        int,
        typer.Option(
            "--guests", "-g",
            help="Number of guests",
        ),
    ] = 2,
    room: Annotated[
        str | None,
        typer.Option(
            "--room", "-r",
            help="Room type filter (comma-separated, e.g., sakura,hinakura)",
        ),
    ] = None,
    interval: Annotated[
        int,
        typer.Option(
            "--interval", "-i",
            help="Check interval in minutes (minimum 15)",
        ),
    ] = 30,
    ntfy_topic: Annotated[
        str | None,
        typer.Option(
            "--ntfy-topic",
            help="ntfy.sh topic for notifications",
            envvar="NTFY_TOPIC",
        ),
    ] = None,
    state_dir: Annotated[
        Path | None,
        typer.Option(
            "--state-dir",
            help="Directory for state files",
        ),
    ] = None,
    headless: Annotated[
        bool,
        typer.Option(
            "--headless/--no-headless",
            help="Run browser in headless mode",
        ),
    ] = True,
    once: Annotated[
        bool,
        typer.Option(
            "--once",
            help="Run a single check and exit",
        ),
    ] = False,
) -> None:
    """Check room availability at Japanese ryokan."""
    try:
        check_in_date = date.fromisoformat(check_date)
    except ValueError:
        console.print(f"[red]Invalid date format: {check_date}. Use YYYY-MM-DD[/red]")
        raise typer.Exit(1)

    properties = parse_properties(property)

    # Parse room filter per property
    room_filter: dict[Property, list] = {}
    if room:
        for prop in properties:
            try:
                prop_rooms = parse_rooms_for_property(room, prop)
                if prop_rooms:
                    room_filter[prop] = prop_rooms
            except typer.Exit:
                # Room not found for this property - skip it unless it's the only property
                if len(properties) == 1:
                    raise
                continue

    try:
        config = Config(
            check_in_date=check_in_date,
            properties=properties,
            nights=nights,
            guests=guests,
            room_filter=room_filter,
            check_interval_minutes=interval,
            ntfy_topic=ntfy_topic,
            state_dir=state_dir or Path.home() / ".ryokan-check",
            headless=headless,
        )
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)

    if once:
        results = asyncio.run(_single_check_all(config))
        has_error = any(r.error for r in results)
        raise typer.Exit(1 if has_error else 0)
    else:
        try:
            asyncio.run(run_check_loop(config))
        except KeyboardInterrupt:
            log("Shutting down...")
            raise typer.Exit(0)


@app.command()
def rooms(
    property: Annotated[
        str,
        typer.Option(
            "--property", "-p",
            help="Property to list rooms for (miyakowasure, miyamaso, all)",
        ),
    ] = "all",
) -> None:
    """List available room types for a property."""
    # Import properties to ensure registration
    import ryokan_check.properties.miyakowasure  # noqa: F401
    import ryokan_check.properties.miyamaso  # noqa: F401

    properties = parse_properties(property)

    for prop in properties:
        prop_config = get_property_config(prop)
        table = Table(title=f"{prop_config.display_name} Room Types", show_header=True)
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Max Guests")
        table.add_column("Private Onsen")

        for room in prop_config.get_rooms():
            onsen = "[green]Yes[/green]" if room.has_private_onsen else "[dim]No[/dim]"
            table.add_row(
                room.room_id,
                room.display_name,
                str(room.max_guests),
                onsen,
            )

        console.print(table)

        # Show usage hints
        if prop == Property.MIYAKOWASURE:
            console.print("[dim]Use --room with: sakura, momiji, momiji-vip, momiji-twin, tsubaki, tsubaki-view[/dim]")
        elif prop == Property.MIYAMASO:
            console.print("[dim]Use --room with: hinakura, rian (both variants), rian-maisonette, rian-japanese[/dim]")
        console.print()


if __name__ == "__main__":
    app()
