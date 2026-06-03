"""Tests for the run_day script's reader loading (shape tolerance)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_day.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_day_script", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def run_day():
    return _load_module()


def _write_readers(tmp_path: Path, payload) -> Path:
    p = tmp_path / "readers.json"
    p.write_text(json.dumps(payload))
    return p


SAMPLE = {
    "slug": "marcus",
    "display_name": "Marcus",
    "teams": ["Argentina"],
    "lens": "Cultural Critic",
}


def test_load_readers_bare_list(run_day, tmp_path, monkeypatch):
    monkeypatch.setattr(run_day, "READERS_FILE", _write_readers(tmp_path, [SAMPLE]))
    readers = run_day._load_readers("json")
    assert len(readers) == 1
    assert readers[0].slug == "marcus"


def test_load_readers_export_envelope(run_day, tmp_path, monkeypatch):
    # The /export endpoint returns {"readers": [...]}; daily.yml writes it raw.
    monkeypatch.setattr(run_day, "READERS_FILE", _write_readers(tmp_path, {"readers": [SAMPLE]}))
    readers = run_day._load_readers("json")
    assert len(readers) == 1
    assert readers[0].slug == "marcus"
