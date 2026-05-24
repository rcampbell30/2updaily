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
- Bayern at 1.40 back / 1.42 lay is a very strong low-QL trade because Rory confirmed 2UP availability, tight back/lay pricing, and a tiny QL. It can be Medium confidence even with incomplete specialist model fields, but it still carries routine-favourite risk if Bayern simply control the final.
- Auckland FC at 2.10 back / 2.30 lay had a bigger QL and good strategy shape, but the 1-0 result showed the core 2UP risk: a favourite can win without ever creating the required two-goal separation.

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

## Double-sided same-market exposure and early payout calc

When Rory backs and lays both teams in the same exchange Match Odds market, do not add exchange liabilities as if they are separate markets. The exchange exposure is shared because only one Match Odds selection can win.

For a two-sided setup with Team A and Team B both backed at the bookmaker and both laid on the exchange:

```text
exchange_if_A_wins = lay_stake_B - ((lay_odds_A - 1) * lay_stake_A)
exchange_if_B_wins = lay_stake_A - ((lay_odds_B - 1) * lay_stake_B)
exchange_if_draw = lay_stake_A + lay_stake_B
```

Apply exchange commission to the net exchange market profit only when the exchange result is positive. If the net exchange result is negative, commission is normally zero because there is no net exchange win on that market.

This means the required exchange bank is the worst negative exchange outcome, not the sum of both individual lay liabilities.

Call the special scenario calculation an `early payout calc` when Rory asks what happens after a team triggers 2UP.

For an early payout calc:

- Treat the team that triggered 2UP as a winning bookmaker back bet even if the match later draws or loses.
- Treat the exchange lays according to the final official Match Odds result.
- If final result is a draw, both team lays win on the exchange, subject to commission on net exchange profit.
- If the triggering team still wins, its lay loses and the other team lay wins; calculate the net exchange result before applying commission.
- If both teams somehow trigger 2UP in the same match, state that as a special case and calculate both bookmaker backs as winners.
- Rare unicorn case: if Team A goes 2-0 up and triggers 2UP, then Team B later goes two goals ahead as well, for example 2-4, and the match eventually ends as a draw such as 4-4, then all four positions can win: both bookmaker backs are treated as early-payout winners and both exchange team lays win because the official Match Odds result is the draw. This is very rare but must be handled explicitly.

Example to remember: Kansas City vs NY Red Bulls double-sided 2UP used Kansas back/lay 3.00/3.15 and NY Red Bulls back/lay 2.10/2.26. If NYRB trigger 2UP and the final score is 2-2, NYRB is a winning bookmaker early-payout bet, Kansas bookmaker back loses, and both exchange lays win because the final Match Odds result is the draw.

Second rare example: Team A 2-0, Team B comes back to 2-4, then final score 4-4. If Rory backed both teams with 2UP and laid both teams on the exchange, both bookmaker backs can win from early payout and both exchange lays can win from the draw result.

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
- `data/team_baselines/bundesliga_dfb_pokal_finalists_2025_26.csv` - compact Bayern/Stuttgart DFB-Pokal final baseline.

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

## Confidence and honesty rules

Confidence should reflect practical trade confidence, not only spreadsheet completeness.

Keep these concepts separate:

- `Data quality` = how complete the baseline model fields are.
- `Confidence` = practical confidence in the 2UP research candidate after combining baseline data with Rory-confirmed human-layer market evidence.

A candidate can be lifted from Low to Medium confidence when all of the following are true:

- Rory has confirmed 2UP / 2 Goals Ahead availability for the exact fixture;
- Rory has supplied current back/lay prices;
- QL has been estimated from those prices;
- favourite odds are present;
- candidate score is at least 30;
- baseline data quality is at least 50%.

Do not lift confidence just because the fixture feels attractive. If 2UP eligibility, back/lay prices, QL, liquidity, or baseline data are missing, keep confidence limited and explain why.

Do not use High confidence unless both the football-data layer and human-layer market checks are genuinely strong. Missing first-half or conceded-after-leading data should still be shown in the notes, even when confidence is lifted to Medium.

Use wording like:

```text
Confidence includes user-confirmed 2UP/back-lay/QL evidence; specialist model fields are still incomplete.
```

This avoids the old problem where a candidate with excellent user-confirmed market data was labelled Low only because specialist model fields were incomplete. It also avoids the opposite problem: pretending the model knows more than it does.

## Required odds-check handoff

After producing a new shortlist, ChatGPT must ask Rory for the live market checks before treating any pick as trade-ready.

For each top candidate, ask Rory for:

- whether 2UP / 2 Goals Ahead is showing on his bookmaker account;
- bookmaker back odds;
- exchange lay odds;
- rough available lay liquidity at or near that lay price;
- commission assumption if it is not the normal default;
- any stake-limit or account restriction warning.

Use a concise handoff like:

```text
Before I can rank these as real trades, send me the back/lay for:
1. [fixture] — back ? / lay ? / 2UP showing? / liquidity?
2. [fixture] — back ? / lay ? / 2UP showing? / liquidity?
3. [fixture] — back ? / lay ? / 2UP showing? / liquidity?
```

Do not leave a run at the watchlist stage without asking for lay odds. The whole point of the system is to move from football shape to trade shape. A fixture with good football data but no back/lay/QL remains a watchlist candidate only.

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
11. Confidence labels must respect user-confirmed 2UP/back-lay/QL evidence, but missing data must still be stated clearly.
12. After every new watchlist run, explicitly ask Rory for back odds, lay odds, 2UP confirmation and liquidity for the top candidates.
13. For double-sided same-market setups, calculate shared exchange exposure by final outcome rather than adding lay liabilities separately.
14. Use `early payout calc` for scenario maths after a 2UP trigger.
15. This is research only, never staking instruction or guaranteed profit.

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
   - `docs/data/results.json`
   - `docs/tracker.html`
8. Commit to `main` with a clear message.
9. Summarise:
   - picks added/changed;
   - baseline data used;
   - back odds;
   - lay odds;
   - estimated QL;
   - 2UP rationale;
   - volatility/comeback angle;
   - confidence/data-quality reasoning;
   - human-layer checks;
   - commit hash;
   - whether report/dashboard updated.
10. If any top candidate is still missing lay odds or 2UP confirmation, ask Rory for those values in the final response.

## Preferred final answer format after a run

Use this structure:

```text
Done — repo updated.

Top pick: [fixture]
Why: [short reason]
Back/Lay: [prices or missing]
Approx QL: [£ per £10 stake or pending]
Confidence/Data quality: [confidence label + any missing-data caveat]
Baseline used: [file/row]
Human layer: [exact checks Rory still needs]

Other candidates:
1. ...
2. ...

Needed from Rory before trade ranking:
1. [fixture] — back ? / lay ? / 2UP showing? / liquidity?
2. [fixture] — back ? / lay ? / 2UP showing? / liquidity?
3. [fixture] — back ? / lay ? / 2UP showing? / liquidity?

Commit: [hash]
Report/dashboard: [updated / not updated / uncertain]
```

Keep the answer honest. If a file, workflow, odds source, or GitHub write fails, say exactly what failed.
