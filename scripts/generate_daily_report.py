"""Generate the daily 2up report and static site files.

This script is designed for GitHub Actions, but it also works locally:

    python scripts/generate_daily_report.py

It reads:
- team_stats.csv
- fixtures_today.csv

It writes:
- reports/daily_report.md
- reports/archive/YYYY-MM-DD.md
- docs/index.html
- docs/data/today.json

In the full GitHub Actions flow, scripts/seed_fixtures_today_from_bank.py runs
first and refreshes fixtures_today.csv from the ChatGPT-maintained fixture bank.
"""

from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from run_twoup_from_split_csv import load_fixtures, load_team_stats
from twoup_agents import TwoUpCandidate, TwoUpResearchPipeline


ROOT = Path(__file__).resolve().parents[1]
TEAM_STATS_PATH = ROOT / "team_stats.csv"
FIXTURES_PATH = ROOT / "fixtures_today.csv"
REPORTS_DIR = ROOT / "reports"
ARCHIVE_DIR = REPORTS_DIR / "archive"
DOCS_DIR = ROOT / "docs"
DATA_DIR = DOCS_DIR / "data"


def odds_display(odds: float | None) -> str:
    return "Unknown" if odds is None else str(odds)


def candidate_to_dict(candidate: TwoUpCandidate, rank: int) -> dict:
    fixture = candidate.fixture
    return {
        "rank": rank,
        "home_team": fixture.home_team,
        "away_team": fixture.away_team,
        "league": fixture.league,
        "kickoff_uk": fixture.kickoff_uk,
        "favourite": fixture.favourite,
        "favourite_odds": fixture.favourite_odds,
        "favourite_odds_display": odds_display(fixture.favourite_odds),
        "source_notes": fixture.source_notes,
        "score": candidate.score,
        "confidence": candidate.confidence,
        "data_quality": candidate.data_quality,
        "reasons": candidate.reasons,
        "risks": candidate.risks,
        "data_notes": candidate.data_notes,
        "missing_fields": candidate.missing_fields,
    }


def list_items(items: list[str], fallback: str) -> str:
    if not items:
        return f"<li>{escape(fallback)}</li>"
    return "\n".join(f"<li>{escape(item)}</li>" for item in items)


def render_source_notes(candidate: dict) -> str:
    source_notes = candidate.get("source_notes", "")
    if not source_notes:
        return ""

    return f"""
                  <h3>Source notes / human layer</h3>
                  <ul><li>{escape(source_notes)}</li></ul>
    """


