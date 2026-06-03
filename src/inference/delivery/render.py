"""Jinja rendering layer for THE INFERENCE.

Composes per-reader issue HTML from generator outputs. The current template
covers: head/header/reader-card, EDITOR section (still hardcoded), TEAM SHEET
sections (templated, loops over team_sheets list), HERE & THERE section
(still hardcoded), footer. As more generators land, more sections template.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..data.models import Match, ReaderProfile, StartingXIEntry

TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class TeamSheetSection:
    """One TEAM SHEET as fed to the template.

    `facts` is the generator's JSON output (structured score, posters, prose).
    `starting_xi` is sourced from the typed Match — the generator doesn't
    re-emit the lineup (wasted tokens; it has the source list already).
    """
    facts: dict[str, Any]
    starting_xi: list[StartingXIEntry]


def build_team_sheet_section(facts: dict[str, Any], match: Match, team_name: str) -> TeamSheetSection:
    side = match.side_for(team_name)
    xi = side.starting_xi if side else []
    return TeamSheetSection(facts=facts, starting_xi=xi)


def render_inference(
    reader: dict[str, Any],
    issue: dict[str, Any],
    team_sheets: list[TeamSheetSection],
    editor: dict[str, Any] | None = None,
    here_there: dict[str, Any] | None = None,
    story_behind_number: dict[str, Any] | None = None,
    back_story: dict[str, Any] | None = None,
    where_played_before: dict[str, Any] | None = None,
    from_the_stands: dict[str, Any] | None = None,
    added_time: dict[str, Any] | None = None,
) -> str:
    """Render the issue HTML. Returns the HTML string.

    Sections that pass `None` are simply omitted (conditional in template).
    """
    return _render("inference.html.j2", autoescape=True,
        reader=reader, issue=issue, team_sheets=team_sheets,
        editor=editor, here_there=here_there,
        story_behind_number=story_behind_number, back_story=back_story,
        where_played_before=where_played_before, from_the_stands=from_the_stands,
        added_time=added_time,
    )


def render_inference_txt(
    reader: dict[str, Any],
    issue: dict[str, Any],
    team_sheets: list[TeamSheetSection],
    editor: dict[str, Any] | None = None,
    here_there: dict[str, Any] | None = None,
    story_behind_number: dict[str, Any] | None = None,
    back_story: dict[str, Any] | None = None,
    where_played_before: dict[str, Any] | None = None,
    from_the_stands: dict[str, Any] | None = None,
    added_time: dict[str, Any] | None = None,
) -> str:
    """Render the plain-text fallback. Strips HTML emphasis tags inline."""
    return _render("inference.txt.j2", autoescape=False,
        reader=reader, issue=issue, team_sheets=team_sheets,
        editor=editor, here_there=here_there,
        story_behind_number=story_behind_number, back_story=back_story,
        where_played_before=where_played_before, from_the_stands=from_the_stands,
        added_time=added_time,
    )


def render_teaser_email(
    *,
    issue_number: str,
    date_human: str,
    date_compact: str,
    headline: str,
    issue_url: str,
    headline_note: str | None = None,
    teaser_line: str | None = None,
    reader_name: str | None = None,
    reader_summary: str | None = None,
    unsubscribe_url: str | None = None,
    year: str | int = 2026,
) -> str:
    """Render the email-safe teaser HTML — the 'envelope' linking to the full
    web issue at `issue_url`. Deliberately plain (tables + inline styles) so it
    survives Gmail/Outlook; the grunge aesthetic lives on the web issue."""
    return _render("teaser.email.html.j2", autoescape=True,
        issue_number=issue_number, date_human=date_human, date_compact=date_compact,
        headline=headline, headline_note=headline_note, teaser_line=teaser_line,
        issue_url=issue_url, reader_name=reader_name, reader_summary=reader_summary,
        unsubscribe_url=unsubscribe_url, year=year,
    )


def render_teaser_text(
    *,
    issue_number: str,
    date_human: str,
    headline: str,
    issue_url: str,
    headline_note: str | None = None,
    teaser_line: str | None = None,
    reader_name: str | None = None,
    reader_summary: str | None = None,
    unsubscribe_url: str | None = None,
    year: str | int = 2026,
) -> str:
    """Plain-text fallback for the teaser email."""
    return _render("teaser.email.txt.j2", autoescape=False,
        issue_number=issue_number, date_human=date_human,
        headline=headline, headline_note=headline_note, teaser_line=teaser_line,
        issue_url=issue_url, reader_name=reader_name, reader_summary=reader_summary,
        unsubscribe_url=unsubscribe_url, year=year,
    )


def _render(template_name: str, *, autoescape: bool, **context: Any) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "j2"]) if autoescape else False,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    template = env.get_template(template_name)
    return template.render(**context)


def reader_to_template_dict(reader: ReaderProfile) -> dict[str, Any]:
    """Flatten a ReaderProfile to the dict the template expects."""
    return {
        "display_name": reader.display_name,
        "teams": reader.teams,
        "teams_short": [_short_code(t) for t in reader.teams],
        "lens": reader.lens,
        "language_label": "English",  # TODO: from reader.language when modelled
    }


def _short_code(team: str) -> str:
    """3-letter code for a team name. Tiny manual map; expand as needed."""
    table = {
        "Argentina": "ARG", "France": "FRA", "Morocco": "MAR", "Brazil": "BRA",
        "Spain": "ESP", "Portugal": "POR", "England": "ENG", "Germany": "GER",
        "Italy": "ITA", "Netherlands": "NED", "Belgium": "BEL", "Mexico": "MEX",
        "USA": "USA", "Croatia": "CRO", "Japan": "JPN", "Senegal": "SEN",
    }
    return table.get(team, team[:3].upper())
