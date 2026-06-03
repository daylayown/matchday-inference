"""Pydantic models for THE INFERENCE.

Only the fields the current generators actually use. Grow this as new
generators land — do not pre-model speculatively.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Lens = Literal[
    "Cultural Critic",
    "Pub-Talker",
    "Tactician",
    "Romantic",
    "Historian",
    "The Diaspora",
    "The Beat Reporter",
]
Length = Literal["Sprint", "Standard", "Long-read"]
EventType = Literal["Goal", "Card", "subst", "Var"]


class ReaderProfile(BaseModel):
    slug: str
    display_name: str
    teams: list[str]
    players: list[str] = Field(default_factory=list)
    lens: Lens
    length: Length = "Standard"
    wildcard: str | None = None
    location: str | None = None  # city or city + country; The Diaspora lens anchors on this


class StartingXIEntry(BaseModel):
    number: int | None
    name: str
    position: str | None
    grid: str | None = None  # formation slot like "2:1"


class MatchEvent(BaseModel):
    minute: int
    extra: int | None = None
    team: str
    player: str | None = None
    assist: str | None = None
    type: str          # API-Football: "Goal", "Card", "subst", "Var"
    detail: str | None = None  # e.g. "Normal Goal", "Yellow Card", "Penalty"
    comments: str | None = None


class TeamMatchSide(BaseModel):
    """One team's view of a single match."""
    name: str
    code: str | None = None  # short code if we have one
    score_regulation: int
    formation: str | None = None
    coach: str | None = None
    starting_xi: list[StartingXIEntry] = Field(default_factory=list)
    statistics: dict[str, str | int | None] = Field(default_factory=dict)


class Match(BaseModel):
    fixture_id: int
    date_iso: str
    venue: str | None = None
    referee: str | None = None
    league: str = "World Cup"
    season: int | None = None
    round: str | None = None
    status_long: str  # e.g. "Match Finished"
    status_short: str  # e.g. "FT", "PEN", "AET"
    home: TeamMatchSide
    away: TeamMatchSide
    penalty_home: int | None = None  # if went to penalties
    penalty_away: int | None = None
    events: list[MatchEvent] = Field(default_factory=list)

    def side_for(self, team_name: str) -> TeamMatchSide | None:
        if self.home.name.lower() == team_name.lower():
            return self.home
        if self.away.name.lower() == team_name.lower():
            return self.away
        return None

    def opponent_of(self, team_name: str) -> TeamMatchSide | None:
        if self.home.name.lower() == team_name.lower():
            return self.away
        if self.away.name.lower() == team_name.lower():
            return self.home
        return None
