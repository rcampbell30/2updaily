# 2upDaily Data Guide

This project works best when the football data is split into two update rhythms:

- `team_stats.csv` — update weekly.
- `fixtures_today.csv` — update daily.

The tool is designed to be useful before full live-data automation. The goal is to keep the data collection simple, repeatable, and easy to audit.

## Daily file: fixtures_today.csv

Use this file for the matches you want to assess today.

Required columns:

```csv
home_team,away_team,league,kickoff_uk,favourite,favourite_odds
```

Example:

```csv
Kawasaki Frontale,Machida Zelvia,J1 League,11:00,Machida Zelvia,2.20
```

### Daily fields

| Field | Meaning |
|---|---|
| `home_team` | Home team name |
| `away_team` | Away team name |
| `league` | Competition name |
| `kickoff_uk` | UK kick-off time |
| `favourite` | Team with shortest win odds |
| `favourite_odds` | Decimal odds |

The `favourite` must match either `home_team` or `away_team`. Spelling matters.

## Weekly file: team_stats.csv

Use this file for team-level stats. A weekly update is enough for the prototype because these stats are slow-changing.

Required columns:

```csv
team,goals_for_avg,goals_against_avg,first_half_goals_avg,clean_sheet_rate,conceded_after_leading_rate,over_25_rate
```

Example:

```csv
Machida Zelvia,1.63,1.00,,0.38,,0.50
```

Blank values are allowed for hard-to-source fields.

## What can be blank?

These are hard to find from free public pages and can be left blank:

- `first_half_goals_avg`
- `conceded_after_leading_rate`

The tool will skip blank values and reduce confidence if too much data is missing.

Blank values accepted by the runner:

- empty cell
- `na`
- `n/a`
- `none`
- `null`
- `-`

## What matters most for 2up?

The strongest profile is a volatile favourite:

1. The favourite can score enough to go two goals up.
2. The opponent concedes regularly.
3. The match has goal volatility.
4. The favourite is not so defensively controlled that comeback risk disappears.

For the current scoring model, the most useful fields are:

- `goals_for_avg`
- `goals_against_avg`
- `clean_sheet_rate`
- `over_25_rate`

The best advanced fields to add later are:

- `first_half_goals_avg`
- `conceded_after_leading_rate`

## Good manual workflow

1. Update `team_stats.csv` once a week.
2. Add today’s fixtures into `fixtures_today.csv` each morning.
3. Run:

```powershell
python run_twoup_from_split_csv.py
```

4. Compare the shortlist with Discord/bookmaker 2up availability.
5. Treat the output as research, not as a guaranteed pick.

## Future automation plan

A later version can add separate agents:

- `FixtureDiscoveryAgent`
- `OddsAgent`
- `StatsBuilderAgent`
- `TimelineAgent`
- `PromoAvailabilityAgent`

The current version deliberately stays offline and CSV-driven so the scoring logic can be tested before adding API complexity.
