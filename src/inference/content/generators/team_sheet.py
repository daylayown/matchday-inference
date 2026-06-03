"""TEAM SHEET generator — one of the reader's teams on one day.

Input: a typed Match and a ReaderProfile.
Output: structured JSON (parsed dict) per the prompt's contract, plus the
GenerationResult so callers can inspect tokens/cost/timing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import Match, ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "team_sheet.md"


@dataclass
class TeamSheetOutput:
    facts: dict[str, Any]   # the structured JSON from the model
    generation: GenerationResult


def _build_input(match: Match, reader: ReaderProfile, team_name: str) -> str:
    side = match.side_for(team_name)
    opponent = match.opponent_of(team_name)
    if side is None or opponent is None:
        raise ValueError(f"team {team_name!r} not in match {match.fixture_id}")

    # Compact payload — only what the prompt needs. The full Match has more
    # detail; the prompt's factual discipline rule says "use only what's
    # given", so we send only what's relevant.
    payload = {
        "reader_profile": reader.model_dump(),
        "team_focus": team_name,
        "match": {
            "fixture_id": match.fixture_id,
            "date_iso": match.date_iso,
            "venue": match.venue,
            "referee": match.referee,
            "round": match.round,
            "status_long": match.status_long,
            "status_short": match.status_short,
            "our_side": side.model_dump(),
            "opponent": opponent.model_dump(),
            "penalty_us": _penalty_for(match, team_name),
            "penalty_them": _penalty_against(match, team_name),
            "events": [e.model_dump() for e in match.events],
        },
    }
    # Prefix line satisfies Responses API's json_object requirement that the
    # input contains the literal word "json".
    return (
        "INPUT (return JSON matching the schema in the system prompt):\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def _penalty_for(match: Match, team_name: str) -> int | None:
    if match.home.name.lower() == team_name.lower():
        return match.penalty_home
    if match.away.name.lower() == team_name.lower():
        return match.penalty_away
    return None


def _penalty_against(match: Match, team_name: str) -> int | None:
    if match.home.name.lower() == team_name.lower():
        return match.penalty_away
    if match.away.name.lower() == team_name.lower():
        return match.penalty_home
    return None


def generate_team_sheet(
    match: Match,
    reader: ReaderProfile,
    team_name: str,
    *,
    client: ContentClient | None = None,
) -> TeamSheetOutput:
    """Generate a TEAM SHEET for `team_name` on `match` for `reader`.

    Caller may pass a shared ContentClient; otherwise a fresh one is built.
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = _build_input(match, reader, team_name)
    result = client.generate(
        instructions=instructions,
        input=payload,
        preset="content",
        json_mode=True,
    )
    facts = json.loads(result.text)
    return TeamSheetOutput(facts=facts, generation=result)
