"""FROM THE STANDS generator — reader Q&A snippet.

Takes a Q (from another reader, verbatim) + a factual brief grounding the
answer + ReaderProfile. Returns a lens-styled answer paired with the
verbatim question.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "from_the_stands.md"


@dataclass
class FromTheStandsOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_from_the_stands(
    qa: dict[str, Any],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> FromTheStandsOutput:
    """Render one FROM THE STANDS for the reader.

    `qa` is a dict with:
      - `asker_name`: str
      - `asker_city`: str
      - `asker_day`: str  # e.g. "Sat 13 Jun"
      - `question`: str  # verbatim
      - `factual_brief`: dict | str  # source facts the answer must use
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "qa": qa,
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
    return FromTheStandsOutput(facts=json.loads(result.text), generation=result)
