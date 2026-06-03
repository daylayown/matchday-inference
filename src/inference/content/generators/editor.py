"""EDITOR generator — the day's universal-but-lens-shaped tournament column.

Takes a DayContext (the day's matches, tournament arc, context notes) plus
the ReaderProfile (to lock the lens). Returns headline, paragraphs, three
things, sig, and optional pull-quote.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "editor.md"


@dataclass
class EditorOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_editor(
    day_context: dict[str, Any],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> EditorOutput:
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "day_context": day_context,
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
    return EditorOutput(facts=json.loads(result.text), generation=result)
