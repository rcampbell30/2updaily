"""Seed fixtures_today.csv from the May fixture bank.

This keeps the homepage populated with a rolling shortlist even when no paid
live-fixtures API key is configured. It selects the next three upcoming banked
fixtures from data/fixture_bank_may_2026.csv and writes them in the format used
by the report generator.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_BANK_PATH = ROOT / "data" / "fixture_bank_may_2026.csv"
FIXTURES_TODAY_PATH = ROOT / "fixtures_today.csv"
MAX_FIXTURES = 3

OUTPUT_FIELDS = [
    "home_team",
    "away_team",
    "league",
    "kickoff_uk",
    "favourite",
    "favourite_odds",
]


def load_upcoming_bank_rows() -> list[dict[str, str]]:
    if not FIXTURE_BANK_PATH.exists():
        return []

    today = date.today().isoformat()
    rows: list[dict[str, str]] = []

    with FIXTURE_BANK_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            match_date = row.get("date", "").strip()
            if match_date and match_date >= today:
                rows.append(row)

    rows.sort(key=lambda row: (row.get("date", ""), row.get("kickoff_uk", "")))
    return rows[:MAX_FIXTURES]


def to_report_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "home_team": row.get("home_team", "").strip(),
        "away_team": row.get("away_team", "").strip(),
        "league": row.get("league", "").strip(),
        "kickoff_uk": row.get("kickoff_uk", "").strip(),
        "favourite": row.get("provisional_favourite", "").strip(),
        "favourite_odds": row.get("favourite_odds", "").strip(),
    }


def main() -> None:
    rows = [to_report_row(row) for row in load_upcoming_bank_rows()]

    if not rows:
        print("No upcoming fixture-bank rows found; fixtures_today.csv was not changed.")
        return

    with FIXTURES_TODAY_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Seeded fixtures_today.csv with {len(rows)} upcoming fixture-bank rows.")


if __name__ == "__main__":
    main()
