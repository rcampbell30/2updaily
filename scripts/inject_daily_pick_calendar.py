"""Inject a simple daily pick calendar into docs/index.html.

The main report generator owns docs/index.html, so this script runs after it in
GitHub Actions and adds a fixture-bank section from data/fixture_bank_may_2026.csv.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "index.html"
FIXTURE_BANK_PATH = ROOT / "data" / "fixture_bank_may_2026.csv"

START_MARKER = "<!-- daily-pick-calendar:start -->"
END_MARKER = "<!-- daily-pick-calendar:end -->"


def load_daily_picks() -> list[dict[str, str]]:
    if not FIXTURE_BANK_PATH.exists():
        return []

    today = date.today().isoformat()
    picks_by_date: OrderedDict[str, dict[str, str]] = OrderedDict()

    with FIXTURE_BANK_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            match_date = row.get("date", "").strip()
            if not match_date or match_date < today:
                continue

            # One visible pick per day. The bank is already ordered by our rough
            # manual priority, so the first fixture for each date wins.
            if match_date not in picks_by_date:
                picks_by_date[match_date] = row

    return list(picks_by_date.values())


def render_pick(row: dict[str, str]) -> str:
    home = escape(row.get("home_team", ""))
    away = escape(row.get("away_team", ""))
    league = escape(row.get("league", ""))
    kickoff = escape(row.get("kickoff_uk", ""))
    favourite = escape(row.get("provisional_favourite", ""))
    odds = escape(row.get("favourite_odds", "").strip() or "Check odds")
    notes = escape(row.get("source_notes", ""))
    match_date = escape(row.get("date", ""))

    return f"""
    <article class="pick-card">
      <div class="card-header">
        <h3>{match_date}: {home} vs {away}</h3>
        <span class="confidence">Fixture bank</span>
      </div>
      <dl class="meta-grid">
        <div><dt>League</dt><dd>{league}</dd></div>
        <div><dt>Kick-off</dt><dd>{kickoff}</dd></div>
        <div><dt>Provisional favourite</dt><dd>{favourite}</dd></div>
        <div><dt>Odds</dt><dd>{odds}</dd></div>
      </dl>
      <p class="subtitle">{notes}</p>
    </article>
    """


def render_section() -> str:
    picks = load_daily_picks()

    if not picks:
        body = """
        <section class="empty-card">
          <h2>Daily pick calendar</h2>
          <p>No upcoming fixture-bank picks found. Add rows to data/fixture_bank_may_2026.csv.</p>
        </section>
        """
    else:
        cards = "\n".join(render_pick(row) for row in picks)
        body = f"""
        <section>
          <h2>Daily pick calendar</h2>
          <p class="subtitle">One provisional 2UP research fixture per available May matchday. Odds and bookmaker terms still need checking on the day.</p>
          {cards}
        </section>
        """

    return f"\n{START_MARKER}\n{body}\n{END_MARKER}\n"


def strip_existing_section(html: str) -> str:
    start = html.find(START_MARKER)
    end = html.find(END_MARKER)
    if start == -1 or end == -1:
        return html
    return html[:start] + html[end + len(END_MARKER):]


def main() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    html = strip_existing_section(html)
    section = render_section()

    insertion_point = html.find("    <section class=\"notice\">")
    if insertion_point == -1:
        insertion_point = html.find("  </main>")

    if insertion_point == -1:
        raise RuntimeError("Could not find a safe insertion point in docs/index.html")

    html = html[:insertion_point] + section + "\n" + html[insertion_point:]
    INDEX_PATH.write_text(html, encoding="utf-8")
    print("Injected daily pick calendar into docs/index.html")


if __name__ == "__main__":
    main()
