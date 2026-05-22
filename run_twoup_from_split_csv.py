"""Run the 2up research pipeline from two CSV files.

Expected files in this same folder:
- team_stats.csv
- fixtures_today.csv

Blank values are allowed for harder-to-source fields such as:
- first_half_goals_avg
- conceded_after_leading_rate
- favourite_odds

If fixtures contain teams not yet present in team_stats.csv, the runner creates
empty TeamStats objects for them instead of crashing. That keeps the daily site
generation alive while clearly reducing data quality in the report.
"""

import csv
from pathlib import Path
from typing import Dict, Optional

from twoup_agents import TeamStats, Fixture, TwoUpResearchPipeline


BASE_DIR = Path(__file__).resolve().parent
TEAM_STATS_PATH = BASE_DIR / "team_stats.csv"
FIXTURES_PATH = BASE_DIR / "fixtures_today.csv"


BLANK_VALUES = {"", "na", "n/a", "none", "null", "-", "unknown"}


def normalise_team_name(name: str) -> str:
    return name.strip().lower()


def parse_float(value: str) -> Optional[float]:
    if value is None:
        return None

    cleaned = str(value).strip().lower()
    if cleaned in BLANK_VALUES:
        return None

    try:
        return float(cleaned)
    except ValueError as error:
        raise ValueError(f"Could not parse '{value}' as a number.") from error


def load_team_stats(path: Path) -> Dict[str, TeamStats]:
    stats_by_team: Dict[str, TeamStats] = {}

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            team_name = row["team"].strip()
            stats = TeamStats(
                name=team_name,
                goals_for_avg=parse_float(row.get("goals_for_avg", "")),
                goals_against_avg=parse_float(row.get("goals_against_avg", "")),
                first_half_goals_avg=parse_float(row.get("first_half_goals_avg", "")),
                clean_sheet_rate=parse_float(row.get("clean_sheet_rate", "")),
                conceded_after_leading_rate=parse_float(row.get("conceded_after_leading_rate", "")),
                over_25_rate=parse_float(row.get("over_25_rate", "")),
            )
            stats_by_team[normalise_team_name(team_name)] = stats

    return stats_by_team


def require_team_stats(stats_by_team: Dict[str, TeamStats], team_name: str) -> TeamStats:
    key = normalise_team_name(team_name)
    if key not in stats_by_team:
        return TeamStats(name=team_name)
    return stats_by_team[key]


def load_fixtures(path: Path, stats_by_team: Dict[str, TeamStats]) -> list[Fixture]:
    fixtures: list[Fixture] = []

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            home_team = row["home_team"].strip()
            away_team = row["away_team"].strip()
            favourite = row["favourite"].strip()

            fixture = Fixture(
                home_team=home_team,
                away_team=away_team,
                league=row["league"].strip(),
                kickoff_uk=row["kickoff_uk"].strip(),
                favourite=favourite,
                favourite_odds=parse_float(row.get("favourite_odds", "")),
                home_stats=require_team_stats(stats_by_team, home_team),
                away_stats=require_team_stats(stats_by_team, away_team),
                source_notes=row.get("source_notes", "").strip(),
            )
            fixtures.append(fixture)

    return fixtures


def main() -> None:
    stats_by_team = load_team_stats(TEAM_STATS_PATH)
    fixtures = load_fixtures(FIXTURES_PATH, stats_by_team)

    pipeline = TwoUpResearchPipeline()
    report = pipeline.run(fixtures)
    print(report)


if __name__ == "__main__":
    main()
