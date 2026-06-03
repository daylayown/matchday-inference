"""Build typed Match objects from API-Football raw JSON.

Takes the four endpoints we need for a complete match view:
  /fixtures (single fixture entry)
  /fixtures/lineups
  /fixtures/events
  /fixtures/statistics

Penalty-shootout handling: API-Football returns regulation+ET score in
`goals.{home,away}`. If `status.short == "PEN"`, the shootout result is in
`score.penalty.{home,away}`. We surface both so the generator can describe
the actual outcome correctly.
"""

from __future__ import annotations

from typing import Any

from .models import Match, MatchEvent, StartingXIEntry, TeamMatchSide


def extract_match(
    fixture_entry: dict[str, Any],
    lineups: list[dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
    statistics: list[dict[str, Any]] | None = None,
) -> Match:
    """Compose a Match from API-Football raw responses for one fixture.

    `fixture_entry` is a single object from `GET /fixtures` (already indexed,
    not the wrapping {"response": [...]}). The other three are likewise the
    `response` lists for that fixture.
    """
    fix = fixture_entry["fixture"]
    teams = fixture_entry["teams"]
    goals = fixture_entry["goals"]
    score = fixture_entry.get("score") or {}
    league = fixture_entry.get("league") or {}

    penalty = score.get("penalty") or {}

    home_side = _build_side(
        teams["home"]["name"],
        goals["home"] or 0,
        lineups=lineups,
        statistics=statistics,
        is_home=True,
    )
    away_side = _build_side(
        teams["away"]["name"],
        goals["away"] or 0,
        lineups=lineups,
        statistics=statistics,
        is_home=False,
    )

    return Match(
        fixture_id=fix["id"],
        date_iso=fix["date"],
        venue=(fix.get("venue") or {}).get("name"),
        referee=fix.get("referee"),
        season=league.get("season"),
        round=league.get("round"),
        status_long=(fix.get("status") or {}).get("long", ""),
        status_short=(fix.get("status") or {}).get("short", ""),
        home=home_side,
        away=away_side,
        penalty_home=penalty.get("home"),
        penalty_away=penalty.get("away"),
        events=[_event(e) for e in (events or [])],
    )


def _build_side(
    name: str,
    score: int,
    lineups: list[dict[str, Any]] | None,
    statistics: list[dict[str, Any]] | None,
    is_home: bool,
) -> TeamMatchSide:
    lineup_block = _find_team_block(lineups, name)
    stat_block = _find_team_block(statistics, name)

    formation = (lineup_block or {}).get("formation")
    coach = ((lineup_block or {}).get("coach") or {}).get("name")
    xi = [_xi_entry(p) for p in ((lineup_block or {}).get("startXI") or [])]
    stats = _stats_dict((stat_block or {}).get("statistics") or [])

    return TeamMatchSide(
        name=name,
        score_regulation=score,
        formation=formation,
        coach=coach,
        starting_xi=xi,
        statistics=stats,
    )


def _find_team_block(blocks: list[dict[str, Any]] | None, team_name: str) -> dict[str, Any] | None:
    if not blocks:
        return None
    for b in blocks:
        if (b.get("team") or {}).get("name", "").lower() == team_name.lower():
            return b
    return None


def _xi_entry(entry: dict[str, Any]) -> StartingXIEntry:
    p = entry.get("player") or {}
    return StartingXIEntry(
        number=p.get("number"),
        name=p.get("name") or "?",
        position=p.get("pos"),
        grid=p.get("grid"),
    )


def _stats_dict(stat_list: list[dict[str, Any]]) -> dict[str, str | int | None]:
    """Convert API-Football's [{type, value}, ...] into a flat dict."""
    out: dict[str, str | int | None] = {}
    for s in stat_list:
        t = s.get("type")
        v = s.get("value")
        if t is not None:
            out[t] = v
    return out


def _event(raw: dict[str, Any]) -> MatchEvent:
    time_block = raw.get("time") or {}
    team_block = raw.get("team") or {}
    player_block = raw.get("player") or {}
    assist_block = raw.get("assist") or {}
    return MatchEvent(
        minute=time_block.get("elapsed") or 0,
        extra=time_block.get("extra"),
        team=team_block.get("name") or "?",
        player=player_block.get("name"),
        assist=assist_block.get("name"),
        type=raw.get("type") or "?",
        detail=raw.get("detail"),
        comments=raw.get("comments"),
    )
