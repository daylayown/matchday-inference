"""Render-layer smoke tests — minimal context, no network.

Also pins the user-facing masthead branding so a regression in the templates
is caught here.
"""

from __future__ import annotations

from inference.delivery.render import (
    render_inference,
    render_inference_txt,
    render_welcome_email,
    render_welcome_text,
)

_READER = {
    "display_name": "Marcus",
    "teams": ["Argentina"],
    "teams_short": ["ARG"],
    "lens": "Cultural Critic",
    "language_label": "English",
}
_ISSUE = {
    "number_str": "04",
    "date_human": "Saturday 14 June 2026",
    "date_compact": "14.06.26",
    "day_short": "Sat",
    "matchday_label": "Matchday 4",
    "page_count": 0,
    "ticker_notes": ["ARGENTINA"],
    "tomorrow": None,
}


def test_render_txt_minimal_has_brand():
    out = render_inference_txt(reader=_READER, issue=_ISSUE, team_sheets=[])
    assert "MATCHDAY INFERENCE" in out
    assert "N° 04" in out


def test_render_html_minimal_has_brand():
    out = render_inference(reader=_READER, issue=_ISSUE, team_sheets=[])
    # Masthead wordmark stays the iconic single word; the lockups carry the full name.
    assert "MATCHDAY INFERENCE N° 04" in out
    assert 'data-text="INFERENCE"' in out


def test_render_welcome_email_personalized():
    out = render_welcome_email(
        reader_name="Nicholas",
        reader_summary="Spain, through the lens of the Historian",
        first_issue_human="Thursday 11 June 2026",
    )
    assert "MATCHDAY INFERENCE" in out
    assert "You're in." in out
    assert "Nicholas" in out
    assert "Spain, through the lens of the Historian" in out
    assert "Thursday 11 June 2026" in out


def test_render_welcome_text_personalized():
    out = render_welcome_text(
        reader_name="Nicholas",
        reader_summary="Spain, through the lens of the Historian",
    )
    assert "You're in." in out
    assert "Nicholas" in out
    assert "Made in Tucson, AZ" in out
