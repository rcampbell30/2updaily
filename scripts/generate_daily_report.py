"""Generate the daily 2up report, tracker JSON, and polished GitHub Pages UI."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from run_twoup_from_split_csv import load_all_team_stats, load_fixtures
from twoup_agents import TwoUpCandidate, TwoUpResearchPipeline


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = ROOT / "fixtures_today.csv"
TRACKER_PATH = ROOT / "data" / "results_tracker.csv"
REPORTS_DIR = ROOT / "reports"
ARCHIVE_DIR = REPORTS_DIR / "archive"
DOCS_DIR = ROOT / "docs"
DATA_DIR = DOCS_DIR / "data"


BLANKS = {"", "na", "n/a", "none", "null", "-", "unknown", "pending"}
COMPLETED_STATUSES = {"settled", "complete", "completed"}


def odds_display(odds: float | None) -> str:
    return "Unknown" if odds is None else str(odds)


def parse_float(value: object) -> float | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    if cleaned.lower() in BLANKS:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def money_display(value: float | None) -> str:
    if value is None:
        return "Pending"
    sign = "-" if value < 0 else ""
    return f"{sign}£{abs(value):.2f}"


def status_class(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned in {"planned", "watchlist"}:
        return "planned"
    if cleaned in {"pending", ""}:
        return "pending"
    if cleaned in COMPLETED_STATUSES:
        return "money"
    return ""


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


def read_tracker(path: Path = TRACKER_PATH) -> list[dict]:
    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8") as file:
        rows = []
        for row in csv.DictReader(file):
            rows.append({
                "date": row.get("date", ""),
                "fixture": row.get("fixture", ""),
                "pick": row.get("pick", ""),
                "league": row.get("league", ""),
                "kickoff_uk": row.get("kickoff_uk", ""),
                "back_odds": parse_float(row.get("back_odds")),
                "lay_odds": parse_float(row.get("lay_odds")),
                "back_stake": parse_float(row.get("back_stake")),
                "estimated_ql": parse_float(row.get("estimated_ql")),
                "actual_ql": parse_float(row.get("actual_ql")),
                "two_up_triggered": row.get("two_up_triggered", ""),
                "trigger_minute": row.get("trigger_minute", ""),
                "final_score": row.get("final_score", ""),
                "final_result": row.get("final_result", ""),
                "net_pl": parse_float(row.get("net_pl")),
                "status": row.get("status", ""),
                "lesson": row.get("lesson", ""),
                "notes": row.get("notes", ""),
                "last_updated": row.get("last_updated", ""),
            })
        return rows


def tracker_summary(rows: list[dict]) -> dict:
    completed = [row for row in rows if row.get("status", "").strip().lower() in COMPLETED_STATUSES]
    trigger_known = [row for row in rows if row.get("two_up_triggered", "").strip().lower() in {"yes", "no"}]
    trigger_count = sum(1 for row in trigger_known if row.get("two_up_triggered", "").strip().lower() == "yes")
    est_ql = sum(value for value in (row.get("estimated_ql") for row in rows) if value is not None)
    actual_ql = sum(value for value in (row.get("actual_ql") for row in completed) if value is not None)
    net_pl = sum(value for value in (row.get("net_pl") for row in completed) if value is not None)
    return {
        "total_rows": len(rows),
        "planned_or_pending": len(rows) - len(completed),
        "completed": len(completed),
        "trigger_count": trigger_count,
        "trigger_rate": round(trigger_count / len(trigger_known), 4) if trigger_known else None,
        "estimated_ql_total": round(est_ql, 2),
        "actual_ql_total": round(actual_ql, 2),
        "net_pl_total": round(net_pl, 2),
    }


def list_items(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"<li>{escape(item)}</li>" for item in values)


def trigger_rate_display(value: float | None) -> str:
    return "Pending" if value is None else f"{value * 100:.0f}%"


def tracker_dashboard_html(tracker: dict) -> str:
    rows = tracker["entries"]
    summary = tracker["summary"]
    row_html = ""
    for row in rows:
        row_html += f"""
            <tr>
              <td>{escape(row['date'])}</td>
              <td>{escape(row['fixture'])}</td>
              <td>{escape(row['pick'])}</td>
              <td class="{status_class(row['status'])}">{escape(row['status'])}</td>
              <td class="{status_class(row['two_up_triggered'])}">{escape(row['two_up_triggered'])}</td>
              <td class="money">{money_display(row['estimated_ql'])}</td>
              <td class="{status_class(str(row['net_pl']))}">{money_display(row['net_pl'])}</td>
            </tr>
        """

    if not row_html:
        row_html = "<tr><td colspan='7'>No tracker rows yet.</td></tr>"

    return f"""
    <section class="card">
      <div class="card-head">
        <h2>2UP Results Tracker</h2>
        <span>Feedback loop</span>
      </div>
      <p class="muted">Records planned and settled tests so the system can learn from real outcomes. Keep account-sensitive bookmaker details out of the repo.</p>
      <div class="grid">
        <div><span>Total Rows</span><strong>{summary['total_rows']}</strong></div>
        <div><span>Completed</span><strong>{summary['completed']}</strong></div>
        <div><span>2UP Triggers</span><strong>{summary['trigger_count']}</strong></div>
        <div><span>Trigger Rate</span><strong>{trigger_rate_display(summary['trigger_rate'])}</strong></div>
        <div><span>Est. QL</span><strong>{money_display(summary['estimated_ql_total'])}</strong></div>
        <div><span>Actual QL</span><strong>{money_display(summary['actual_ql_total'])}</strong></div>
        <div><span>Net P/L</span><strong>{money_display(summary['net_pl_total'])}</strong></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Fixture</th><th>Pick</th><th>Status</th><th>2UP</th><th>Est. QL</th><th>Net P/L</th></tr></thead>
          <tbody>{row_html}</tbody>
        </table>
      </div>
    </section>
    """


def tracker_page_html(payload: dict) -> str:
    tracker = payload["tracker"]
    rows = tracker["entries"]
    summary = tracker["summary"]
    row_html = ""
    for row in rows:
        back_lay = "Pending"
        if row.get("back_odds") is not None and row.get("lay_odds") is not None:
            back_lay = f"{row['back_odds']} / {row['lay_odds']}"
        row_html += f"""
            <tr>
              <td>{escape(row['date'])}</td>
              <td>{escape(row['fixture'])}</td>
              <td>{escape(row['pick'])}</td>
              <td class="{status_class(row['status'])}">{escape(row['status'])}</td>
              <td class="{status_class(row['two_up_triggered'])}">{escape(row['two_up_triggered'])}</td>
              <td>{escape(back_lay)}</td>
              <td class="money">{money_display(row['estimated_ql'])}</td>
              <td class="{status_class(str(row['net_pl']))}">{money_display(row['net_pl'])}</td>
              <td class="note">{escape(row['lesson'])}</td>
            </tr>
        """

    if not row_html:
        row_html = "<tr><td colspan='9'>No tracker rows yet.</td></tr>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2UP Results Tracker</title>
  <link rel="stylesheet" href="app.css">
</head>
<body>
  <main>
    <header>
      <p class="confidence">Feedback loop</p>
      <h1>2UP Results Tracker</h1>
      <p class="subtitle">Tracks planned and settled 2UP tests so the system can learn from real outcomes. Do not add account-sensitive bookmaker details here.</p>
      <p class="nav"><a href="./">← Back to dashboard</a></p>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>Summary</h2>
        <span>Current test slate</span>
      </div>
      <div class="grid">
        <div><span>Total Rows</span><strong>{summary['total_rows']}</strong></div>
        <div><span>Completed</span><strong>{summary['completed']}</strong></div>
        <div><span>2UP Triggers</span><strong>{summary['trigger_count']}</strong></div>
        <div><span>Trigger Rate</span><strong>{trigger_rate_display(summary['trigger_rate'])}</strong></div>
        <div><span>Estimated QL</span><strong>{money_display(summary['estimated_ql_total'])}</strong></div>
        <div><span>Actual QL</span><strong>{money_display(summary['actual_ql_total'])}</strong></div>
        <div><span>Net P/L</span><strong>{money_display(summary['net_pl_total'])}</strong></div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Tracked Tests</h2>
        <span>Pending outcomes</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Fixture</th><th>Pick</th><th>Status</th><th>2UP</th><th>Back/Lay</th><th>Est. QL</th><th>Net P/L</th><th>Lesson</th></tr></thead>
          <tbody>{row_html}</tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <h2>How to update after a match</h2>
      <p class="subtitle">Update <code>data/results_tracker.csv</code> with the actual result, then regenerate the page. Set <code>status</code> to <code>Settled</code> once complete.</p>
    </section>
  </main>
</body>
</html>
"""


