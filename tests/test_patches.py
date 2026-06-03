"""Smoke tests for the patches loader."""

from __future__ import annotations

import json

from inference.data.patches import (
    apply_fixture_overrides,
    apply_stat_overrides,
    day_context_overrides,
    editorial_notes_for,
    editorial_seed,
    load_patch,
)


def test_load_patch_missing(tmp_path):
    assert load_patch("2099-01-01", patches_dir=tmp_path) == {}


def test_load_patch_present(tmp_path):
    (tmp_path / "2026-06-11.json").write_text(json.dumps({"note": "hello"}))
    patch = load_patch("2026-06-11", patches_dir=tmp_path)
    assert patch == {"note": "hello"}


def test_apply_fixture_overrides_empty_patch():
    inp = {"fixture": {"id": 1, "referee": "Original"}, "goals": {"home": 1}}
    out = apply_fixture_overrides(inp, {})
    assert out == inp
    assert out is inp  # no copy when no override


def test_apply_fixture_overrides_with_patch():
    inp = {"fixture": {"id": 42, "referee": "Original", "venue": {"name": "Stadium"}}}
    patch = {"fixtures": {"42": {"fixture": {"referee": "Corrected"}}}}
    out = apply_fixture_overrides(inp, patch)
    assert out["fixture"]["referee"] == "Corrected"
    assert out["fixture"]["id"] == 42
    assert out["fixture"]["venue"] == {"name": "Stadium"}  # preserved
    assert inp["fixture"]["referee"] == "Original"  # not mutated


def test_apply_stat_overrides():
    stats = [
        {"team": {"name": "Argentina"},
         "statistics": [{"type": "Shots", "value": 10}]},
        {"team": {"name": "France"},
         "statistics": [{"type": "Shots", "value": 8}]},
    ]
    patch = {"fixtures": {"42": {"stat_overrides": {
        "Argentina": {"Shots": 12, "Possession": "55%"}
    }}}}
    out = apply_stat_overrides(stats, 42, patch)
    arg_stats = {s["type"]: s["value"] for s in out[0]["statistics"]}
    assert arg_stats["Shots"] == 12
    assert arg_stats["Possession"] == "55%"
    # France untouched
    fra_stats = {s["type"]: s["value"] for s in out[1]["statistics"]}
    assert fra_stats["Shots"] == 8


def test_editorial_seed():
    patch = {"editorial_seeds": {"back_story": {"teams": ["A", "B"]}}}
    assert editorial_seed(patch, "back_story") == {"teams": ["A", "B"]}
    assert editorial_seed(patch, "missing_seed") is None
    assert editorial_seed({}, "back_story") is None


def test_editorial_notes_for():
    patch = {"fixtures": {"42": {"editorial_notes": ["a", "b"]}}}
    assert editorial_notes_for(42, patch) == ["a", "b"]
    assert editorial_notes_for(99, patch) == []


def test_day_context_overrides():
    patch = {"day_context": {"today_label": "Opening Day", "context_notes": ["x"]}}
    assert day_context_overrides(patch) == {"today_label": "Opening Day", "context_notes": ["x"]}
    assert day_context_overrides({}) == {}
