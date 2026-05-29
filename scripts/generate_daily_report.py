"""Generate the simple pick-only 2upDaily homepage.

The repo now publishes a clean one-pick-per-day research watchlist from
`data/next_picks.json`. It does not generate tracking pages, settlement tables,
or legacy analytics dashboards.
"""

from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
NEXT_PICKS_PATH = ROOT / "data" / "next_picks.json"
REPORTS_DIR = ROOT / "reports"
ARCHIVE_DIR = REPORTS_DIR / "archive"
DOCS_DIR = ROOT / "docs"
DATA_DIR = DOCS_DIR / "data"


def load_next_picks() -> dict:
    if not NEXT_PICKS_PATH.exists():
        raise FileNotFoundError("data/next_picks.json is required for the pick-only homepage.")
    return json.loads(NEXT_PICKS_PATH.read_text(encoding="utf-8"))


def status_label(status: str) -> str:
    cleaned = status.strip().upper()
    return cleaned or "PENDING"


def checks_html(checks: list[str]) -> str:
    if not checks:
        return "<li>No checks needed — pass day.</li>"
    return "\n".join(f"<li>{escape(check)}</li>" for check in checks)


def commission_label(pick: dict) -> str:
    return str(pick.get("commission_assumption") or "2%")


def pick_card(pick: dict) -> str:
    status = status_label(str(pick.get("status", "")))
    title = f"{pick.get('day', '')} {pick.get('date', '')} — {pick.get('fixture', 'No fixture')}"
    competition = pick.get("competition", "N/A")
    kickoff = pick.get("kickoff_uk", "N/A")
    candidate_type = pick.get("candidate_type", "")
    why = pick.get("why", "")
    checks = pick.get("checks_needed", [])
    commission = commission_label(pick)

    return f"""
    <article class="card">
      <div class="card-head">
        <h2>{escape(title)}</h2>
        <span>{escape(status)}</span>
      </div>
      <div class="grid">
        <div><span>Competition</span><strong>{escape(competition)}</strong></div>
        <div><span>Kick-off UK</span><strong>{escape(kickoff)}</strong></div>
        <div><span>Type</span><strong>{escape(candidate_type)}</strong></div>
        <div><span>Commission assumption</span><strong>{escape(commission)}</strong></div>
      </div>
      <h3>Read</h3>
      <p>{escape(why)}</p>
      <h3>Checks needed</h3>
      <ul>{checks_html(checks)}</ul>
    </article>
    """


def render_homepage(payload: dict, generated_london: str) -> str:
    picks = payload.get("picks", [])
    cards = "\n".join(pick_card(pick) for pick in picks)
    if not cards:
        cards = "<section class='card'><h2>No picks banked</h2><p>Add rows to data/next_picks.json.</p></section>"

    watchlist_count = sum(1 for pick in picks if status_label(str(pick.get("status", ""))) == "WATCHLIST")
    pass_count = sum(1 for pick in picks if status_label(str(pick.get("status", ""))) == "PASS")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2upDaily</title>
  <link rel="stylesheet" href="app.css">
</head>
<body>
  <main>
    <header>
      <p class="confidence">One pick per day</p>
      <h1>2upDaily</h1>
      <p class="subtitle">Clean 2UP research shortlist only. One focused candidate per day where a strong trade shape exists. If there is no worthwhile setup, the slate says PASS instead of forcing action.</p>
      <nav class="site-nav">
        <a href="data/next_picks.json">Next picks JSON</a>
        <a href="https://github.com/rcampbell30/2updaily">GitHub Repo</a>
      </nav>
    </header>

    <section class="status">
      <span class="pill">Updated: {escape(generated_london)}</span>
      <span class="pill">Mode: pick-only</span>
      <span class="pill">Watchlist days: {watchlist_count}</span>
      <span class="pill">Pass days: {pass_count}</span>
    </section>

    <section class="card notice">
      <strong>Workflow:</strong> shortlist first, then check live availability, back/lay prices, liquidity and stake sizing separately. No public tracking or result-ledger pages are generated.
    </section>

    {cards}

    <section class="card notice">
      <strong>Rule:</strong> no forced action. If prices, liquidity or terms are poor on the day, the correct move is PASS.
    </section>
  </main>
</body>
</html>
"""


def render_markdown(payload: dict, generated_london: str) -> str:
    lines = [
        f"Generated: {generated_london}",
        "Mode: one pick per day / pass if weak",
        "",
        "# 2upDaily Next Picks",
        "",
    ]
    for pick in payload.get("picks", []):
        lines.extend([
            f"## {pick.get('day', '')} {pick.get('date', '')} — {pick.get('fixture', 'No fixture')}",
            f"Status: {status_label(str(pick.get('status', '')))}",
            f"Competition: {pick.get('competition', 'N/A')}",
            f"Kick-off UK: {pick.get('kickoff_uk', 'N/A')}",
            f"Commission assumption: {commission_label(pick)}",
            f"Read: {pick.get('why', '')}",
            "",
            "Checks needed:",
        ])
        checks = pick.get("checks_needed", [])
        if checks:
            lines.extend(f"- {check}" for check in checks)
        else:
            lines.append("- No checks needed — pass day.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    london_now = datetime.now(ZoneInfo("Europe/London"))
    generated_london = london_now.strftime("%Y-%m-%d %H:%M %Z")
    report_date = london_now.date().isoformat()

    payload = load_next_picks()
    payload["generated_at_london"] = generated_london
    payload["report_date_london"] = report_date

    REPORTS_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    (DOCS_DIR / "index.html").write_text(render_homepage(payload, generated_london), encoding="utf-8")
    (DATA_DIR / "next_picks.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (DATA_DIR / "today.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown = render_markdown(payload, generated_london)
    (REPORTS_DIR / "daily_report.md").write_text(markdown, encoding="utf-8")
    (ARCHIVE_DIR / f"{report_date}.md").write_text(markdown, encoding="utf-8")

    print(f"Generated pick-only homepage for {report_date}")
    print(f"Picks loaded: {len(payload.get('picks', []))}")


if __name__ == "__main__":
    main()
