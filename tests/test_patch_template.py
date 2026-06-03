"""Tests for the patch-skeleton generator + drift guard against the orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

from inference.data.patch_template import SEED_KEYS, skeleton_patch
from inference.data.patches import editorial_seed


def test_skeleton_has_all_seed_blocks():
    skel = skeleton_patch("2026-06-11")
    assert skel["date"] == "2026-06-11"
    assert set(skel["editorial_seeds"]) == set(SEED_KEYS)


def test_skeleton_is_json_round_trippable():
    skel = skeleton_patch("2026-06-11")
    # Must survive a JSON round-trip (the CLI writes it to disk).
    assert json.loads(json.dumps(skel)) == skel


def test_skeleton_seeds_readable_by_patch_loader():
    skel = skeleton_patch("2026-06-11")
    for key in SEED_KEYS:
        assert editorial_seed(skel, key) is not None


def test_seed_keys_match_orchestrator_calls():
    """Pin: every SEED_KEY must be one the daily orchestrator actually reads.

    Guards against the template drifting from the pipeline — if someone renames
    a seed key in daily.py, this fails until the template is updated too.
    """
    daily_src = (
        Path(__file__).resolve().parents[1]
        / "src" / "inference" / "orchestrate" / "daily.py"
    ).read_text()
    for key in SEED_KEYS:
        assert f'editorial_seed(patch, "{key}")' in daily_src, (
            f"SEED_KEYS lists {key!r} but daily.py doesn't read it"
        )
