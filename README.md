# 2upDaily

2upDaily is a small Python narrow-agent project for producing a 2UP early-payout matched-betting research shortlist.

It uses a **ChatGPT-maintained fixture bank** plus semi-static **team baseline CSVs** as the source of truth. The intended workflow is manual: Rory asks ChatGPT to read `AGENT_CONTEXT.md`, then ChatGPT uses that file plus the current repo state to research/update the shortlist when requested.

This is a shortlist/research tool only. It does not place bets, guarantee profit, check bookmaker 2UP eligibility, or replace bankroll discipline.

## Manual agent workflow

Read these files first when running a future update:

```text
AGENT_CONTEXT.md
data/user_defaults.md
```

`AGENT_CONTEXT.md` contains the strategy, ranking rules, baseline-data rules, human-layer checks, qualifying-loss logic, and preferred final-answer format.

`data/user_defaults.md` contains Rory-specific operational defaults such as the current default exchange commission. As of 2026-05-24, Rory's default commission is **2%**, so live-position QL should use 2% as the headline value unless Rory says otherwise.

The workflow is:

```text
Read AGENT_CONTEXT.md
↓
Read data/user_defaults.md
↓
Inspect the current fixture bank
↓
Inspect relevant team baseline CSVs
↓
Research current/next fixtures when asked
↓
Update the ranked fixture bank
↓
Seed fixtures_today.csv
↓
Generate reports and static site files
↓
Commit the update
```

## Live managed positions

Watchlist candidates and real placed positions are separate.

Use these files for live managed positions:

```text
docs/live-bets.html
docs/data/live-bets.json
data/results_tracker.csv
```

Live-position notes should avoid bookmaker/account names and account-sensitive details. Store only the useful trading data: back stake, back odds, lay odds, lay stake/liability at 2% commission, headline QL at 2%, free-bet/reload value if relevant, 2UP trigger status, and settlement status.

## Baseline team data

Semi-static team baselines live here:

```text
data/team_baselines/
```

Current baseline files:

- `data/team_baselines/premier_league_2025_26.csv` - richer Premier League baseline.
- `data/team_baselines/a_league_men_2025_26.csv` - richer A-League Men baseline.
- `data/team_baselines/additional_leagues_compact_2025_26.csv` - compact Championship, LaLiga, Serie A, Scottish Premiership, and Eredivisie baseline.
- `data/team_baselines/bundesliga_dfb_pokal_finalists_2025_26.csv` - compact Bayern/Stuttgart DFB-Pokal final baseline.

These files are intended to be refreshed every 3 to 6 months. They give the stable football layer: scoring, conceding, BTTS/over-goals profile, clean sheets, failed-to-score rate, and 2UP role classification.

Daily/manual checks still need the human layer: 2UP availability, current bookmaker back price, exchange lay price, exchange liquidity, commission, stake limits, restrictions, and exact qualifying loss.

## Quick local run

```powershell
python run_twoup_from_split_csv.py
```

## Generate the report locally

```powershell
python scripts/seed_fixtures_today_from_bank.py
python scripts/generate_daily_report.py
python scripts/inject_daily_pick_calendar.py
```

## GitHub Action

The workflow lives at:

```text
.github/workflows/daily-report.yml
```

It no longer has a scheduled cron. It runs on pushes to `main` and can also be triggered manually from:

```text
GitHub repo → Actions → Generate 2up report → Run workflow
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

- `AGENT_CONTEXT.md` - source-of-truth prompt/context for future ChatGPT-assisted runs.
- `data/user_defaults.md` - Rory-specific defaults such as exchange commission and live-position conventions.
- `data/fixture_bank_may_2026.csv` - current fixture bank and ranking source.
- `data/team_baselines/` - semi-static league/team baseline data refreshed every 3 to 6 months.
- `team_stats.csv` - simple scorer-compatible stats template.
- `fixtures_today.csv` - generated from the fixture bank, but can still be edited manually if needed.
- `docs/data/live-bets.json` - live managed positions supplied by Rory.
- `docs/live-bets.html` - static live-position dashboard.

## Main files

- `AGENT_CONTEXT.md` - manual agent prompt/context.
- `data/user_defaults.md` - operational defaults for future runs.
- `twoup_agents.py` - the narrow-agent 2UP research/scoring module.
- `run_twoup_from_split_csv.py` - the CSV runner.
- `scripts/seed_fixtures_today_from_bank.py` - seeds `fixtures_today.csv` from the fixture bank.
- `scripts/generate_daily_report.py` - generates reports and static site files.
- `scripts/inject_daily_pick_calendar.py` - adds the fixture-bank calendar to the dashboard.
- `.github/workflows/daily-report.yml` - push/manual report-generation workflow.
- `team_stats.csv` - current simple team stats template.
- `fixtures_today.csv` - current generated fixture file.
- `DATA_GUIDE.md` - explains the CSV data workflow.

## Static site output

The generated static site files live here:

```text
docs/
├── index.html
├── tracker.html
├── live-bets.html
└── data/
    ├── today.json
    ├── results.json
    └── live-bets.json
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

The fixture bank and baseline files can record public fixture research and user-confirmed back/lay notes, but private account checks still need the human layer: 2UP eligibility, live bookie price, live exchange lay price, liquidity, restrictions, commission, stake limits, and exact qualifying loss.
