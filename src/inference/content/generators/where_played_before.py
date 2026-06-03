"""WHERE THEY PLAYED BEFORE generator — venue history for a reader's upcoming match.

Takes a venue + a curated list of historical World Cup matches there +
ReaderProfile. Returns a lens-styled retelling of 2-4 anecdotes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "where_played_before.md"


@dataclass
class WherePlayedBeforeOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_where_played_before(
    venue_input: dict[str, Any],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> WherePlayedBeforeOutput:
    """Render one WHERE THEY PLAYED BEFORE for the reader.

    `venue_input` is a dict with:
      - `venue`: dict with name, city, capacity, opened, world_cups (list of years)
      - `historical_matches`: list of dicts with year, body (factual seed)
      - `closer_hint`: optional one-line hint to anchor the closer
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "venue": venue_input["venue"],
        "historical_matches": venue_input["historical_matches"],
        "closer_hint": venue_input.get("closer_hint"),
    }
    user_input = (
        "INPUT (return JSON matching the schema in the system prompt):\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    result = client.generate(
        instructions=instructions,
        input=user_input,
        preset="content",
        json_mode=True,
    )
    return WherePlayedBeforeOutput(facts=json.loads(result.text), generation=result)
