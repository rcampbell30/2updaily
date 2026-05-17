"""Fetch live football fixtures for today's 2upDaily run.

Provider: API-Football / API-Sports

Required GitHub secret:
- API_FOOTBALL_KEY

Optional environment variables:
- API_FOOTBALL_LEAGUE_IDS: comma-separated league IDs to fetch individually.
  If omitted, the script fetches all fixtures for the date and filters locally.
- LIVE_FIXTURE_DATE: YYYY-MM-DD override for testing. Defaults to today's
  Europe/London date.

Output:
- fixtures_today.csv

Notes:
- This fetches fixtures, not bookmaker odds.
- favourite_odds is left blank until odds automation is added.
- favourite is inferred from team_stats.csv when possible; otherwise the home
  team is used as a safe placeholder and confidence will be reduced downstream.
"""

from __future__ import annotations

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

import requests


ROOT = Path(__file__).resolve().parents[1]
TEAM_STATS_PATH = ROOT / "team_stats.csv"
FIXTURES_PATH = ROOT / "fixtures_today.csv"
API_BASE_URL = "https://v3.football.api-sports.io/fixtures"
LONDON_TZ = ZoneInfo("Europe/London")

ALLOWED_LEAGUE_KEYWORDS = [
    "Premier League",
    "Championship",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Champions League",
    "Europa League",
    "Conference League",
    "Eredivisie",
    "Primeira Liga",
    "J1 League",
    "J2 League",
    "J-League",
    "Japan",
    "A-League",
    "Australia",
]

TEAM_STATS_FIELDS = [
    "team",
    "goals_for_avg",
    "goals_against_avg",
    "first_half_goals_avg",
    "clean_sheet_rate",
    "conceded_after_leading_rate",
    "over_25_rate",
]

FIXTURE_FIELDS = [
    "home_team",
    "away_team",
    "league",
    "kickoff_uk",
    "favourite",
    "favourite_odds",
]


def normalise(value: str) -> str:
    return value.strip().lower()


