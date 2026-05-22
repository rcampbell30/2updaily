# 2upDaily Agent Context

This file is the source-of-truth prompt/context for future ChatGPT-assisted 2UP research runs.

Rory's intended workflow is manual, not cron-based:

1. Rory asks ChatGPT to read this file.
2. ChatGPT uses this file plus the current repo state as context.
3. ChatGPT researches the current/next football slate.
4. ChatGPT updates the fixture bank, generated report, and dashboard only when asked.
5. Rory stays as the human layer for account-specific checks before placing anything.

No hidden ChatGPT cron or scheduled automation should be required. The repo should carry the strategy.

## Core objective

Produce a practical 2UP early-payout matched-betting research shortlist.

This is not normal football tipping. The goal is not simply to find the team most likely to win. The goal is to find a tradeable 2UP setup where:

- a bookmaker offers 2UP / 2 Goals Ahead early payout on the match;
- the chosen team can realistically go two goals ahead;
- the same team can be laid at close enough exchange odds;
- the qualifying loss is acceptable;
- the match still has enough volatility that the lay side can win if the backed team later draws or loses after triggering 2UP.

The best 2UP candidate is often a volatile/imperfect favourite, not the safest favourite.

## Current strategic lesson

Do not over-rank ultra-short favourites just because they create tiny qualifying losses.

Example from the May 2026 update:

- Celtic at 1.20 back / 1.23 lay is a very low-QL trade, but the comeback/draw angle is weak because a two-goal lead is likely to become a routine win.
- Bayern at 1.33 back / 1.38 lay is also low QL and has better final volatility than Celtic, but still risks becoming a routine favourite win.
- Auckland FC at 2.10 back / 2.30 lay has a bigger QL, but Rory preferred it because it has a stronger 2UP shape: grand-final volatility, realistic two-goal lead potential, and better chance that the lay remains alive after a 2UP trigger.

So the ranking should balance:

1. 2UP eligibility.
2. Back/lay closeness and qualifying loss.
3. Chance of the backed team going two goals ahead.
4. Comeback/draw volatility after a possible 2UP trigger.
5. Exchange liquidity.
6. Market practicality and timing.

## Human layer

ChatGPT must not pretend to know account-specific or fast-moving facts that Rory has not provided.

Rory may need to confirm manually:

- whether his specific bookmaker/account shows 2UP on the exact fixture;
- bookmaker back price at the moment of placing;
- exchange lay price at the moment of placing;
- exchange liquidity at/near the lay price;
- exact commission;
- exact qualifying loss;
- stake limits, market suspension behaviour, cashout rules, or offer restrictions.

If a candidate is strong but missing one of those private/manual checks, keep it on the shortlist and mark it clearly as needing human confirmation.

## Qualifying-loss calculation

For a simple qualifying-loss estimate, use the standard matched-betting relation:

```text
lay_stake = back_odds * back_stake / (lay_odds - commission)
back_win_profit = (back_odds - 1) * back_stake - (lay_odds - 1) * lay_stake
lay_win_profit = lay_stake * (1 - commission) - back_stake
qualifying_loss = absolute value of the smaller/negative side
```

When commission is unknown, state assumptions clearly.

Useful shorthand for source notes:

```text
Approx QL per £10 back stake: £X before commission, £Y at 2%, £Z at 5%.
```

Do not invent commission. If unknown, show before-commission QL and flag commission as a manual check.

## League priority

Tier 1 first:

- Premier League
- Championship
- Champions League
- Europa League
- Conference League
- FA Cup / EFL Cup / major domestic cups
- high-liquidity finals/playoffs where 2UP is confirmed

Tier 2 next:

- La Liga
- Bundesliga
- Serie A
- Ligue 1
- Eredivisie
- Primeira Liga
- Scottish Premiership big matches
- major international fixtures

Tier 3 only when useful:

- Japan J1/J2
- Australia A-League
- selected high-profile cup or playoff matches outside Europe

