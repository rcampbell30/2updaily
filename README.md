# 2upDaily

2upDaily is a small Python narrow-agent project for producing a daily 2up matched-betting research shortlist.

It can now run in two modes:

1. **Local CSV mode** — you manually edit `fixtures_today.csv` and `team_stats.csv`, then run the scorer locally.
2. **GitHub Actions live-fixture mode** — GitHub Actions fetches today's football fixtures from API-Football, writes `fixtures_today.csv`, generates the daily report, and builds a static page in `docs/`.

This is a shortlist/research tool only. It does not place bets, guarantee profit, check bookmaker 2up eligibility, or replace bankroll discipline.

## Quick local run

```powershell
python run_twoup_from_split_csv.py
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
Fetch live fixtures
↓
Overwrite fixtures_today.csv
↓
Run the 2up scorer
↓
Generate reports/daily_report.md
↓
Archive reports/archive/YYYY-MM-DD.md
↓
Generate docs/index.html and docs/data/today.json
↓
Commit the generated files back to the repo
```

## Required GitHub secret

Live fixture fetching requires an API-Football key.

Add this repository secret:

```text
API_FOOTBALL_KEY
```

GitHub path:

```text
Repo → Settings → Secrets and variables → Actions → New repository secret
```

Without this secret, the live-fixture step will fail.

## Optional GitHub variable

You can optionally restrict API-Football to specific league IDs by adding an Actions variable:

```text
API_FOOTBALL_LEAGUE_IDS
```

Example value:

```text
39,40,140,135,78,61,98,88,94
```

If this variable is omitted, the script fetches all fixtures for the day and filters locally by league keywords.

## Files to edit

- `team_stats.csv` - update this weekly with team-level stats.
- `fixtures_today.csv` - normally generated daily by GitHub Actions, but you can still edit it manually.

## Main files

- `twoup_agents.py` - the narrow-agent 2up research/scoring module.
- `run_twoup_from_split_csv.py` - the CSV runner.
- `scripts/fetch_live_fixtures.py` - fetches live fixtures from API-Football.
- `scripts/generate_daily_report.py` - generates reports and static site files.
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

## Important current limitation

The live-fixture script fetches fixtures, not odds. Until odds automation is added, `favourite_odds` is left blank and the scorer allows the fixture through while lowering confidence.

The favourite is inferred from existing `team_stats.csv` data where possible. If neither team has stats, the script uses the home team as a placeholder and the report will show low data quality.
