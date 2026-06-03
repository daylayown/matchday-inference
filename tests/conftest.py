"""Shared fixtures for the test suite.

Mocks the OpenAI Responses API. No network calls during tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from inference.content.api import ContentClient, GenerationResult
from inference.data.models import (
    Match,
    MatchEvent,
    ReaderProfile,
    StartingXIEntry,
    TeamMatchSide,
)


@dataclass
class MockResponse:
    text: str


class MockClient:
    """Drop-in replacement for ContentClient that returns a canned payload.

    Tests inject a JSON string; the wrapper packages it as a GenerationResult.
    """

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.last_call: dict[str, Any] | None = None

    def generate(self, instructions: str, input: Any, preset: str = "content",
                 json_mode: bool = False, **overrides: Any) -> GenerationResult:
        self.last_call = {
            "instructions": instructions,
            "input": input,
            "preset": preset,
            "json_mode": json_mode,
            "overrides": overrides,
        }
        return GenerationResult(
            text=json.dumps(self.payload),
            model="gpt-5.5-mock",
            input_tokens=100,
            output_tokens=200,
            reasoning_tokens=50,
            cost_usd=0.001,
            elapsed_seconds=0.0,
            raw=None,
        )


@pytest.fixture
def reader() -> ReaderProfile:
    return ReaderProfile(
        slug="testuser",
        display_name="Tester",
        teams=["Argentina", "France"],
        players=["Lionel Messi"],
        lens="Cultural Critic",
        length="Standard",
        wildcard=None,
        location="Brooklyn, NY",
    )


@pytest.fixture
def match() -> Match:
    """A minimal ARG-FRA Match good enough for prompts."""
    arg = TeamMatchSide(
        name="Argentina",
        score_regulation=3,
        formation="4-3-3",
        coach="Scaloni",
        starting_xi=[
            StartingXIEntry(number=23, name="E. Martínez", position="G", grid="1:1"),
            StartingXIEntry(number=10, name="L. Messi", position="F", grid="3:1"),
        ],
        statistics={"Shots on Goal": 6, "Total Shots": 17, "Ball Possession": "46%"},
    )
    fra = TeamMatchSide(
        name="France",
        score_regulation=3,
        formation="4-2-3-1",
        coach="Deschamps",
        starting_xi=[
            StartingXIEntry(number=1, name="H. Lloris", position="G", grid="1:1"),
            StartingXIEntry(number=10, name="K. Mbappé", position="F", grid="3:1"),
        ],
        statistics={"Shots on Goal": 6, "Total Shots": 18, "Ball Possession": "54%"},
    )
    return Match(
        fixture_id=979139,
        date_iso="2022-12-18T15:00:00+00:00",
        venue="Lusail Iconic Stadium",
        referee="Szymon Marciniak",
        season=2022,
        round="Final",
        status_long="Match Finished",
        status_short="PEN",
        home=arg,
        away=fra,
        penalty_home=4,
        penalty_away=2,
        events=[
            MatchEvent(minute=23, team="Argentina", player="L. Messi",
                       type="Goal", detail="Penalty"),
            MatchEvent(minute=80, team="France", player="K. Mbappé",
                       type="Goal", detail="Penalty"),
        ],
    )


def install_mock(monkeypatch, module_path: str, payload: dict[str, Any]) -> MockClient:
    """Install a MockClient as the default ContentClient inside `module_path`."""
    mock = MockClient(payload)
    monkeypatch.setattr(module_path + ".ContentClient", lambda *a, **k: mock)
    return mock
