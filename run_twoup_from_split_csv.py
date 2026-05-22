"""Run the 2up research pipeline from CSV files.

Expected files:
- team_stats.csv
- fixtures_today.csv
- data/team_baselines/*.csv

The runner now loads the small scorer-compatible `team_stats.csv` first, then
merges in the richer/compact baseline files from `data/team_baselines/`. That
means the daily scorer can use the semi-static baseline layer directly instead
of only showing it in source notes.

Blank values are allowed for harder-to-source fields such as:
- first_half_goals_avg
- first_half_goals_for_avg
- conceded_after_leading_rate
- favourite_odds

If fixtures contain teams not yet present in either team_stats.csv or the
baseline files, the runner creates empty TeamStats objects for them instead of
crashing. That keeps the daily site generation alive while clearly reducing data
quality in the report.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, Optional

from twoup_agents import TeamStats, Fixture, TwoUpResearchPipeline


BASE_DIR = Path(__file__).resolve().parent
TEAM_STATS_PATH = BASE_DIR / "team_stats.csv"
TEAM_BASELINES_DIR = BASE_DIR / "data" / "team_baselines"
FIXTURES_PATH = BASE_DIR / "fixtures_today.csv"


BLANK_VALUES = {"", "na", "n/a", "none", "null", "-", "unknown"}

# Fixture sources and stats sources do not always use the exact same club names.
# Keep this deliberately small and obvious: only aliases that already appear in
# current fixture-bank/baseline data should live here.
TEAM_NAME_ALIASES = {
    "brighton & hove albion": "brighton",
    "brighton and hove albion": "brighton",
    "tottenham hotspur": "tottenham",
    "spurs": "tottenham",
    "wolverhampton wanderers": "wolverhampton",
    "wolves": "wolverhampton",
    "man utd": "manchester united",
    "man united": "manchester united",
    "man city": "manchester city",
    "newcastle": "newcastle united",
    "west ham": "west ham united",
    "leeds": "leeds united",
    "nottingham forest fc": "nottingham forest",
}


def normalise_team_name(name: str) -> str:
    cleaned = " ".join(name.strip().lower().replace(".", "").split())
    return TEAM_NAME_ALIASES.get(cleaned, cleaned)


def parse_float(value: str | None) -> Optional[float]:
    if value is None:
        return None

    cleaned = str(value).strip().lower()
    if cleaned in BLANK_VALUES:
        return None

    try:
        return float(cleaned)
    except ValueError as error:
        raise ValueError(f"Could not parse '{value}' as a number.") from error


def first_present(row: dict[str, str], field_names: Iterable[str]) -> str:
    for field_name in field_names:
        value = row.get(field_name, "")
        if str(value).strip().lower() not in BLANK_VALUES:
            return value
    return ""


def row_to_team_stats(row: dict[str, str]) -> TeamStats:
    team_name = row["team"].strip()
    return TeamStats(
        name=team_name,
        goals_for_avg=parse_float(row.get("goals_for_avg", "")),
        goals_against_avg=parse_float(row.get("goals_against_avg", "")),
        first_half_goals_avg=parse_float(
            first_present(row, ["first_half_goals_avg", "first_half_goals_for_avg"])
        ),
        clean_sheet_rate=parse_float(row.get("clean_sheet_rate", "")),
        conceded_after_leading_rate=parse_float(row.get("conceded_after_leading_rate", "")),
        over_25_rate=parse_float(row.get("over_25_rate", "")),
    )


def load_team_stats(path: Path) -> Dict[str, TeamStats]:
    stats_by_team: Dict[str, TeamStats] = {}

    if not path.exists():
        return stats_by_team

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            stats = row_to_team_stats(row)
            stats_by_team[normalise_team_name(stats.name)] = stats

    return stats_by_team


def load_baseline_stats(directory: Path) -> Dict[str, TeamStats]:
    stats_by_team: Dict[str, TeamStats] = {}

    if not directory.exists():
        return stats_by_team

    for path in sorted(directory.glob("*.csv")):
        stats_by_team.update(load_team_stats(path))

    return stats_by_team


def load_all_team_stats(
    team_stats_path: Path = TEAM_STATS_PATH,
    baselines_dir: Path = TEAM_BASELINES_DIR,
) -> Dict[str, TeamStats]:
    """Load scorer stats, then overlay semi-static team baselines.

    Baseline files intentionally overwrite duplicate teams from team_stats.csv
    because they are usually richer and more recently maintained. Teams that are
    only present in team_stats.csv, such as ad-hoc J1 rows, are preserved.
    """

    stats_by_team = load_team_stats(team_stats_path)
    stats_by_team.update(load_baseline_stats(baselines_dir))
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
    stats_by_team = load_all_team_stats()
    fixtures = load_fixtures(FIXTURES_PATH, stats_by_team)

    pipeline = TwoUpResearchPipeline()
    report = pipeline.run(fixtures)
    print(report)


if __name__ == "__main__":
    main()