def parse_float(value: str | None) -> Optional[float]:
    if value is None:
        return None
    cleaned = str(value).strip().lower()
    if cleaned in {"", "na", "n/a", "none", "null", "-", "unknown"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def load_team_stats_rows() -> list[dict[str, str]]:
    if not TEAM_STATS_PATH.exists():
        return []

    with TEAM_STATS_PATH.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [{field: row.get(field, "") for field in TEAM_STATS_FIELDS} for row in reader]


def save_team_stats_rows(rows: list[dict[str, str]]) -> None:
    with TEAM_STATS_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=TEAM_STATS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def stats_rating(row: dict[str, str] | None, home_bonus: float = 0.0) -> Optional[float]:
    if row is None:
        return None

    goals_for = parse_float(row.get("goals_for_avg"))
    goals_against = parse_float(row.get("goals_against_avg"))
    over_25 = parse_float(row.get("over_25_rate"))
    clean_sheet = parse_float(row.get("clean_sheet_rate"))

    if goals_for is None and goals_against is None:
        return None

    rating = home_bonus
    if goals_for is not None:
        rating += goals_for
    if goals_against is not None:
        rating -= goals_against * 0.65
    if over_25 is not None:
        rating += over_25 * 0.25
    if clean_sheet is not None:
        rating += clean_sheet * 0.2

    return rating


def infer_favourite(home_team: str, away_team: str, stats_by_team: dict[str, dict[str, str]]) -> str:
    home_stats = stats_by_team.get(normalise(home_team))
    away_stats = stats_by_team.get(normalise(away_team))

    home_rating = stats_rating(home_stats, home_bonus=0.15)
    away_rating = stats_rating(away_stats, home_bonus=0.0)

    if home_rating is None and away_rating is None:
        return home_team
    if away_rating is None:
        return home_team
    if home_rating is None:
        return away_team

    return home_team if home_rating >= away_rating else away_team


def is_allowed_league(league_name: str, country_name: str) -> bool:
    haystack = f"{league_name} {country_name}".lower()
    return any(keyword.lower() in haystack for keyword in ALLOWED_LEAGUE_KEYWORDS)


def fixture_kickoff_uk(fixture_date: str) -> str:
    # API-Football returns ISO 8601 timestamps, usually with +00:00.
    kickoff = datetime.fromisoformat(fixture_date.replace("Z", "+00:00"))
    return kickoff.astimezone(LONDON_TZ).strftime("%H:%M")


def fetch_api_football(api_key: str, target_date: str, league_ids: Iterable[str]) -> list[dict]:
    headers = {"x-apisports-key": api_key}
    base_params = {"date": target_date, "timezone": "Europe/London"}

    fixtures: list[dict] = []
    if league_ids:
        for league_id in league_ids:
            params = {**base_params, "league": league_id.strip()}
            response = requests.get(API_BASE_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            fixtures.extend(response.json().get("response", []))
    else:
        response = requests.get(API_BASE_URL, headers=headers, params=base_params, timeout=30)
        response.raise_for_status()
        fixtures.extend(response.json().get("response", []))

    return fixtures


def convert_fixtures(raw_fixtures: list[dict], stats_by_team: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    for item in raw_fixtures:
        league = item.get("league", {})
        teams = item.get("teams", {})
        fixture = item.get("fixture", {})
        status = fixture.get("status", {})

        league_name = league.get("name", "").strip()
        country_name = league.get("country", "").strip()

        if not is_allowed_league(league_name, country_name):
            continue

        status_short = status.get("short", "")
        if status_short not in {"NS", "TBD"}:
            # Keep only not-started fixtures for the daily shortlist.
            continue

        home_team = teams.get("home", {}).get("name", "").strip()
        away_team = teams.get("away", {}).get("name", "").strip()
        fixture_date = fixture.get("date", "")

        if not home_team or not away_team or not fixture_date:
            continue

        kickoff_uk = fixture_kickoff_uk(fixture_date)
        favourite = infer_favourite(home_team, away_team, stats_by_team)
        key = (home_team, away_team, league_name, kickoff_uk)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        rows.append(
            {
                "home_team": home_team,
                "away_team": away_team,
                "league": league_name,
                "kickoff_uk": kickoff_uk,
                "favourite": favourite,
                "favourite_odds": "",
            }
        )

    return sorted(rows, key=lambda row: (row["kickoff_uk"], row["league"], row["home_team"]))


def save_fixtures(rows: list[dict[str, str]]) -> None:
    with FIXTURES_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIXTURE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def ensure_team_stats_rows(existing_rows: list[dict[str, str]], fixture_rows: list[dict[str, str]]) -> None:
    known = {normalise(row["team"]) for row in existing_rows}
    added = False

    for fixture in fixture_rows:
        for team_name in [fixture["home_team"], fixture["away_team"]]:
            key = normalise(team_name)
            if key in known:
                continue
            existing_rows.append(
                {
                    "team": team_name,
                    "goals_for_avg": "",
                    "goals_against_avg": "",
                    "first_half_goals_avg": "",
                    "clean_sheet_rate": "",
                    "conceded_after_leading_rate": "",
                    "over_25_rate": "",
                }
            )
            known.add(key)
            added = True

    if added:
        save_team_stats_rows(existing_rows)


def main() -> int:
    api_key = os.getenv("API_FOOTBALL_KEY") or os.getenv("API_SPORTS_KEY")
    if not api_key:
        print("Missing API_FOOTBALL_KEY secret. Add it in GitHub repo Settings → Secrets and variables → Actions.")
        return 1

    target_date = os.getenv("LIVE_FIXTURE_DATE") or datetime.now(LONDON_TZ).date().isoformat()
    league_ids_raw = os.getenv("API_FOOTBALL_LEAGUE_IDS", "")
    league_ids = [item.strip() for item in league_ids_raw.split(",") if item.strip()]

    existing_team_rows = load_team_stats_rows()
    stats_by_team = {normalise(row["team"]): row for row in existing_team_rows}

    raw_fixtures = fetch_api_football(api_key=api_key, target_date=target_date, league_ids=league_ids)
    fixture_rows = convert_fixtures(raw_fixtures, stats_by_team)

    save_fixtures(fixture_rows)
    ensure_team_stats_rows(existing_team_rows, fixture_rows)

    print(f"Fetched {len(raw_fixtures)} raw fixtures for {target_date}.")
    print(f"Wrote {len(fixture_rows)} allowed not-started fixtures to fixtures_today.csv.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
