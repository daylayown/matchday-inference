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


_BACK_STORY = {
    "year": "2010",
    "score": "1–1",
    "context_line": "South Africa · opening match · Soccer City",
    "label": "BACK STORY",
    "headline": "The first World Cup match on African soil",
    "paragraphs": ["A thunderbolt, then an equaliser."],
}


def test_render_back_story_video_embed():
    bs = {**_BACK_STORY, "video": {
        "youtube_id": "YrzfY3T_ItQ",
        "title": "Tshabalala v Mexico",
        "caption": "the goal that opened 2010",
        "source": "FIFA · official",
    }}
    out = render_inference(reader=_READER, issue=_ISSUE, team_sheets=[], back_story=bs)
    # The clip the page is about is embedded, with the grunge facade + fallback link.
    assert "YrzfY3T_ItQ" in out
    assert "bs-video-frame" in out
    assert "Roll the tape" in out
    assert "youtube.com/watch?v=YrzfY3T_ItQ" in out  # graceful no-JS fallback


def test_render_back_story_without_video_has_no_embed():
    out = render_inference(reader=_READER, issue=_ISSUE, team_sheets=[], back_story=_BACK_STORY)
    # The CSS class name is always present in <style>; assert the figure itself
    # (and its script) did not render.
    assert "Roll the tape" not in out
    assert "data-yt=" not in out
    assert "youtube" not in out
