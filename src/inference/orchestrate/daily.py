"""Daily pipeline orchestrator for THE INFERENCE.

One call: `run_for_date(date_iso, readers)`. For each reader, fetches that
day's fixtures, applies patches, runs the relevant generators, renders the
HTML, writes it to disk, and returns a structured result with paths +
cost + timing.

This is the production spine — the GH Actions cron will call this. It does
NOT send email; the caller (or a separate dispatch step) does that.

Editorial seeds (story_behind_number, back_story, where_played_before,
from_the_stands, anomalies, here_there_thread) come from
`data/patches/<date>.json` under `editorial_seeds`. If a seed is missing,
that section is omitted for the day — there's no AI fallback for
"invent a back story between Brazil and Germany." Editorial humans pick
the threads; the AI writes them in the reader's voice.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..content.api import ContentClient, GenerationResult
from ..content.generators.added_time import generate_added_time
from ..content.generators.back_story import generate_back_story
from ..content.generators.editor import generate_editor
from ..content.generators.from_the_stands import generate_from_the_stands
from ..content.generators.here_and_there import generate_here_and_there
from ..content.generators.story_behind_number import generate_story_behind_number
from ..content.generators.team_sheet import generate_team_sheet
from ..content.generators.where_played_before import generate_where_played_before
from ..data.api_football import APIFootballClient
from ..data.extract import extract_match
from ..data.models import Match, ReaderProfile
from ..data.patches import (
    apply_fixture_overrides,
    apply_stat_overrides,
    day_context_overrides,
    editorial_seed,
    load_patch,
)
from ..delivery.render import (
    build_team_sheet_section,
    reader_to_template_dict,
    render_inference,
    render_inference_txt,
)

WC_LEAGUE_ID = 1
DEFAULT_OUTPUT_DIR = Path("output/inferences")


@dataclass
class GeneratorRun:
    label: str
    facts: dict[str, Any] | None = None
    generation: GenerationResult | None = None
    error: str | None = None

    @property
    def cost_usd(self) -> float:
        if self.generation and self.generation.cost_usd:
            return self.generation.cost_usd
        return 0.0


@dataclass
class ReaderResult:
    reader_slug: str
    date_iso: str
    html_path: Path | None = None
    txt_path: Path | None = None
    runs: list[GeneratorRun] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: str | None = None
    txt_error: str | None = None
    # Carried to the email teaser (the email links to the web issue, not the HTML).
    editor_headline: str | None = None
    editor_headline_note: str | None = None
    editor_teaser_line: str | None = None
    reader_summary: str | None = None

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.runs)

    def summary(self) -> str:
        if self.error:
            return f"reader={self.reader_slug} FAILED: {self.error}"
        ok = sum(1 for r in self.runs if r.error is None)
        return (
            f"reader={self.reader_slug} sections={ok}/{len(self.runs)} "
            f"cost=${self.total_cost_usd:.4f} {self.elapsed_seconds:.1f}s "
            f"→ {self.html_path}"
        )


def run_for_date(
    date_iso: str,
    readers: list[ReaderProfile],
    *,
    season: int | None = None,
    issue_number: str = "01",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    api_client: APIFootballClient | None = None,
    content_client: ContentClient | None = None,
) -> list[ReaderResult]:
    """Run the daily pipeline for `date_iso` across all `readers`.

    `season` defaults to the year of `date_iso` (API-Football's WC season
    convention is the start-year of the tournament).

    Per-reader failures are captured in the result; the run continues. The
    caller decides whether to halt on first failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if season is None:
        season = int(date_iso[:4])

    api = api_client or APIFootballClient()
    content = content_client or ContentClient()
    patch = load_patch(date_iso)

    # Fetch the day's fixtures once, then per-fixture supporting data on demand.
    day_fixtures_raw = api.fixtures(
        league=WC_LEAGUE_ID, season=season, date=date_iso
    )
    fixtures = day_fixtures_raw.get("response", [])
    fixtures_by_team = _index_fixtures_by_team(fixtures)

    # The previous day's fixtures feed the EDITOR's recap (`yesterday_matches`).
    # Empty on opening day; finished matches only are surfaced as results.
    prev_fixtures = api.fixtures(
        league=WC_LEAGUE_ID, season=season, date=_prev_date(date_iso)
    ).get("response", [])

    results: list[ReaderResult] = []
    for reader in readers:
        result = _run_for_reader(
            reader=reader,
            date_iso=date_iso,
            issue_number=issue_number,
            fixtures=fixtures,
            fixtures_by_team=fixtures_by_team,
            prev_fixtures=prev_fixtures,
            patch=patch,
            api=api,
            content=content,
            output_dir=output_dir,
        )
        results.append(result)

    if api_client is None:
        api.close()
    return results


