"""Skeleton generator for daily editorial patches.

The patch file is the only manual content step in the pipeline (see
`patches.py`). `skeleton_patch(date_iso)` emits a fill-in-the-blanks dict with
every editorial-seed block the orchestrator looks for, each field stubbed with
a `TODO:` placeholder and the right *shape* so an editor just overwrites
strings instead of remembering the schema.

The editorial-seed keys here are kept in lockstep with the keys the daily
orchestrator reads via `editorial_seed(patch, ...)`. A test pins them together
so the template can't silently drift from what the pipeline consumes.
"""

from __future__ import annotations

from typing import Any

# The editorial-seed blocks the orchestrator runs a generator for, in page order.
# Must match the `editorial_seed(patch, <key>)` calls in orchestrate/daily.py.
SEED_KEYS = (
    "here_there_thread",
    "story_behind_number",
    "back_story",
    "where_played_before",
    "from_the_stands",
    "anomalies",
)

_TODO = "TODO: "


def skeleton_patch(date_iso: str) -> dict[str, Any]:
    """Return a placeholder patch dict for `date_iso` (e.g. '2026-06-11').

    Every value is a TODO placeholder; the structure mirrors the shapes the
    generators expect (see `data/patches/2022-12-18.json` for a filled example).
    Delete any seed block you don't want for the day — a missing seed cleanly
    omits that section rather than inventing content.
    """
    return {
        "date": date_iso,
        "note": _TODO + "one-line reason this patch exists / what's notable today",
        "fixtures": {
            # "<fixture_id>": {
            #   "fixture": {"referee": "..."},
            #   "stat_overrides": {"<Team>": {"Shots on Goal": 0}},
            #   "editorial_notes": ["..."]
            # }
        },
        "day_context": {
            "today_label": _TODO + "e.g. 'Matchday 1 — the tournament opens'",
            "tournament_summary": _TODO + "where the tournament stands this morning",
            "context_notes": [_TODO + "bullet of standings/storyline context"],
        },
        "editorial_seeds": {
            "here_there_thread": {
                "topic": _TODO + "the thread tying two places/teams together",
                "framing": _TODO + "a sentence framing why the thread matters today",
                "facts": [
                    {"label": _TODO + "year/place tag", "fact": _TODO + "the fact"},
                ],
            },
            "story_behind_number": {
                "number": _TODO + "the headline number (e.g. '1966')",
                "surface_stat": _TODO + "the stat as it appears on the surface",
                "historical_anchor": _TODO + "what the number really points back to",
                "quick_facts": [
                    {"k": _TODO + "label", "v": _TODO + "value"},
                ],
                "supporting_context": [_TODO + "a supporting sentence"],
            },
            "back_story": {
                "teams": [_TODO + "Team A", _TODO + "Team B"],
                "focus_meeting": {
                    "year": _TODO + "YYYY",
                    "score": _TODO + "e.g. '4 — 3'",
                    "host": _TODO + "host nation",
                    "round": _TODO + "e.g. 'Round of 16'",
                    "venue": _TODO + "stadium, city",
                    "context_line": _TODO + "host · round · venue",
                    "goals": [
                        {"scorer": _TODO + "name", "minute": _TODO + "e.g. \"41'\"", "note": None},
                    ],
                    "narrative_beats": [_TODO + "a beat of the story"],
                },
                "ledger": _TODO + "the head-to-head ledger before today",
            },
            "where_played_before": {
                "venue": {
                    "name": _TODO + "stadium name",
                    "city": _TODO + "city, country",
                    "capacity": 0,
                    "opened": 0,
                    "world_cups": [],
                },
                "historical_matches": [
                    {"year": _TODO + "YYYY", "body": _TODO + "what happened here"},
                ],
                "closer_hint": _TODO + "a closing line about the venue",
            },
            "from_the_stands": {
                "asker_name": _TODO + "reader first name",
                "asker_city": _TODO + "reader city",
                "asker_day": _TODO + "e.g. 'Sun 14 Jun'",
                "question": _TODO + "the reader's question",
                "factual_brief": {
                    "facts": [_TODO + "a fact that answers the question"],
                    "note": _TODO + "what the brief shows vs. what the question assumes",
                },
            },
            "anomalies": [
                {"tag": _TODO + "short tag", "seed": _TODO + "the odd/notable thing"},
            ],
        },
    }
