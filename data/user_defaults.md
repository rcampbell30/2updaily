# User Defaults for 2upDaily

These defaults are manually supplied by Rory and should be used by future ChatGPT-assisted 2UP runs unless Rory explicitly updates them.

## Exchange commission

- Default exchange commission: **2%**.
- Use 2% as the headline qualifying-loss calculation for live positions and final summaries.
- 0% and 5% can still be shown as reference/sensitivity figures, but they should not be treated as the main expected QL.

## Current live-position convention

- Store real placed positions separately from watchlist candidates.
- Use `docs/data/live-bets.json` and `docs/live-bets.html` for live managed positions.
- Use `data/results_tracker.csv` for the tracker/feed-back loop.
- Avoid storing bookmaker names, account-specific restrictions, or sensitive account details in the public repo.

## Matched-betting output convention

When Rory supplies live odds and confirms 2UP/liquidity, report:

```text
Back stake
Back odds
Lay odds
Lay stake at 2%
Lay liability at 2%
Headline QL at 2%
Free bet/reload value, if any
2UP trigger status
Settlement status
```

If 2UP visibility or liquidity is not confirmed, keep the fixture as a watchlist candidate only.
