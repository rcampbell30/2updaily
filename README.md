# 2up Agents - Complete Replacement Pack

This is the current all-in-one version of the 2up research helper.

You can replace your old folder with this folder, then run:

```powershell
python run_twoup_from_split_csv.py
```

## Files to edit

- `team_stats.csv` - update this weekly with team-level stats.
- `fixtures_today.csv` - update this daily with the fixtures you want to assess.

## Main files

- `twoup_agents.py` - the narrow-agent 2up research/scoring module.
- `run_twoup_from_split_csv.py` - the CSV runner.
- `team_stats.csv` - current simple team stats template.
- `fixtures_today.csv` - current simple fixture template.
- `test_output.txt` - example output from the current version.

## Examples folder

The `examples` folder contains fuller sample CSVs with a `notes` column:

- `examples/team_stats_with_notes_example.csv`
- `examples/fixtures_today_with_notes_example.csv`

The runner ignores extra columns like `notes`, so you can keep notes in your CSV if you want.

## Optional/missing data

These harder-to-source fields can be left blank:

- `first_half_goals_avg`
- `conceded_after_leading_rate`

Blank cells are treated as missing. These also count as blank:

- `na`
- `n/a`
- `none`
- `null`
- `-`

The module will skip missing values instead of crashing and will print data-quality notes when confidence is reduced.

## Important

This is a shortlist/research tool only. It does not guarantee profit, place bets, check whether a bookmaker's 2up offer applies, or replace bankroll discipline.
