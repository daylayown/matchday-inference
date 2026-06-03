"""Local patch layer for THE INFERENCE.

Per `api-research.md`: API-Football is the sole live provider; editorial
corrections, missing context, and overrides live in
`data/patches/YYYY-MM-DD.json` — a manual layer applied AFTER the API fetch
and BEFORE generation.

Patch file shape (all keys optional — write only what you need):

```json
{
  "date": "2026-06-11",
  "note": "Free-form human note about why this patch exists.",
  "fixtures": {
    "1234567": {
      "fixture":   { "referee": "Corrected name" },
      "stat_overrides": { "Argentina": { "Shots on Goal": 10 } },
      "editorial_notes": ["Argentina's first WC final since 1990"]
    }
  },
  "day_context": {
    "today_label": "Matchday 1",
    "context_notes": ["Opening match of the tournament"]
  },
  "editorial_seeds": {
    "story_behind_number": { "number": "1934", "...": "..." },
    "back_story":          { "teams": ["...", "..."], "...": "..." },
    "where_played_before": { "venue": { "name": "..." }, "...": "..." },
    "from_the_stands":     { "asker_name": "...", "...": "..." },
    "anomalies":           [ { "tag": "...", "seed": "..." } ],
    "here_there_thread":   { "topic": "...", "facts": [] }
  }
}
```

The loader returns the raw dict; callers reach into the slices they need.
There's no validation here — that's the generators' job, since each one has
its own schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_PATCHES_DIR = Path("data/patches")


def load_patch(date_iso: str, patches_dir: Path = DEFAULT_PATCHES_DIR) -> dict[str, Any]:
    """Load the patch JSON for `date_iso` (e.g. "2026-06-11"). Empty dict if none."""
    path = patches_dir / f"{date_iso}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def apply_fixture_overrides(fixture_entry: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Apply patch overrides to one raw API-Football fixture entry.

    Returns a NEW dict — does not mutate the input. The patch's `fixtures.<id>.fixture`
    sub-block is deep-merged into the input's `fixture` sub-block.
    """
    fixture_id = str((fixture_entry.get("fixture") or {}).get("id"))
    overrides = (patch.get("fixtures") or {}).get(fixture_id) or {}
    fixture_override = overrides.get("fixture") or {}
    if not fixture_override:
        return fixture_entry

    out = _deep_copy(fixture_entry)
    out["fixture"] = _deep_merge(out.get("fixture") or {}, fixture_override)
    return out


def apply_stat_overrides(
    statistics: list[dict[str, Any]],
    fixture_id: int,
    patch: dict[str, Any],
) -> list[dict[str, Any]]:
    """Apply per-team stat overrides to API-Football's `/fixtures/statistics` response.

    Patch shape: `fixtures.<id>.stat_overrides.<TeamName>.<StatName>` → new value.
    Returns a new list; does not mutate.
    """
    fixture_overrides = (patch.get("fixtures") or {}).get(str(fixture_id)) or {}
    stat_overrides = fixture_overrides.get("stat_overrides") or {}
    if not stat_overrides:
        return statistics

    out: list[dict[str, Any]] = []
    for team_block in statistics:
        team_name = (team_block.get("team") or {}).get("name", "")
        per_team = stat_overrides.get(team_name)
        if not per_team:
            out.append(team_block)
            continue

        new_block = _deep_copy(team_block)
        stats = list(new_block.get("statistics") or [])
        seen = {s.get("type"): i for i, s in enumerate(stats)}
        for stat_name, new_value in per_team.items():
            if stat_name in seen:
                stats[seen[stat_name]] = {"type": stat_name, "value": new_value}
            else:
                stats.append({"type": stat_name, "value": new_value})
        new_block["statistics"] = stats
        out.append(new_block)
    return out


def editorial_notes_for(fixture_id: int, patch: dict[str, Any]) -> list[str]:
    """Editorial-only notes attached to a fixture in the patch. Empty list if none."""
    fixture_overrides = (patch.get("fixtures") or {}).get(str(fixture_id)) or {}
    return list(fixture_overrides.get("editorial_notes") or [])


def editorial_seed(patch: dict[str, Any], generator_key: str) -> Any:
    """Return the editorial seed payload for a named generator, or None.

    `generator_key` is one of: 'story_behind_number', 'back_story',
    'where_played_before', 'from_the_stands', 'anomalies', 'here_there_thread'.
    """
    return (patch.get("editorial_seeds") or {}).get(generator_key)


def day_context_overrides(patch: dict[str, Any]) -> dict[str, Any]:
    """Day-level overrides (today_label, context_notes, etc.). Empty dict if none."""
    return dict(patch.get("day_context") or {})


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Recursive dict merge — overrides win at every level. Returns a new dict."""
    out = _deep_copy(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = _deep_copy(v)
    return out


def _deep_copy(obj: Any) -> Any:
    """JSON-safe deep copy (everything our patches handle is JSON-shaped)."""
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(v) for v in obj]
    return obj
