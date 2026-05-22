"""Seed fixtures_today.csv from the fixture bank.

Selects the best upcoming rows from data/fixture_bank_may_2026.csv and writes
fixtures_today.csv for the report generator. If shortlist_rank exists, lower
rank numbers are preferred before plain chronological order.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_BANK_PATH = ROOT / "data" / "fixture_bank_may_2026.csv"
FIXTURES_TODAY_PATH = ROOT / "fixtures_today.csv"
LONDON_TZ = ZoneInfo("Europe/London")
MAX_FIXTURES = 3

OUTPUT_FIELDS = [
    "home_team",
    "away_team",
    "league",
    "kickoff_uk",
    "favourite",
    "favourite_odds",
    "source_notes",
]


def now_london() -> datetime:
    return datetime.now(LONDON_TZ)


def human_date(iso_date: str) -> str:
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return iso_date
    return parsed.strftime("%A %d %B %Y")


def parse_match_datetime(row: dict[str, str]) -> datetime | None:
    match_date = row.get("date", "").strip()
    kickoff = row.get("kickoff_uk", "").strip()
    if not match_date or not kickoff:
        return None

    try:
        parsed = datetime.strptime(f"{match_date} {kickoff}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None

    return parsed.replace(tzinfo=LONDON_TZ)


def rank_value(row: dict[str, str]) -> int:
    raw_rank = row.get("shortlist_rank", "").strip()
    if not raw_rank:
        return 999

    try:
        return int(raw_rank)
    except ValueError:
        return 999


def format_dashboard_kickoff(row: dict[str, str]) -> str:
    match_date = row.get("date", "").strip()
    kickoff = row.get("kickoff_uk", "").strip()

    if match_date and kickoff:
        return f"{human_date(match_date)}, {kickoff} UK"
    if match_date:
        return f"{human_date(match_date)}, time TBC"
    return kickoff


def load_upcoming_bank_rows() -> list[dict[str, str]]:
    if not FIXTURE_BANK_PATH.exists():
        return []

    now = now_london()
    rows: list[dict[str, str]] = []

    with FIXTURE_BANK_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            match_datetime = parse_match_datetime(row)
            if match_datetime is not None:
                if match_datetime >= now:
                    rows.append(row)
                continue

            match_date = row.get("date", "").strip()
            if match_date and match_date >= now.date().isoformat():
                rows.append(row)

    rows.sort(
        key=lambda row: (
            rank_value(row),
            row.get("date", ""),
            row.get("kickoff_uk", ""),
        )
    )
    return rows[:MAX_FIXTURES]


def to_report_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "home_team": row.get("home_team", "").strip(),
        "away_team": row.get("away_team", "").strip(),
        "league": row.get("league", "").strip(),
        "kickoff_uk": format_dashboard_kickoff(row),
        "favourite": row.get("provisional_favourite", "").strip(),
        "favourite_odds": row.get("favourite_odds", "").strip(),
        "source_notes": row.get("source_notes", "").strip(),
    }


def write_fixtures(rows: list[dict[str, str]]) -> None:
    with FIXTURES_TODAY_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = [to_report_row(row) for row in load_upcoming_bank_rows()]
    write_fixtures(rows)

    if rows:
        print(f"Seeded fixtures_today.csv with {len(rows)} fixture-bank rows.")
    else:
        print("No upcoming fixture-bank rows found; wrote empty fixtures_today.csv.")


if __name__ == "__main__":
    main()