def candidate_card(candidate: dict) -> str:
    title = f"{candidate['rank']}. {candidate['home_team']} vs {candidate['away_team']}"
    data_quality = int(candidate["data_quality"] * 100)
    source_notes = candidate.get("source_notes") or "No source notes."
    confidence = f"{candidate['confidence']} confidence"
    if candidate["rank"] == 2:
        confidence = "Volatility watch"
    elif candidate["rank"] == 3:
        confidence = "Watchlist"

    return f"""
    <article class="card">
      <div class="card-head">
        <h2>{escape(title)}</h2>
        <span>{escape(confidence)}</span>
      </div>
      <div class="grid">
        <div><span>League</span><strong>{escape(candidate['league'])}</strong></div>
        <div><span>Kick-off</span><strong>{escape(candidate['kickoff_uk'])}</strong></div>
        <div><span>Favourite</span><strong>{escape(candidate['favourite'])}</strong></div>
        <div><span>Odds</span><strong>{escape(candidate['favourite_odds_display'])}</strong></div>
        <div><span>Score</span><strong>{candidate['score']}</strong></div>
        <div><span>Data quality</span><strong>{data_quality}%</strong></div>
      </div>
      <h3>Why it fits</h3>
      <ul>{list_items(candidate['reasons'], 'No strong positive scoring factors were triggered.')}</ul>
      <h3>Risks</h3>
      <ul>{list_items(candidate['risks'], 'No major statistical risk flagged from available data.')}</ul>
      <h3>Human layer / notes</h3>
      <p>{escape(source_notes)}</p>
      <h3>Data notes</h3>
      <ul>{list_items(candidate['data_notes'], 'No data quality notes.')}</ul>
    </article>
    """


