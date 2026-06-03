"""BACK STORY generator — head-to-head history between two of the reader's teams.

Takes a focus h2h meeting + the broader ledger + ReaderProfile. Returns a
lens-styled retelling of the focus match, anchored by a closer that ties
to the present.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "back_story.md"


@dataclass
class BackStoryOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_back_story(
    back_story_input: dict[str, Any],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> BackStoryOutput:
    """Render one BACK STORY for the reader.

    `back_story_input` is a dict with:
      - `teams`: list of 2 strings, e.g. ["Argentina", "Mexico"]
      - `focus_meeting`: dict with year, score, host, round, venue, goals (list), narrative_beats (list)
      - `ledger`: optional summary of the broader h2h record
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "teams": back_story_input["teams"],
        "focus_meeting": back_story_input["focus_meeting"],
        "ledger": back_story_input.get("ledger"),
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
    return BackStoryOutput(facts=json.loads(result.text), generation=result)
