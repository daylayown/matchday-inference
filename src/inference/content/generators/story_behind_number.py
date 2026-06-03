"""STORY BEHIND THE NUMBER generator — one stat, at scale.

Takes a number-story payload (the figure, its label, the historical anchor,
quick supporting facts) + ReaderProfile. Returns lens-styled prose that
makes the number feel weighty.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "story_behind_number.md"


@dataclass
class StoryBehindNumberOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_story_behind_number(
    number_story: dict[str, Any],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> StoryBehindNumberOutput:
    """Render one STORY BEHIND THE NUMBER for the reader.

    `number_story` is a dict with:
      - `number`: the headline figure (str, e.g. "1934" or "0" or "64%")
      - `surface_stat`: the stat as one line, e.g. "Italy · 0 shots on target vs Norway"
      - `historical_anchor`: e.g. "Last time this happened to Italy at a WC: 1934, Pozzo's team"
      - `quick_facts`: 2-4 dicts with k, v
      - `supporting_context`: optional list of background facts
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "number_story": number_story,
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
    return StoryBehindNumberOutput(facts=json.loads(result.text), generation=result)
