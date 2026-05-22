"""
twoup_agents.py
================

A small narrow-agent pipeline for creating 2up research shortlists from football
fixture and team-stat data.

This module does not place bets, scrape bookmakers, or guarantee profit. It
takes structured data, filters fixtures, scores them, and prints a ranked
shortlist with reasons, risks, confidence, source notes, and data-quality notes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class TeamStats:
    """Team statistics used by the 2up scoring model."""

    name: str
    goals_for_avg: Optional[float] = None
    goals_against_avg: Optional[float] = None
    first_half_goals_avg: Optional[float] = None
    clean_sheet_rate: Optional[float] = None
    conceded_after_leading_rate: Optional[float] = None
    over_25_rate: Optional[float] = None


@dataclass
class Fixture:
    """A single football fixture with home/away stats attached."""

    home_team: str
    away_team: str
    league: str
    kickoff_uk: str
    favourite: str
    favourite_odds: Optional[float]
    home_stats: TeamStats
    away_stats: TeamStats
    source_notes: str = ""


@dataclass
class TwoUpCandidate:
    """A scored candidate fixture."""

    fixture: Fixture
    score: float
    reasons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    data_notes: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    data_quality: float = 1.0
    confidence: str = "Medium"


class LeagueFilterAgent:
    """Keeps competitions likely to have usable 2up coverage/liquidity."""

    def __init__(self) -> None:
        self.allowed_keywords = [
            "Premier League",
            "Championship",
            "La Liga",
            "Serie A",
            "Bundesliga",
            "DFB-Pokal",
            "Ligue 1",
            "Champions League",
            "Europa League",
            "Conference League",
            "FA Cup",
            "EFL Cup",
            "Scottish Cup",
            "Scottish Premiership",
            "Eredivisie",
            "Primeira Liga",
            "Japan",
            "J1",
            "J-League",
            "Australia",
            "A-League",
        ]

    def run(self, fixtures: List[Fixture]) -> List[Fixture]:
        filtered: List[Fixture] = []
        for fixture in fixtures:
            league_lower = fixture.league.lower()
            if any(keyword.lower() in league_lower for keyword in self.allowed_keywords):
                filtered.append(fixture)
        return filtered


class OddsFilterAgent:
    """Keeps fixtures with favourite odds in a practical 2up range.

    The lower bound is deliberately 1.20 rather than 1.40 because low-odds picks
    can still be useful when the bookmaker back price and exchange lay price are
    very close, keeping the qualifying loss low.
    """

    def __init__(
        self,
        min_odds: Optional[float] = 1.20,
        max_odds: Optional[float] = 2.40,
        allow_missing_odds: bool = True,
    ) -> None:
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.allow_missing_odds = allow_missing_odds

    def run(self, fixtures: List[Fixture]) -> List[Fixture]:
        filtered: List[Fixture] = []
        for fixture in fixtures:
            if fixture.favourite_odds is None:
                if self.allow_missing_odds:
                    filtered.append(fixture)
                continue

            if (self.min_odds is None or fixture.favourite_odds >= self.min_odds) and (
                self.max_odds is None or fixture.favourite_odds <= self.max_odds
            ):
                filtered.append(fixture)

        return filtered


class StatsProfileAgent:
    """Extracts favourite and underdog stats from a fixture."""

    @staticmethod
    def get_favourite_stats(fixture: Fixture) -> TeamStats:
        if fixture.favourite.strip().lower() == fixture.home_team.strip().lower():
            return fixture.home_stats
        if fixture.favourite.strip().lower() == fixture.away_team.strip().lower():
            return fixture.away_stats
        raise ValueError(
            f"Favourite '{fixture.favourite}' does not match home or away team "
            f"for {fixture.home_team} vs {fixture.away_team}."
        )

    @staticmethod
    def get_underdog_stats(fixture: Fixture) -> TeamStats:
        if fixture.favourite.strip().lower() == fixture.home_team.strip().lower():
            return fixture.away_stats
        if fixture.favourite.strip().lower() == fixture.away_team.strip().lower():
            return fixture.home_stats
        raise ValueError(
            f"Favourite '{fixture.favourite}' does not match home or away team "
            f"for {fixture.home_team} vs {fixture.away_team}."
        )


class DataQualityAgent:
    """Measures how complete the stats are for a candidate fixture."""

    tracked_fields = [
        "goals_for_avg",
        "goals_against_avg",
        "first_half_goals_avg",
        "clean_sheet_rate",
        "conceded_after_leading_rate",
        "over_25_rate",
    ]

    def run(self, favourite: TeamStats, underdog: TeamStats) -> Tuple[float, List[str], List[str]]:
        total_fields = len(self.tracked_fields) * 2
        known_fields = 0
        missing_fields: List[str] = []
        data_notes: List[str] = []

        for side_name, stats in [("favourite", favourite), ("underdog", underdog)]:
            for field_name in self.tracked_fields:
                value = getattr(stats, field_name)
                label = f"{side_name}.{field_name}"
                if value is None:
                    missing_fields.append(label)
                else:
                    known_fields += 1

        quality = known_fields / total_fields if total_fields else 0.0

        if "favourite.first_half_goals_avg" in missing_fields:
            data_notes.append("Missing favourite first-half scoring data; early-start angle was skipped.")

        if "favourite.conceded_after_leading_rate" in missing_fields:
            data_notes.append("Missing favourite conceded-after-leading data; comeback-volatility angle was skipped.")

        if quality < 0.75:
            data_notes.append("Data quality is incomplete, so confidence has been reduced.")

        return quality, missing_fields, data_notes


class VolatilityAgent:
    """Scores whether a fixture fits the volatile-favourite 2up profile."""

    def __init__(self) -> None:
        self.stats_agent = StatsProfileAgent()
        self.data_quality_agent = DataQualityAgent()

    def run(self, fixture: Fixture) -> Tuple[float, List[str], List[str], List[str], List[str], float]:
        favourite = self.stats_agent.get_favourite_stats(fixture)
        underdog = self.stats_agent.get_underdog_stats(fixture)

        score = 0.0
        reasons: List[str] = []
        risks: List[str] = []

        data_quality, missing_fields, data_notes = self.data_quality_agent.run(favourite, underdog)

        if fixture.favourite_odds is None:
            data_notes.append("Missing favourite odds; odds-range filter was skipped for this fixture.")
        elif fixture.favourite_odds < 1.30:
            score -= 25
            risks.append(
                "Ultra-short favourite price; useful only if qualifying loss is tiny and the match still has real comeback volatility."
            )
            data_notes.append("Low favourite odds; only useful if back/lay closeness keeps qualifying loss low.")
        elif fixture.favourite_odds < 1.40:
            score -= 15
            risks.append(
                "Short favourite price; avoid over-ranking unless the 2UP trigger and comeback angle are both strong."
            )
            data_notes.append("Low favourite odds; only useful if back/lay closeness keeps qualifying loss low.")

        if favourite.goals_for_avg is not None:
            if favourite.goals_for_avg >= 1.8:
                score += 20
                reasons.append(f"{favourite.name} have strong scoring output.")
            elif favourite.goals_for_avg < 1.4:
                score -= 15
                risks.append(f"{favourite.name} may not score enough for a strong 2up angle.")

        if favourite.first_half_goals_avg is not None:
            if favourite.first_half_goals_avg >= 0.8:
                score += 15
                reasons.append(f"{favourite.name} start games well.")

        if underdog.goals_against_avg is not None:
            if underdog.goals_against_avg >= 1.5:
                score += 20
                reasons.append(f"{underdog.name} concede regularly.")
            elif underdog.goals_against_avg < 1.0:
                score -= 15
                risks.append(f"{underdog.name} are not clearly weak defensively.")

        over_25_values = [
            value for value in [favourite.over_25_rate, underdog.over_25_rate]
            if value is not None
        ]
        if over_25_values and max(over_25_values) >= 0.55:
            score += 15
            reasons.append("The match profile suggests goal volatility.")

        if favourite.conceded_after_leading_rate is not None:
            if favourite.conceded_after_leading_rate >= 0.25:
                score += 20
                reasons.append(f"{favourite.name} have shown vulnerability after leading.")

        if favourite.clean_sheet_rate is not None and favourite.clean_sheet_rate >= 0.55:
            score -= 10
            risks.append(
                f"{favourite.name} may be too controlled defensively, reducing comeback angle."
            )

        return score, reasons, risks, data_notes, missing_fields, data_quality


class TwoUpScoringAgent:
    """Turns fixtures into ranked 2up candidates."""

    def __init__(self) -> None:
        self.volatility_agent = VolatilityAgent()

    @staticmethod
    def _base_confidence(score: float) -> str:
        if score >= 65:
            return "High"
        if score >= 45:
            return "Medium"
        return "Low"

    @staticmethod
    def _downgrade_confidence(confidence: str, data_quality: float, odds_missing: bool) -> str:
        order = ["Low", "Medium", "High"]
        index = order.index(confidence)

        if data_quality < 0.50:
            index = max(0, index - 2)
        elif data_quality < 0.75:
            index = max(0, index - 1)

        if odds_missing:
            index = max(0, index - 1)

        return order[index]

    def score_fixture(self, fixture: Fixture) -> TwoUpCandidate:
        score, reasons, risks, data_notes, missing_fields, data_quality = self.volatility_agent.run(fixture)
        base_confidence = self._base_confidence(score)
        confidence = self._downgrade_confidence(
            base_confidence,
            data_quality,
            odds_missing=fixture.favourite_odds is None,
        )

        return TwoUpCandidate(
            fixture=fixture,
            score=round(score, 2),
            reasons=reasons,
            risks=risks,
            data_notes=data_notes,
            missing_fields=missing_fields,
            data_quality=round(data_quality, 2),
            confidence=confidence,
        )

    def run(self, fixtures: List[Fixture]) -> List[TwoUpCandidate]:
        candidates = [self.score_fixture(fixture) for fixture in fixtures]
        return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)


class ReportAgent:
    """Formats candidates into a readable report."""

    @staticmethod
    def _odds_display(odds: Optional[float]) -> str:
        return "Unknown" if odds is None else str(odds)

    def run(self, candidates: List[TwoUpCandidate], limit: int = 3) -> str:
        top_candidates = candidates[:limit]

        if not top_candidates:
            return "No strong 2up candidates found today."

        lines: List[str] = ["# Daily 2up Shortlist", ""]

        for index, candidate in enumerate(top_candidates, start=1):
            fixture = candidate.fixture
            data_quality_percent = int(candidate.data_quality * 100)

            lines.append(f"## {index}. {fixture.home_team} vs {fixture.away_team}")
            lines.append(f"League: {fixture.league}")
            lines.append(f"Kick-off: {fixture.kickoff_uk}")
            lines.append(f"Favourite: {fixture.favourite}")
            lines.append(f"Approx odds: {self._odds_display(fixture.favourite_odds)}")
            lines.append(f"2up score: {candidate.score}")
            lines.append(f"Confidence: {candidate.confidence}")
            lines.append(f"Data quality: {data_quality_percent}%")

            if fixture.source_notes:
                lines.append("")
                lines.append("Source notes / human layer:")
                lines.append(f"- {fixture.source_notes}")

            lines.append("")
            lines.append("Reasons:")
            if candidate.reasons:
                for reason in candidate.reasons:
                    lines.append(f"- {reason}")
            else:
                lines.append("- No strong positive scoring factors were triggered.")

            lines.append("")
            lines.append("Risks:")
            if candidate.risks:
                for risk in candidate.risks:
                    lines.append(f"- {risk}")
            else:
                lines.append("- No major statistical risk flagged from the available data.")

            if candidate.data_notes:
                lines.append("")
                lines.append("Data notes:")
                for note in candidate.data_notes:
                    lines.append(f"- {note}")

            if candidate.missing_fields:
                lines.append("")
                lines.append("Missing fields:")
                for field_name in candidate.missing_fields:
                    lines.append(f"- {field_name}")

            lines.append("")

        return "\n".join(lines)


class TwoUpResearchPipeline:
    """Runs the full narrow-agent 2up research pipeline."""

    def __init__(
        self,
        league_filter: Optional[LeagueFilterAgent] = None,
        odds_filter: Optional[OddsFilterAgent] = None,
        scorer: Optional[TwoUpScoringAgent] = None,
        reporter: Optional[ReportAgent] = None,
    ) -> None:
        self.league_filter = league_filter or LeagueFilterAgent()
        self.odds_filter = odds_filter or OddsFilterAgent()
        self.scorer = scorer or TwoUpScoringAgent()
        self.reporter = reporter or ReportAgent()

    def run(self, fixtures: List[Fixture]) -> str:
        filtered = self.league_filter.run(fixtures)
        filtered = self.odds_filter.run(filtered)
        candidates = self.scorer.run(filtered)
        return self.reporter.run(candidates, limit=3)


__all__ = [
    "TeamStats",
    "Fixture",
    "TwoUpCandidate",
    "LeagueFilterAgent",
    "OddsFilterAgent",
    "StatsProfileAgent",
    "DataQualityAgent",
    "VolatilityAgent",
    "TwoUpScoringAgent",
    "ReportAgent",
    "TwoUpResearchPipeline",
]
