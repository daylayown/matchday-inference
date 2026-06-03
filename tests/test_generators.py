"""Smoke tests for each generator.

Each test mocks the LLM with a known JSON payload, runs the generator, and
verifies:
  1. The generator builds a valid input payload (no exceptions),
  2. The mock receives the prompt file as instructions,
  3. The generator returns the mock's payload as `.facts`,
  4. The GenerationResult cost-tracking surfaces (smoke-level).

These do NOT validate prompt quality — that's the job of running it against
the real model. They catch schema breakage and import regressions.
"""

from __future__ import annotations

from inference.content.generators.added_time import generate_added_time
from inference.content.generators.back_story import generate_back_story
from inference.content.generators.editor import generate_editor
from inference.content.generators.from_the_stands import generate_from_the_stands
from inference.content.generators.here_and_there import generate_here_and_there
from inference.content.generators.story_behind_number import generate_story_behind_number
from inference.content.generators.team_sheet import generate_team_sheet
from inference.content.generators.where_played_before import generate_where_played_before

from .conftest import install_mock


def test_team_sheet(monkeypatch, match, reader):
    payload = {
        "team": "Argentina",
        "result_line": "Lifted the cup.",
        "score_poster": {"home": "Argentina", "home_score": 3, "away": "France",
                         "away_score": 3, "result_tag": "Won 4-2 on penalties"},
        "match_meta": {"formation": "4-3-3", "date_human": "Sunday 18 December 2022",
                       "venue": "Lusail", "round": "Final"},
        "stat_posters": [{"big_num": "6", "label": "Shots on Goal", "note": "Same as France."}],
        "recap_paragraphs": ["A historic final."],
        "pull_quote": None,
        "wildcard_used": False,
    }
    mock = install_mock(monkeypatch, "inference.content.generators.team_sheet", payload)
    out = generate_team_sheet(match, reader, team_name="Argentina")
    assert out.facts == payload
    assert out.generation.cost_usd == 0.001
    assert mock.last_call is not None
    assert "TEAM SHEET" in mock.last_call["instructions"]
    assert mock.last_call["json_mode"] is True


def test_editor(monkeypatch, reader):
    payload = {
        "headline": "ARGENTINA LIFT",
        "headline_note": None,
        "paragraphs": ["Para one."],
        "three_things": [{"lead": "Messi.", "body": "26th match."}],
        "sig": "— from the desk",
        "pull_quote": None,
        "wildcard_used": False,
    }
    mock = install_mock(monkeypatch, "inference.content.generators.editor", payload)
    out = generate_editor({"today_label": "Final", "yesterday_matches": []}, reader)
    assert out.facts == payload
    assert "EDITOR" in mock.last_call["instructions"].upper()


def test_here_and_there(monkeypatch, reader):
    payload = {
        "headline": "Mbappé arrives",
        "dek": "A thread across four meetings.",
        "thread_facts": [{"label": "1930", "fact": "First meeting."}],
        "closer": "Chapter five yesterday.",
        "wildcard_used": False,
    }
    install_mock(monkeypatch, "inference.content.generators.here_and_there", payload)
    thread = {"topic": "ARG vs FRA", "framing": "Four meetings.",
              "facts": [{"label": "1930", "fact": "First."}]}
    out = generate_here_and_there(thread, reader)
    assert out.facts == payload


def test_story_behind_number(monkeypatch, reader):
    payload = {
        "number": "1966",
        "label": "Hat-trick in a final",
        "headline": "Mbappé joins Hurst.",
        "paragraphs": ["The number reaches back."],
        "quick_facts": [{"k": "Mbappé", "v": "3 goals"}],
        "float_note": None,
        "wildcard_used": False,
    }
    install_mock(monkeypatch, "inference.content.generators.story_behind_number", payload)
    number_story = {
        "number": "1966", "surface_stat": "...", "historical_anchor": "...",
        "quick_facts": [{"k": "Mbappé", "v": "3 goals"}],
    }
    out = generate_story_behind_number(number_story, reader)
    assert out.facts == payload


def test_back_story(monkeypatch, reader):
    payload = {
        "label": "Kazan 2018",
        "headline": "Four minutes, two goals.",
        "year": "2018",
        "score": "4 — 3",
        "context_line": "Russia · R16 · Kazan",
        "goals_strip": [{"scorer": "Di María", "minute": "41'", "note": None}],
        "paragraphs": ["A turning point."],
        "closer": "Wednesday, chapter five.",
        "float_note": None,
        "wildcard_used": False,
    }
    install_mock(monkeypatch, "inference.content.generators.back_story", payload)
    bs_input = {
        "teams": ["Argentina", "France"],
        "focus_meeting": {"year": "2018", "score": "4-3", "goals": []},
        "ledger": "ARG 2, FRA 1",
    }
    out = generate_back_story(bs_input, reader)
    assert out.facts == payload


def test_where_played_before(monkeypatch, reader):
    payload = {
        "venue_display": "Lusail",
        "venue_meta": "Lusail · 88,966 · 2021",
        "world_cups_label": "One World Cup · 2022",
        "heading": "What's happened here.",
        "historical_matches": [{"year": "2022", "body": "Final.", "sub": None}],
        "closer": "Argentina's home.",
        "wildcard_used": False,
    }
    install_mock(monkeypatch, "inference.content.generators.where_played_before", payload)
    venue_input = {
        "venue": {"name": "Lusail", "city": "Lusail", "capacity": 88966,
                  "opened": 2021, "world_cups": [2022]},
        "historical_matches": [{"year": "2022", "body": "Final."}],
    }
    out = generate_where_played_before(venue_input, reader)
    assert out.facts == payload


def test_from_the_stands(monkeypatch, reader):
    payload = {
        "section_label": "From the Mixed Zone · Sun 18 Dec · Reader: Mateo, Rosario",
        "question": "Why did Deschamps sub at half-time?",
        "answer_html": "Because the shape was cold.",
        "cta_line": "Got a question?",
        "cta_tease": "Tomorrow's Q",
        "float_note": None,
        "wildcard_used": False,
    }
    install_mock(monkeypatch, "inference.content.generators.from_the_stands", payload)
    qa = {
        "asker_name": "Mateo", "asker_city": "Rosario", "asker_day": "Sun 18 Dec",
        "question": "Why did Deschamps sub at half-time?",
        "factual_brief": {"facts": ["..."]},
    }
    out = generate_from_the_stands(qa, reader)
    assert out.facts == payload


def test_added_time(monkeypatch, reader):
    payload = {
        "headline": "Added Time",
        "dek": "Notes.",
        "notes": [{"kicker": "Hat-trick.", "body": "Three, and still lost."}],
        "closer": "Some finals end.",
        "float_note": None,
        "wildcard_used": False,
    }
    install_mock(monkeypatch, "inference.content.generators.added_time", payload)
    anomalies = [{"tag": "Mbappé hat-trick", "seed": "Three goals, lost."}]
    out = generate_added_time(anomalies, reader)
    assert out.facts == payload