def render_html(payload: dict) -> str:
    candidates = payload["candidates"]
    generated = escape(payload["generated_at_london"])
    report_date = escape(payload["report_date_london"])

    if not candidates:
        cards_html = """
        <section class="empty-card">
          <h2>No candidates found</h2>
          <p>No fixtures passed the current league and odds filters.</p>
        </section>
        """
    else:
        cards = []
        for candidate in candidates:
            title = f"{candidate['rank']}. {candidate['home_team']} vs {candidate['away_team']}"
            data_quality_percent = int(candidate["data_quality"] * 100)
            cards.append(
                f"""
                <article class="pick-card">
                  <div class="card-header">
                    <h2>{escape(title)}</h2>
                    <span class="confidence">{escape(candidate['confidence'])}</span>
                  </div>
                  <dl class="meta-grid">
                    <div><dt>League</dt><dd>{escape(candidate['league'])}</dd></div>
                    <div><dt>Kick-off</dt><dd>{escape(candidate['kickoff_uk'])}</dd></div>
                    <div><dt>Favourite</dt><dd>{escape(candidate['favourite'])}</dd></div>
                    <div><dt>Odds</dt><dd>{escape(candidate['favourite_odds_display'])}</dd></div>
                    <div><dt>Score</dt><dd>{candidate['score']}</dd></div>
                    <div><dt>Data quality</dt><dd>{data_quality_percent}%</dd></div>
                  </dl>

                  {render_source_notes(candidate)}

                  <h3>Why it fits</h3>
                  <ul>{list_items(candidate['reasons'], 'No strong positive scoring factors were triggered.')}</ul>

                  <h3>Risks</h3>
                  <ul>{list_items(candidate['risks'], 'No major statistical risk flagged from the available data.')}</ul>

                  <h3>Data notes</h3>
                  <ul>{list_items(candidate['data_notes'], 'No data quality notes.')}</ul>
                </article>
                """
            )
        cards_html = "\n".join(cards)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2upDaily Research Shortlist</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f172a;
      --panel: #111827;
      --panel-2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --accent: #38bdf8;
      --border: #334155;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #1e293b 0, var(--bg) 45%);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      width: min(1100px, calc(100% - 32px));
      margin: 0 auto;
      padding: 40px 0 64px;
    }}
    header {{
      margin-bottom: 28px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 4rem);
      letter-spacing: -0.04em;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      max-width: 760px;
    }}
    .status-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin: 24px 0;
    }}
    .pill {{
      border: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.72);
      padding: 8px 12px;
      border-radius: 999px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .pick-card, .empty-card, .notice {{
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(31, 41, 55, 0.92), rgba(17, 24, 39, 0.94));
      border-radius: 20px;
      padding: 22px;
      margin: 18px 0;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
    }}
    .card-header {{
      display: flex;
      gap: 12px;
      justify-content: space-between;
      align-items: flex-start;
    }}
    h2 {{ margin: 0 0 16px; }}
    h3 {{ margin: 20px 0 8px; color: var(--accent); }}
    .confidence {{
      background: rgba(56, 189, 248, 0.14);
      color: #bae6fd;
      border: 1px solid rgba(56, 189, 248, 0.42);
      padding: 6px 10px;
      border-radius: 999px;
      white-space: nowrap;
      font-weight: 700;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin: 0;
    }}
    .meta-grid div {{
      background: rgba(15, 23, 42, 0.72);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
    }}
    dt {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    dd {{ margin: 4px 0 0; font-weight: 700; }}
    ul {{ padding-left: 1.2rem; }}
    li {{ margin: 6px 0; }}
    .notice {{ color: var(--muted); }}
    a {{ color: #7dd3fc; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>2upDaily</h1>
      <p class="subtitle">Today’s 2up research shortlist. This is a data-driven shortlist tool, not a guarantee, and it does not place bets.</p>
    </header>

    <section class="status-bar">
      <span class="pill">Report date: {report_date}</span>
      <span class="pill">Generated: {generated}</span>
      <span class="pill">Fixtures loaded: {payload['total_fixtures_loaded']}</span>
      <span class="pill">Candidates shown: {len(candidates)}</span>
    </section>

    {cards_html}

    <section class="notice">
      <strong>Reminder:</strong> use this as a research shortlist only. Confirm the bookmaker offer, odds, liquidity, and staking plan before doing anything with real money.
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    london_now = datetime.now(ZoneInfo("Europe/London"))
    utc_now = datetime.now(ZoneInfo("UTC"))
    report_date = london_now.date().isoformat()

    stats_by_team = load_team_stats(TEAM_STATS_PATH)
    fixtures = load_fixtures(FIXTURES_PATH, stats_by_team)

    pipeline = TwoUpResearchPipeline()
    filtered = pipeline.league_filter.run(fixtures)
    filtered = pipeline.odds_filter.run(filtered)
    candidates = pipeline.scorer.run(filtered)
    top_candidates = candidates[:3]
    report = pipeline.reporter.run(top_candidates, limit=3)

    payload = {
        "generated_at_utc": utc_now.isoformat(timespec="seconds"),
        "generated_at_london": london_now.isoformat(timespec="seconds"),
        "report_date_london": report_date,
        "total_fixtures_loaded": len(fixtures),
        "total_fixtures_after_filters": len(filtered),
        "candidates": [candidate_to_dict(candidate, rank) for rank, candidate in enumerate(top_candidates, start=1)],
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    header = (
        f"Generated: {payload['generated_at_london']}\n"
        f"Report date: {payload['report_date_london']}\n"
        f"Fixtures loaded: {payload['total_fixtures_loaded']}\n\n"
    )

    (REPORTS_DIR / "daily_report.md").write_text(header + report + "\n", encoding="utf-8")
    (ARCHIVE_DIR / f"{report_date}.md").write_text(header + report + "\n", encoding="utf-8")
    (DATA_DIR / "today.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (DOCS_DIR / "index.html").write_text(render_html(payload), encoding="utf-8")

    print(f"Generated report for {report_date}")
    print(f"Fixtures loaded: {len(fixtures)}")
    print(f"Candidates shown: {len(top_candidates)}")


if __name__ == "__main__":
    main()
