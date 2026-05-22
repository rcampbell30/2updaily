"""Generate the daily 2up report, tracker JSON, and static site files."""

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


def tracker_html(tracker: dict) -> str:
    rows = tracker["entries"]
    summary = tracker["summary"]
    trigger_rate = summary["trigger_rate"]
    trigger_text = "Pending" if trigger_rate is None else f"{trigger_rate * 100:.0f}%"
    row_html = ""
    for row in rows:
        row_html += f"""
        <tr>
          <td>{escape(row['date'])}</td>
          <td>{escape(row['fixture'])}</td>
          <td>{escape(row['pick'])}</td>
          <td>{escape(row['status'])}</td>
          <td>{escape(row['two_up_triggered'])}</td>
          <td>{money_display(row['estimated_ql'])}</td>
          <td>{money_display(row['net_pl'])}</td>
        </tr>
        """
    if not row_html:
        row_html = "<tr><td colspan='7'>No tracker rows yet.</td></tr>"
    return f"""
    <section class="card">
      <h2>2UP Results Tracker</h2>
      <p class="muted">Records planned and settled 2UP tests so the system can learn from real outcomes. Keep account-sensitive details out of the repo.</p>
      <div class="grid">
        <div><span>Total Rows</span><strong>{summary['total_rows']}</strong></div>
        <div><span>Completed</span><strong>{summary['completed']}</strong></div>
        <div><span>2UP Triggers</span><strong>{summary['trigger_count']}</strong></div>
        <div><span>Trigger Rate</span><strong>{trigger_text}</strong></div>
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


def tracker_markdown(tracker: dict) -> str:
    rows = tracker["entries"]
    summary = tracker["summary"]
    trigger_rate = summary["trigger_rate"]
    trigger_text = "Pending" if trigger_rate is None else f"{trigger_rate * 100:.0f}%"
    lines = [
        "## 2UP Results Tracker",
        "",
        f"Total rows: {summary['total_rows']}",
        f"Completed: {summary['completed']}",
        f"2UP triggers: {summary['trigger_count']}",
        f"Trigger rate: {trigger_text}",
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


def render_html(payload: dict) -> str:
    cards = ""
    for candidate in payload["candidates"]:
        title = f"{candidate['rank']}. {candidate['home_team']} vs {candidate['away_team']}"
        data_quality = int(candidate["data_quality"] * 100)
        source_notes = candidate.get("source_notes") or "No source notes."
        cards += f"""
        <article class="card">
          <div class="card-head"><h2>{escape(title)}</h2><span>{escape(candidate['confidence'])}</span></div>
          <div class="grid">
            <div><span>League</span><strong>{escape(candidate['league'])}</strong></div>
            <div><span>Kick-off</span><strong>{escape(candidate['kickoff_uk'])}</strong></div>
            <div><span>Favourite</span><strong>{escape(candidate['favourite'])}</strong></div>
            <div><span>Odds</span><strong>{escape(candidate['favourite_odds_display'])}</strong></div>
            <div><span>Score</span><strong>{candidate['score']}</strong></div>
            <div><span>Data Quality</span><strong>{data_quality}%</strong></div>
          </div>
          <h3>Source notes / human layer</h3><p>{escape(source_notes)}</p>
          <h3>Why it fits</h3><ul>{list_items(candidate['reasons'], 'No strong positive scoring factors were triggered.')}</ul>
          <h3>Risks</h3><ul>{list_items(candidate['risks'], 'No major statistical risk flagged from available data.')}</ul>
          <h3>Data notes</h3><ul>{list_items(candidate['data_notes'], 'No data quality notes.')}</ul>
        </article>
        """
    if not cards:
        cards = "<section class='card'><h2>No candidates found</h2><p>No fixtures passed the current filters.</p></section>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2upDaily Research Shortlist</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#9ca3af; --accent:#38bdf8; --border:#334155; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:radial-gradient(circle at top,#1e293b 0,var(--bg) 45%); color:var(--text); line-height:1.5; }}
    main {{ width:min(1100px,calc(100% - 32px)); margin:0 auto; padding:40px 0 64px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(2rem,5vw,4rem); letter-spacing:-0.04em; }}
    h2 {{ margin:0 0 16px; }} h3 {{ margin:20px 0 8px; color:var(--accent); }}
    .muted, .subtitle, .notice {{ color:var(--muted); }}
    .status {{ display:flex; flex-wrap:wrap; gap:12px; margin:24px 0; }}
    .pill {{ border:1px solid var(--border); background:rgba(15,23,42,.72); padding:8px 12px; border-radius:999px; color:var(--muted); }}
    .card {{ border:1px solid var(--border); background:linear-gradient(180deg,rgba(31,41,55,.92),rgba(17,24,39,.94)); border-radius:20px; padding:22px; margin:18px 0; box-shadow:0 20px 60px rgba(0,0,0,.24); }}
    .card-head {{ display:flex; gap:12px; justify-content:space-between; align-items:flex-start; }}
    .card-head span {{ background:rgba(56,189,248,.14); color:#bae6fd; border:1px solid rgba(56,189,248,.42); padding:6px 10px; border-radius:999px; white-space:nowrap; font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin:12px 0 18px; }}
    .grid div {{ background:rgba(15,23,42,.72); border:1px solid var(--border); border-radius:14px; padding:12px; }}
    .grid span {{ display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }}
    .grid strong {{ display:block; margin-top:4px; }}
    ul {{ padding-left:1.2rem; }} li {{ margin:6px 0; }}
    .table-wrap {{ width:100%; overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; min-width:760px; }}
    th, td {{ border-bottom:1px solid var(--border); padding:10px 8px; text-align:left; vertical-align:top; }}
    th {{ color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }}
  </style>
</head>
<body>
  <main>
    <header><h1>2upDaily</h1><p class="subtitle">Today’s 2UP research shortlist. This is a data-driven shortlist tool, not a guarantee, and it does not place bets.</p></header>
    <section class="status">
      <span class="pill">Report date: {escape(payload['report_date_london'])}</span>
      <span class="pill">Generated: {escape(payload['generated_at_london'])}</span>
      <span class="pill">Fixtures loaded: {payload['total_fixtures_loaded']}</span>
      <span class="pill">Candidates shown: {len(payload['candidates'])}</span>
    </section>
    {cards}
    {tracker_html(payload['tracker'])}
    <section class="card notice"><strong>Reminder:</strong> use this as a research shortlist only. Confirm the bookmaker offer, odds, liquidity, and staking plan before doing anything with real money.</section>
  </main>
</body>
</html>
"""


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
        "generated_at_london": london_now.isoformat(timespec="seconds"),
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

    print(f"Generated report for {report_date}")
    print(f"Fixtures loaded: {len(fixtures)}")
    print(f"Candidates shown: {len(top_candidates)}")
    print(f"Tracker rows: {len(tracker_rows)}")


if __name__ == "__main__":
    main()
