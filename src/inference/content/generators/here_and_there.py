"""HERE & THERE generator — personalized heritage thread.

Takes a thread (topic, framing, facts list) + ReaderProfile. Rewrites the
thread in the reader's lens. Heritage facts are the source of truth — the
generator transforms voice, not adds invention.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...data.models import ReaderProfile
from ..api import ContentClient, GenerationResult

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "here_and_there.md"


@dataclass
class HereAndThereOutput:
    facts: dict[str, Any]
    generation: GenerationResult


def generate_here_and_there(
    thread: dict[str, Any],
    reader: ReaderProfile,
    *,
    client: ContentClient | None = None,
) -> HereAndThereOutput:
    """Render one HERE & THERE thread for the reader.

    `thread` is a dict with at least: `topic` (str), `framing` (str),
    `facts` (list[dict{label, fact}]).
    """
    client = client or ContentClient()
    instructions = PROMPT_FILE.read_text()
    payload = {
        "reader_profile": reader.model_dump(),
        "thread_topic": thread["topic"],
        "thread_framing": thread["framing"],
        "thread_facts": thread["facts"],
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
    return HereAndThereOutput(facts=json.loads(result.text), generation=result)
