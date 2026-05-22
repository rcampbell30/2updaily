# 2upDaily

2upDaily is a small Python narrow-agent project for producing a daily 2up research shortlist.

It now uses a **ChatGPT-maintained fixture bank** as the source of truth. The daily workflow seeds `fixtures_today.csv` from `data/fixture_bank_may_2026.csv`, generates the report, builds the static dashboard, and commits the generated files back to the repo.

This is a shortlist/research tool only. It does not place bets, guarantee profit, check bookmaker 2up eligibility, or replace bankroll discipline.

## Quick local run

```powershell
python run_twoup_from_split_csv.py
```

## Generate the daily report locally

```powershell
python scripts/seed_fixtures_today_from_bank.py
python scripts/generate_daily_report.py
python scripts/inject_daily_pick_calendar.py
```

## Daily GitHub Action

The workflow lives at:

```text
.github/workflows/daily-report.yml
```

It runs daily and can also be triggered manually from:

```text
GitHub repo → Actions → Generate daily 2up report → Run workflow
```

The workflow does this:

```text
Seed fixtures_today.csv from the fixture bank
↓
Run the 2up scorer
↓
Generate reports/daily_report.md
↓
Archive reports/archive/YYYY-MM-DD.md
↓
Generate docs/index.html and docs/data/today.json
↓
Inject the daily pick calendar
↓
Commit the generated files back to the repo
```

## Files to edit

- `data/fixture_bank_may_2026.csv` - main fixture bank and ranking source.
- `team_stats.csv` - update this with team-level stats when reliable data is available.
- `fixtures_today.csv` - generated from the fixture bank, but can still be edited manually if needed.

## Main files

- `twoup_agents.py` - the narrow-agent 2up research/scoring module.
- `run_twoup_from_split_csv.py` - the CSV runner.
- `scripts/seed_fixtures_today_from_bank.py` - seeds `fixtures_today.csv` from the fixture bank.
- `scripts/generate_daily_report.py` - generates reports and static site files.
- `scripts/inject_daily_pick_calendar.py` - adds the fixture-bank calendar to the dashboard.
- `.github/workflows/daily-report.yml` - scheduled daily automation.
- `team_stats.csv` - current simple team stats template.
- `fixtures_today.csv` - current daily fixture file.
- `DATA_GUIDE.md` - explains the CSV data workflow.

## Static site output

The generated static site files live here:

```text
docs/
├── index.html
└── data/
    └── today.json
```

You can publish this through GitHub Pages by setting Pages source to the `docs/` folder on `main`.

## Optional/missing data

These harder-to-source fields can be left blank:

- `first_half_goals_avg`
- `conceded_after_leading_rate`
- `favourite_odds`

Blank cells are treated as missing. These also count as blank:

- `na`
- `n/a`
- `none`
- `null`
- `-`
- `unknown`

The module will skip missing values instead of crashing and will print data-quality notes when confidence is reduced.

## Current limitation

The fixture bank can record public fixture research and user-confirmed back/lay notes, but private account checks still need the human layer: 2up eligibility, live bookie price, live exchange lay price, liquidity, restrictions, and exact qualifying loss.