def _run_for_reader(
    reader: ReaderProfile,
    date_iso: str,
    issue_number: str,
    fixtures: list[dict[str, Any]],
    fixtures_by_team: dict[str, dict[str, Any]],
    patch: dict[str, Any],
    api: APIFootballClient,
    content: ContentClient,
    output_dir: Path,
    prev_fixtures: list[dict[str, Any]] | None = None,
) -> ReaderResult:
    result = ReaderResult(reader_slug=reader.slug, date_iso=date_iso)
    t0 = time.monotonic()

    try:
        # 1) Reader's matches for the day, by team. A reader may follow multiple
        # teams playing on the same day; both get TEAM SHEET sections.
        reader_matches: list[tuple[str, Match]] = []
        for team_name in reader.teams:
            fx = fixtures_by_team.get(team_name.lower())
            if fx is None:
                continue
            match = _build_match_from_api(api, fx, patch)
            reader_matches.append((team_name, match))

        team_sheets: list[Any] = []
        for team_name, match in reader_matches:
            run = _run_generator(
                "TEAM SHEET",
                lambda: generate_team_sheet(match, reader, team_name=team_name, client=content),
            )
            result.runs.append(run)
            if run.facts is not None:
                team_sheets.append(build_team_sheet_section(run.facts, match, team_name))

        # 2) Universal sections — EDITOR uses the day context (universal across readers
        # but lens-shaped per reader). Build the day_context once.
        day_context = _build_day_context(date_iso, fixtures, patch, prev_fixtures)
        editor_facts = None
        editor_run = _run_generator(
            "EDITOR",
            lambda: generate_editor(day_context, reader, client=content),
        )
        result.runs.append(editor_run)
        editor_facts = editor_run.facts
        if editor_facts:
            result.editor_headline = editor_facts.get("headline")
            result.editor_headline_note = editor_facts.get("headline_note")
            paragraphs = editor_facts.get("paragraphs") or []
            if paragraphs:
                result.editor_teaser_line = _teaser_snippet(paragraphs[0])
        result.reader_summary = _reader_summary(reader)

        # 3) Editorial-seeded sections. If the patch doesn't supply a seed for a
        # section, we omit it cleanly — no hallucinated heritage.
        here_there_seed = editorial_seed(patch, "here_there_thread")
        here_there_facts = None
        if here_there_seed:
            run = _run_generator(
                "HERE & THERE",
                lambda: generate_here_and_there(here_there_seed, reader, client=content),
            )
            result.runs.append(run)
            here_there_facts = run.facts

        sbn_seed = editorial_seed(patch, "story_behind_number")
        sbn_facts = None
        if sbn_seed:
            run = _run_generator(
                "STORY BEHIND THE NUMBER",
                lambda: generate_story_behind_number(sbn_seed, reader, client=content),
            )
            result.runs.append(run)
            sbn_facts = run.facts

        bs_seed = editorial_seed(patch, "back_story")
        back_story_facts = None
        if bs_seed:
            run = _run_generator(
                "BACK STORY",
                lambda: generate_back_story(bs_seed, reader, client=content),
            )
            result.runs.append(run)
            back_story_facts = run.facts
            # Carry the editorial video (a YouTube id for the historical clip the
            # Back Story is about) straight from the patch to the template — never
            # through the LLM, which would invent the id. Renders as a grunge
            # "roll the tape" embed on the web issue.
            if back_story_facts is not None and isinstance(bs_seed, dict) and bs_seed.get("video"):
                back_story_facts["video"] = bs_seed["video"]

        venue_seed = editorial_seed(patch, "where_played_before")
        venue_facts = None
        if venue_seed:
            run = _run_generator(
                "WHERE THEY PLAYED BEFORE",
                lambda: generate_where_played_before(venue_seed, reader, client=content),
            )
            result.runs.append(run)
            venue_facts = run.facts

        stands_seed = editorial_seed(patch, "from_the_stands")
        stands_facts = None
        if stands_seed:
            run = _run_generator(
                "FROM THE STANDS",
                lambda: generate_from_the_stands(stands_seed, reader, client=content),
            )
            result.runs.append(run)
            stands_facts = run.facts

        anomalies_seed = editorial_seed(patch, "anomalies")
        added_facts = None
        if anomalies_seed:
            run = _run_generator(
                "ADDED TIME",
                lambda: generate_added_time(anomalies_seed, reader, client=content),
            )
            result.runs.append(run)
            added_facts = run.facts

        # 4) Render
        issue = {
            "number_str": issue_number,
            "date_human": _human_date(date_iso),
            "date_compact": _compact_date(date_iso),
            "day_short": _day_short(date_iso),
            "matchday_label": day_context.get("today_label", ""),
            "page_count": sum(
                1 for x in (
                    editor_facts, here_there_facts, sbn_facts, back_story_facts,
                    venue_facts, stands_facts, added_facts,
                ) if x is not None
            ) + len(team_sheets),
            "ticker_notes": [t.upper() for t in reader.teams[:3]],
            "tomorrow": None,
        }

        render_kwargs = dict(
            reader=reader_to_template_dict(reader),
            issue=issue,
            team_sheets=team_sheets,
            editor=editor_facts,
            here_there=here_there_facts,
            story_behind_number=sbn_facts,
            back_story=back_story_facts,
            where_played_before=venue_facts,
            from_the_stands=stands_facts,
            added_time=added_facts,
        )

        html = render_inference(**render_kwargs)
        out_path = output_dir / f"{date_iso}__{reader.slug}.html"
        out_path.write_text(html)
        result.html_path = out_path

        # Plain-text fallback for the email pipeline. Non-fatal: the HTML is the
        # primary artifact, so a txt-render failure must not sink the whole issue.
        try:
            txt = render_inference_txt(**render_kwargs)
            txt_path = output_dir / f"{date_iso}__{reader.slug}.txt"
            txt_path.write_text(txt)
            result.txt_path = txt_path
        except Exception as exc:
            result.txt_error = f"{type(exc).__name__}: {exc}"

    except Exception as exc:
        result.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"

    result.elapsed_seconds = time.monotonic() - t0
    return result


