# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies (uses uv or pip)
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run a specific test file
pytest tests/test_config.py

# Run a specific test
pytest tests/test_config.py::TestConfig::test_check_out_date_calculation

# Run CLI (after installing)
ryokan-check check --date 2026-03-15 --guests 2

# Run CLI without installing
python -m ryokan_check.cli check --date 2026-03-15 --guests 2

# Install playwright browsers (required for scraping)
playwright install chromium
```

## Architecture Overview

This is a CLI tool that monitors room availability at Japanese ryokan. It supports multiple properties:
- **Miyakowasure** (Natsuse Onsen) via Yadosys booking system
- **Miyamaso Takamiya** (Zao Onsen) via 489ban.net booking system

It uses Playwright to scrape booking systems and sends notifications via ntfy.sh when rooms become available.

### Directory Structure

```
src/ryokan_check/
├── cli.py                    # Typer CLI with check/rooms commands
├── config.py                 # Multi-property configuration
├── notifier.py               # NtfyNotifier for push notifications
├── state.py                  # Per-property notification state (24h cooldown)
├── ports/                    # Interfaces (hexagonal architecture)
│   ├── room.py               # RoomInfo protocol
│   └── scraper.py            # AvailabilityScraper protocol
├── domain/
│   ├── models.py             # RoomAvailability, CheckResult
│   └── property.py           # Property enum, PropertyConfig registry
└── properties/
    ├── miyakowasure/
    │   ├── rooms.py          # MiyakowasureRoom enum (6 rooms)
    │   └── scraper.py        # YadosysScraper for Yadosys
    └── miyamaso/
        ├── rooms.py          # MiyamasoRoom enum (3 rooms with private onsen)
        └── scraper.py        # BanScraper for 489ban.net
```

### Data Flow

1. CLI parses args into `Config` with property selection
2. For each property, the appropriate scraper checks availability
3. For each available room, `NotificationState` checks 24h cooldown
4. `NtfyNotifier` sends alert with property-aware title
5. State saved to `~/.ryokan-check/{property}-state.json`

### Room Types

**Miyakowasure** (6 rooms, shared onsen):
- `sakura`, `momiji`, `momiji-vip`, `momiji-twin`, `tsubaki`, `tsubaki-view`

**Miyamaso Takamiya** (3 rooms, all with private natural hot spring bath):
- `hinakura` - HINAKURA Villa (110m2, the only real in-room onsen in Zao Onsen)
- `rian` - Both Rian Sansui variants (maisonette + japanese style)
- `rian-maisonette`, `rian-japanese` - Specific Rian Sansui variants

### CLI Examples

```bash
# Check all properties
ryokan-check check --date 2026-03-15 --once

# Check specific property
ryokan-check check --property miyamaso --date 2026-03-15 --room hinakura

# Monitor with notifications
ryokan-check check --property all --date 2026-03-15 --ntfy-topic my-topic

# List rooms for a property
ryokan-check rooms --property miyamaso
```
