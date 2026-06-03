"""ADDED TIME generator — closing anomalies kicker.

Takes a list of candidate anomalies + ReaderProfile. Returns 3-5
lens-styled notes that tail-end the issue.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "added_time.md"


@dataclass
class AddedTimeOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_added_time(
    anomalies: list[dict[str, Any]],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> AddedTimeOutput:
    """Render one ADDED TIME for the reader.

    `anomalies` is a list of dicts with at least a `seed` factual one-liner;
    optional `tag` for a topic hint. The generator picks the best 3-5.
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "anomalies": anomalies,
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
    return AddedTimeOutput(facts=json.loads(result.text), generation=result)