def _run_generator(label: str, fn: Callable[[], Any]) -> GeneratorRun:
    """Wrap one generator call. Captures errors so other sections can still run."""
    try:
        out = fn()
        return GeneratorRun(label=label, facts=out.facts, generation=out.generation)
    except Exception as exc:
        return GeneratorRun(label=label, error=f"{type(exc).__name__}: {exc}")


def _index_fixtures_by_team(fixtures: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return a {team_name_lower: fixture_entry} map. A team can only play once per day."""
    out: dict[str, dict[str, Any]] = {}
    for fx in fixtures:
        teams = fx.get("teams") or {}
        for side_key in ("home", "away"):
            name = ((teams.get(side_key) or {}).get("name") or "").lower()
            if name:
                out[name] = fx
    return out


def _build_match_from_api(
    api: APIFootballClient,
    fixture_entry: dict[str, Any],
    patch: dict[str, Any],
) -> Match:
    """Fetch lineups/events/statistics for a fixture and assemble a typed Match.

    Applies patches before extraction so the typed Match sees the corrected data.
    """
    fixture_id = fixture_entry["fixture"]["id"]
    patched_entry = apply_fixture_overrides(fixture_entry, patch)

    lineups = api.fixture_lineups(fixture_id).get("response", [])
    events = api.fixture_events(fixture_id).get("response", [])
    statistics = api.fixture_team_statistics(fixture_id).get("response", [])
    statistics = apply_stat_overrides(statistics, fixture_id, patch)

    return extract_match(patched_entry, lineups, events, statistics)


# API-Football status.short values that mean the match is over and the
# scoreline is real. Anything else (NS, TBD, PST, 1H, HT, …) has no result yet.
_FINISHED_STATUSES = {"FT", "AET", "PEN", "WO", "AWD"}


def _fixture_status(fx: dict[str, Any]) -> str:
    return ((fx.get("fixture") or {}).get("status") or {}).get("short") or "NS"


def _build_day_context(
    date_iso: str,
    fixtures: list[dict[str, Any]],
    patch: dict[str, Any],
    prev_fixtures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Universal day-context payload for the EDITOR generator.

    Fixtures are bucketed by *match status*, not by date: finished matches
    (with a real scoreline) become `yesterday_matches` — the recap — while
    not-yet-played matches become `today_matches` — previews carrying NO score.
    `prev_fixtures` (the previous calendar day) feeds the recap so a
    mid-tournament morning has yesterday's results to reflect on; on opening day
    it is empty. The patch can override any field (`today_label`,
    `tournament_summary`, `context_notes`).
    """
    overrides = day_context_overrides(patch)

    yesterday_matches: list[dict[str, Any]] = []
    today_matches: list[dict[str, Any]] = []
    for fx in [*(prev_fixtures or []), *fixtures]:
        teams = fx.get("teams") or {}
        league = fx.get("league") or {}
        venue = (fx.get("fixture") or {}).get("venue") or {}
        home = (teams.get("home") or {}).get("name")
        away = (teams.get("away") or {}).get("name")
        if _fixture_status(fx) in _FINISHED_STATUSES:
            goals = fx.get("goals") or {}
            yesterday_matches.append({
                "home": home,
                "away": away,
                "score_regulation": f"{goals.get('home')}-{goals.get('away')}",
                "result_tag": None,
                "round": league.get("round"),
                "venue": venue.get("name"),
                "key_moments": [],
            })
        else:
            today_matches.append({
                "home": home,
                "away": away,
                "round": league.get("round"),
                "venue": venue.get("name"),
                "kickoff_status": "upcoming — not yet played",
            })

    base = {
        "tournament": "FIFA World Cup 2026",
        "today_label": f"Matchday {date_iso}",
        "today_date_iso": date_iso,
        "yesterday_matches": yesterday_matches,
        "today_matches": today_matches,
        "tournament_summary": "",
        "context_notes": [],
    }
    base.update(overrides)
    return base


def _human_date(date_iso: str) -> str:
    """e.g. '2026-06-11' → 'Thursday 11 June 2026'."""
    from datetime import date

    y, m, d = (int(p) for p in date_iso.split("-"))
    dt = date(y, m, d)
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return f"{days[dt.weekday()]} {dt.day} {months[dt.month - 1]} {dt.year}"


def _teaser_snippet(text: str, limit: int = 200) -> str:
    """First ~`limit` chars of the editor's opening paragraph for the email
    teaser — trimmed at a word boundary, with an ellipsis if cut."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
    return f"{cut}…"


def _reader_summary(reader: ReaderProfile) -> str | None:
    """e.g. 'Mexico · The Diaspora lens' for the teaser footer line."""
    parts: list[str] = []
    if reader.teams:
        parts.append(", ".join(reader.teams))
    if reader.lens:
        parts.append(f"{reader.lens} lens")
    return " · ".join(parts) or None


def _prev_date(date_iso: str) -> str:
    """e.g. '2026-06-11' → '2026-06-10'."""
    from datetime import date, timedelta

    y, m, d = (int(p) for p in date_iso.split("-"))
    return (date(y, m, d) - timedelta(days=1)).isoformat()


def _compact_date(date_iso: str) -> str:
    """e.g. '2026-06-11' → '11.06.26'."""
    y, m, d = date_iso.split("-")
    return f"{d}.{m}.{y[-2:]}"


def _day_short(date_iso: str) -> str:
    from datetime import date

    y, m, d = (int(p) for p in date_iso.split("-"))
    dt = date(y, m, d)
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
