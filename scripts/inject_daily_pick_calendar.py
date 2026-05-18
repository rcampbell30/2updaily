"""Inject a featured daily pick and organised fixture-bank calendar into docs/index.html.

The main report generator owns docs/index.html, so this script runs after it in
GitHub Actions and adds a fixture-bank section from data/fixture_bank_may_2026.csv.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from datetime import date, datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "index.html"
FIXTURE_BANK_PATH = ROOT / "data" / "fixture_bank_may_2026.csv"

START_MARKER = "<!-- daily-pick-calendar:start -->"
END_MARKER = "<!-- daily-pick-calendar:end -->"


def human_date(iso_date: str) -> str:
    """Return dates as 'Monday 18 May 2026' for clearer homepage reading."""
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return iso_date
    return parsed.strftime("%A %-d %B %Y")


def relative_day_label(iso_date: str) -> str:
    today = date.today()
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return "Fixture bank"

    if parsed == today:
        return "Today"
    if (parsed - today).days == 1:
        return "Tomorrow"
    return parsed.strftime("%A")


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

            # One visible pick per matchday. The fixture bank is ordered by
            # rough manual priority, so the first fixture for each date wins.
            if match_date not in picks_by_date:
                picks_by_date[match_date] = row

    return list(picks_by_date.values())


def pick_title(row: dict[str, str]) -> str:
    return f"{escape(row.get('home_team', ''))} vs {escape(row.get('away_team', ''))}"


def render_meta(row: dict[str, str]) -> str:
    match_date_raw = row.get("date", "").strip()
    match_date = escape(human_date(match_date_raw))
    league = escape(row.get("league", ""))
    kickoff = escape(row.get("kickoff_uk", ""))
    favourite = escape(row.get("provisional_favourite", ""))
    odds = escape(row.get("favourite_odds", "").strip() or "Check odds")

    return f"""
      <dl class="meta-grid">
        <div><dt>Date</dt><dd>{match_date}</dd></div>
        <div><dt>League</dt><dd>{league}</dd></div>
        <div><dt>Kick-off UK</dt><dd>{kickoff}</dd></div>
        <div><dt>Provisional favourite</dt><dd>{favourite}</dd></div>
        <div><dt>Odds</dt><dd>{odds}</dd></div>
      </dl>
    """


def render_featured_pick(row: dict[str, str]) -> str:
    today = date.today().isoformat()
    match_date_raw = row.get("date", "").strip()
    readable_date = escape(human_date(match_date_raw))
    relative_label = escape(relative_day_label(match_date_raw))
    label = "Today’s fixture-bank pick" if match_date_raw == today else "Next fixture-bank pick"
    notes = escape(row.get("source_notes", ""))

    return f"""
    <section>
      <h2>{label}</h2>
      <article class="pick-card">
        <div class="card-header">
          <h3>{relative_label} — {readable_date}<br>{pick_title(row)}</h3>
          <span class="confidence">Fixture bank</span>
        </div>
        {render_meta(row)}
        <h3>What to do today</h3>
        <ul>
          <li>Check live odds before using this as a 2UP research angle.</li>
          <li>Confirm the bookmaker early-payout terms still apply.</li>
          <li>Only treat this as a shortlist candidate, not a guaranteed pick.</li>
        </ul>
        <p class="subtitle">{notes}</p>
      </article>
    </section>
    """


def render_calendar_pick(row: dict[str, str]) -> str:
    match_date_raw = row.get("date", "").strip()
    readable_date = escape(human_date(match_date_raw))
    relative_label = escape(relative_day_label(match_date_raw))
    notes = escape(row.get("source_notes", ""))

    return f"""
    <article class="pick-card">
      <div class="card-header">
        <h3>{relative_label} — {readable_date}<br>{pick_title(row)}</h3>
        <span class="confidence">Fixture bank</span>
      </div>
      {render_meta(row)}
      <p class="subtitle">{notes}</p>
    </article>
    """


def render_section() -> str:
    picks = load_daily_picks()

    if not picks:
        body = """
        <section class="empty-card">
          <h2>Today’s fixture-bank pick</h2>
          <p>No upcoming fixture-bank picks found. Add rows to data/fixture_bank_may_2026.csv.</p>
        </section>
        """
    else:
        featured = render_featured_pick(picks[0])
        cards = "\n".join(render_calendar_pick(row) for row in picks)
        body = f"""
        {featured}
        <section>
          <h2>Upcoming pick calendar</h2>
          <p class="subtitle">Organised by day and date. One provisional 2UP research fixture is shown per available May matchday. If there is no fixture today, the featured card rolls forward to the next banked fixture.</p>
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
    print("Injected featured daily pick and organised calendar into docs/index.html")


if __name__ == "__main__":
    main()