def render_html(payload: dict) -> str:
    cards = "\n".join(candidate_card(candidate) for candidate in payload["candidates"])
    if not cards:
        cards = "<section class='card'><h2>No candidates found</h2><p>No fixtures passed the current filters.</p></section>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2upDaily Research Dashboard</title>
  <link rel="stylesheet" href="app.css">
</head>
<body>
  <main>
    <header>
      <p class="confidence">2UP Research Dashboard</p>
      <h1>2upDaily</h1>
      <p class="subtitle">A focused 2UP early-payout research dashboard. It ranks shortlist candidates, shows the human checks still needed, and tracks results so the system learns from real outcomes.</p>
      <nav class="site-nav">
        <a href="tracker.html">Open tracker</a>
        <a href="data/today.json">Today JSON</a>
        <a href="data/results.json">Results JSON</a>
      </nav>
    </header>

    <section class="status">
      <span class="pill">Report date: {escape(payload['report_date_london'])}</span>
      <span class="pill">Generated: {escape(payload['generated_at_london'])}</span>
      <span class="pill">Fixtures loaded: {payload['total_fixtures_loaded']}</span>
      <span class="pill">Candidates shown: {len(payload['candidates'])}</span>
    </section>

    {cards}

    {tracker_dashboard_html(payload['tracker'])}

    <section class="card notice">
      <strong>Reminder:</strong> this is a research shortlist only. Confirm the bookmaker offer, odds, liquidity, and staking plan before doing anything with real money.
    </section>
  </main>
</body>
</html>
"""


def tracker_markdown(tracker: dict) -> str:
    rows = tracker["entries"]
    summary = tracker["summary"]
    lines = [
        "## 2UP Results Tracker",
        "",
        f"Total rows: {summary['total_rows']}",
        f"Completed: {summary['completed']}",
        f"2UP triggers: {summary['trigger_count']}",
        f"Trigger rate: {trigger_rate_display(summary['trigger_rate'])}",
        f"Estimated QL total: {money_display(summary['estimated_ql_total'])}",
        f"Actual QL total: {money_display(summary['actual_ql_total'])}",
        f"Net P/L: {money_display(summary['net_pl_total'])}",
        "",
        "| Date | Fixture | Pick | Status | 2UP | Est. QL | Net P/L |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['date']} | {row['fixture']} | {row['pick']} | {row['status']} | {row['two_up_triggered']} | {money_display(row['estimated_ql'])} | {money_display(row['net_pl'])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    london_now = datetime.now(ZoneInfo("Europe/London"))
    utc_now = datetime.now(ZoneInfo("UTC"))
    report_date = london_now.date().isoformat()

    stats_by_team = load_all_team_stats()
    fixtures = load_fixtures(FIXTURES_PATH, stats_by_team)

    pipeline = TwoUpResearchPipeline()
    filtered = pipeline.league_filter.run(fixtures)
    filtered = pipeline.odds_filter.run(filtered)
    candidates = pipeline.scorer.run(filtered)
    top_candidates = candidates[:3]
    report = pipeline.reporter.run(top_candidates, limit=3)

    tracker_rows = read_tracker()
    tracker = {"summary": tracker_summary(tracker_rows), "entries": tracker_rows}
    payload = {
        "generated_at_utc": utc_now.isoformat(timespec="seconds"),
        "generated_at_london": london_now.strftime("%Y-%m-%d %H:%M %Z"),
        "report_date_london": report_date,
        "total_fixtures_loaded": len(fixtures),
        "total_fixtures_after_filters": len(filtered),
        "candidates": [candidate_to_dict(candidate, rank) for rank, candidate in enumerate(top_candidates, start=1)],
        "tracker": tracker,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    header = (
        f"Generated: {payload['generated_at_london']}\n"
        f"Report date: {payload['report_date_london']}\n"
        f"Fixtures loaded: {payload['total_fixtures_loaded']}\n\n"
    )
    full_report = header + report + "\n" + tracker_markdown(tracker) + "\n"

    (REPORTS_DIR / "daily_report.md").write_text(full_report, encoding="utf-8")
    (ARCHIVE_DIR / f"{report_date}.md").write_text(full_report, encoding="utf-8")
    (DATA_DIR / "today.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (DATA_DIR / "results.json").write_text(json.dumps(tracker, indent=2), encoding="utf-8")
    (DOCS_DIR / "index.html").write_text(render_html(payload), encoding="utf-8")
    (DOCS_DIR / "tracker.html").write_text(tracker_page_html(payload), encoding="utf-8")

    print(f"Generated report for {report_date}")
    print(f"Fixtures loaded: {len(fixtures)}")
    print(f"Candidates shown: {len(top_candidates)}")
    print(f"Tracker rows: {len(tracker_rows)}")


if __name__ == "__main__":
    main()