Tier 3 can outrank Tier 1 if Rory confirms 2UP coverage, back/lay odds are workable, and the match has a better 2UP volatility shape.

Usually avoid:

- tiny domestic leagues;
- youth/reserve fixtures;
- friendlies;
- obscure markets with poor liquidity;
- uncertain kick-offs/status;
- matches where 2UP eligibility cannot be confirmed or reasonably checked.

## Team baseline data layer

The repo now has semi-static team baseline files. These are designed to be refreshed every 3 to 6 months and used as the stable football-data layer before doing any daily odds/account checks.

Baseline files currently available:

- `data/team_baselines/premier_league_2025_26.csv` - richer Premier League baseline.
- `data/team_baselines/a_league_men_2025_26.csv` - richer A-League Men baseline.
- `data/team_baselines/additional_leagues_compact_2025_26.csv` - compact baseline for Championship, LaLiga, Serie A, Scottish Premiership, and Eredivisie.

Use these files before ranking daily candidates. They help identify:

- teams that can realistically go two goals ahead;
- teams that concede enough for the lay side to stay alive;
- high BTTS / over-goals environments;
- ultra-safe favourites that may be poor 2UP value despite tiny qualifying loss;
- low-scoring teams that should usually be avoided as the back side.

Data-quality rules:

- Rich baseline files should be trusted more than compact baseline files.
- Compact rows are still useful for first-pass filtering but should not be treated as perfect.
- If a team or league is not in the baseline layer, do not invent stats. Research it or mark the data gap clearly.
- Daily live odds, 2UP eligibility, exchange liquidity, commission, stake limits, and exact QL still need Rory's human-layer confirmation.

## Research rules

1. Search current and next-upcoming fixtures from reliable sources.
2. Convert kick-off times to UK time.
3. Check the relevant baseline team files before final ranking.
4. Prioritise 2UP eligibility, back/lay closeness, exchange liquidity, QL, and volatility over normal win probability.
5. Record bookmaker back odds as `favourite_odds` when verified.
6. Record lay odds, QL estimates, exchange/source notes, uncertainty, and human-layer checks in `source_notes` until dedicated columns exist.
7. Prefer volatile favourites: teams that can go two goals ahead but are not guaranteed to close the match calmly.
8. Avoid ultra-safe dominant favourites unless the QL is excellent and the 2UP trigger chance is high enough to justify the trade.
9. Do not invent fixtures, odds, stats, kick-off times, favourites, liquidity, qualifying loss, or offer eligibility.
10. If odds/eligibility are supplied by Rory, treat them as user-confirmed but still tell him to recheck before staking.
11. This is research only, never staking instruction or guaranteed profit.

## Repo update workflow

When Rory asks for a run:

1. Read this file first.
2. Inspect `data/fixture_bank_may_2026.csv` or the current fixture-bank file.
3. Inspect the relevant files in `data/team_baselines/` for the teams/leagues in scope.
4. Research/update the best candidates.
5. Update the fixture bank with ranked rows.
6. Ensure `fixtures_today.csv` reflects the ranked bank.
7. Regenerate or update:
   - `reports/daily_report.md`
   - `reports/archive/YYYY-MM-DD.md`
   - `docs/index.html`
   - `docs/data/today.json`
8. Commit to `main` with a clear message.
9. Summarise:
   - picks added/changed;
   - baseline data used;
   - back odds;
   - lay odds;
   - estimated QL;
   - 2UP rationale;
   - volatility/comeback angle;
   - human-layer checks;
   - commit hash;
   - whether report/dashboard updated.

## Preferred final answer format after a run

Use this structure:

```text
Done — repo updated.

Top pick: [fixture]
Why: [short reason]
Back/Lay: [prices]
Approx QL: [£ per £10 stake]
Baseline used: [file/row]
Human layer: [exact checks Rory still needs]

Other candidates:
1. ...
2. ...

Commit: [hash]
Report/dashboard: [updated / not updated / uncertain]
```

Keep the answer honest. If a file, workflow, odds source, or GitHub write fails, say exactly what failed.
