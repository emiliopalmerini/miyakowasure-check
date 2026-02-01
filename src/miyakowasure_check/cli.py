"""CLI interface for Miyakowasure availability checker."""

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from miyakowasure_check.config import Config
from miyakowasure_check.models import RoomType
from miyakowasure_check.notifier import NtfyNotifier
from miyakowasure_check.scraper import check_availability
from miyakowasure_check.state import NotificationState

app = typer.Typer(
    name="miyakowasure-check",
    help="Monitor room availability at Natsuse Onsen Miyakowasure ryokan.",
    no_args_is_help=True,
)
console = Console()


def parse_room_type(value: str) -> RoomType | None:
    """Parse room type from string."""
    return RoomType.from_string(value)


def log(message: str) -> None:
    """Log a timestamped message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[dim]{timestamp}[/dim] {message}")


async def run_check_loop(config: Config) -> None:
    """Main check loop."""
    state = NotificationState(state_file=config.state_file)
    state.load()

    notifier = NtfyNotifier(config.ntfy_topic) if config.ntfy_topic else None

    log(f"Starting availability checker for {config.check_in_date} ({config.nights} night(s))")
    log(f"Checking rooms: {', '.join(r.display_name for r in config.rooms_to_check)}")
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

        result = await check_availability(config)

        if result.error:
            log(f"[red]Error: {result.error}[/red]")
        else:
            available = result.available_rooms
            if available:
                log(f"[green]Found {len(available)} available room(s)![/green]")
                for room in available:
                    log(f"  - {room.room_type.display_name}")
                    if room.price_per_person:
                        log(f"    Price: ¥{room.price_per_person:,}/person")
                    if room.spots_left:
                        log(f"    Spots left: {room.spots_left}")

                    if notifier and state.should_notify(room):
                        success = await notifier.send(room)
                        if success:
                            state.mark_notified(room)
                            log(f"    [green]Notification sent![/green]")
                        else:
                            log(f"    [red]Failed to send notification[/red]")
                    elif notifier:
                        log(f"    [dim]Already notified within 24h[/dim]")
            else:
                log("[dim]No rooms available[/dim]")

            table = Table(title="Room Status", show_header=True)
            table.add_column("Room")
            table.add_column("Status")
            table.add_column("Price")
            for room in result.rooms_checked:
                status = "[green]Available[/green]" if room.available else "[red]Unavailable[/red]"
                price = f"¥{room.price_per_person:,}" if room.price_per_person else "-"
                table.add_row(room.room_type.display_name, status, price)
            console.print(table)

        log(f"Next check in {config.check_interval_minutes} minutes...")
        await asyncio.sleep(config.check_interval_minutes * 60)


@app.command()
def check(
    check_date: Annotated[
        str,
        typer.Option(
            "--date", "-d",
            help="Check-in date (YYYY-MM-DD)",
        ),
    ],
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
            help="Room type filter (e.g., sakura, momiji-vip, tsubaki-view). Can be specified multiple times.",
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
    state_file: Annotated[
        Path | None,
        typer.Option(
            "--state-file",
            help="Path to state file for tracking notifications",
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
    """Check room availability at Miyakowasure ryokan."""
    try:
        check_in_date = date.fromisoformat(check_date)
    except ValueError:
        console.print(f"[red]Invalid date format: {check_date}. Use YYYY-MM-DD[/red]")
        raise typer.Exit(1)

    room_filter: list[RoomType] = []
    if room:
        parsed = RoomType.from_string(room)
        if parsed:
            room_filter.append(parsed)
        else:
            console.print(f"[red]Unknown room type: {room}[/red]")
            console.print("Valid options: sakura, momiji, momiji-vip, momiji-twin, tsubaki, tsubaki-view")
            raise typer.Exit(1)

    try:
        config = Config(
            check_in_date=check_in_date,
            nights=nights,
            guests=guests,
            room_filter=room_filter,
            check_interval_minutes=interval,
            ntfy_topic=ntfy_topic,
            state_file=state_file or Path.home() / ".miyakowasure-state.json",
            headless=headless,
        )
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)

    if once:
        result = asyncio.run(_single_check(config))
        raise typer.Exit(0 if not result.error else 1)
    else:
        try:
            asyncio.run(run_check_loop(config))
        except KeyboardInterrupt:
            log("Shutting down...")
            raise typer.Exit(0)


async def _single_check(config: Config) -> "CheckResult":
    """Run a single availability check."""
    from miyakowasure_check.models import CheckResult

    log(f"Single check for {config.check_in_date} ({config.nights} night(s))")

    result = await check_availability(config)

    if result.error:
        log(f"[red]Error: {result.error}[/red]")
    else:
        table = Table(title="Room Availability", show_header=True)
        table.add_column("Room")
        table.add_column("Status")
        table.add_column("Price")
        for room in result.rooms_checked:
            status = "[green]Available[/green]" if room.available else "[red]Unavailable[/red]"
            price = f"¥{room.price_per_person:,}" if room.price_per_person else "-"
            table.add_row(room.room_type.display_name, status, price)
        console.print(table)

    return result


@app.command()
def rooms() -> None:
    """List all available room types and their details."""
    table = Table(title="Miyakowasure Room Types", show_header=True)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Max Guests")
    table.add_column("Base Price")

    for room_type in RoomType:
        table.add_row(
            room_type.value,
            room_type.display_name,
            str(room_type.max_guests),
            f"¥{room_type.max_guests * 19500:,}~",
        )

    console.print(table)
    console.print("\n[dim]Use --room flag with: sakura, momiji, momiji-vip, momiji-twin, tsubaki, tsubaki-view[/dim]")


if __name__ == "__main__":
    app()
