# 2upDaily Data Guide

This project works best when the football data is split into two update rhythms:

- `team_stats.csv` — update weekly or when a new team is added.
- `fixtures_today.csv` — generated daily from the fixture bank.
- `data/fixture_bank_may_2026.csv` — ChatGPT-maintained fixture research bank.

The tool is designed as a 2UP matched-betting research scanner. It does not place bets, guarantee profit, or replace checking bookmaker/exchange prices yourself before staking.

## Core 2UP matched-betting mechanic

The main target is not simply a good football pick. The main target is a tradeable 2UP setup:

1. The bookmaker has a valid 2UP/2 Goals Ahead early-payout offer on the match.
2. The team can be backed at the bookmaker.
3. The same team can be laid at close exchange odds with enough liquidity.
4. The qualifying loss is low.
5. The team has a realistic path to going two goals ahead.
6. The match still has comeback/draw volatility, so the lay side can win if the backed team fails to win after triggering 2UP.

A good football angle with bad back/lay odds is usually not a good matched-betting trade. A good odds match with no realistic 2UP trigger is also weak.

## Recommended league priority for 2UP research

League choice should be driven by offer eligibility, exchange liquidity, and back/lay closeness first.

### Tier 1 — best starting point

These are usually the best leagues/competitions to check first because they tend to have stronger bookmaker coverage, better exchange liquidity, and more reliable public data:

- Premier League
- Championship
- Champions League
- Europa League
- Conference League
- FA Cup / EFL Cup / major domestic cups when 2UP eligible
- Major playoff/final fixtures with strong liquidity

### Tier 2 — useful when odds and liquidity are good

These can be good, especially for goal volatility, but should still be checked for 2UP eligibility and exchange liquidity:

- La Liga
- Bundesliga
- Serie A
- Ligue 1
- Eredivisie
- Primeira Liga
- Scottish Premiership big matches
- Major international fixtures

### Tier 3 — possible but needs stricter checks

These can be useful when UK/European fixtures are thin, but they need careful validation because odds coverage, exchange liquidity, and 2UP eligibility may vary:

- Japan J1 / J2
- Australia A-League
- Selected high-profile cup or playoff matches outside Europe

### Usually avoid

Avoid these unless there is a very clear reason, close back/lay odds, and enough exchange liquidity:

- Tiny domestic leagues
- Youth/reserve matches
- Friendlies
- Obscure leagues with poor data
- Matches with uncertain kick-off/status
- Matches where no 2UP bookmaker eligibility can be confirmed

## Daily file: fixtures_today.csv

This file is generated from the fixture bank and should contain the top researched candidates for the current run.

Current required columns:

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
| `favourite` | Team to back for the 2UP angle |
| `favourite_odds` | Bookmaker back odds, if verified |

The `favourite` must match either `home_team` or `away_team`. Spelling matters.

Until dedicated odds columns are added, put these in `source_notes` in the fixture bank:

- 2UP bookmaker checked
- bookmaker back odds
- exchange lay odds
- rough back/lay gap
- estimated qualifying loss per £10 stake
- exchange/source checked
- uncertainty notes

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
- `favourite_odds` when back odds cannot be verified

The tool will skip blank values and reduce confidence if too much data is missing.

Blank values accepted by the runner:

- empty cell
- `na`
- `n/a`
- `none`
- `null`
- `-`

## What matters most for 2UP?

The strongest profile is a low-QL volatile favourite:

1. Back odds and lay odds are close.
2. Exchange liquidity is good enough.
3. The favourite can score enough to go two goals up.
4. The opponent concedes regularly.
5. The match has goal volatility.
6. The favourite is not so defensively controlled that comeback risk disappears.

For the current scoring model, the most useful fields are:

- bookmaker back odds
- exchange lay odds
- estimated qualifying loss
- `goals_for_avg`
- `goals_against_avg`
- `clean_sheet_rate`
- `over_25_rate`

The best advanced fields to add later are:

- `first_half_goals_avg`
- `conceded_after_leading_rate`
- exchange liquidity
- 2UP eligible bookmaker
- BTTS rate
- average first goal time

## Good daily workflow

1. Search current fixtures and shortlist only 2UP-eligible markets where possible.
2. Check bookmaker back odds and exchange lay odds.
3. Reject poor back/lay matches even if the football angle looks good.
4. Add the best researched candidates to the fixture bank.
5. Let the workflow generate `fixtures_today.csv`, reports, and the static page.
6. Before staking, manually confirm the bookmaker 2UP terms, odds, exchange price, liquidity, and bankroll exposure.

## Future automation plan

A later version can add separate agents:

- `FixtureDiscoveryAgent`
- `OddsAgent`
- `ExchangeLayAgent`
- `QualifyingLossAgent`
- `StatsBuilderAgent`
- `TimelineAgent`
- `PromoAvailabilityAgent`

The current version deliberately stays CSV-driven so the workflow can be audited before adding API complexity.