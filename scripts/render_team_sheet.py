"""Render one TEAM SHEET end-to-end for a fake reader against cached spike data.

Pulls the cached ARG-FRA 2022 final from output/cache/api-football/, extracts
a typed Match, and generates a TEAM SHEET for "Marcus" (Cultural Critic) on
Argentina. Saves the structured output JSON and prints a summary.

Usage:
    .venv/bin/python scripts/render_team_sheet.py
    .venv/bin/python scripts/render_team_sheet.py --team France --lens Pub-Talker
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from dotenv import load_dotenv

from inference.content.generators.team_sheet import generate_team_sheet
from inference.data.extract import extract_match
from inference.data.models import ReaderProfile

load_dotenv()

CACHE = Path("output/cache/api-football")
OUT_DIR = Path("output/team_sheets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIXTURE_ID = 979139  # ARG–FRA 2022 final, per data spike


def _load_cached_match(fixture_id: int):
    fixtures_raw = json.loads(
        (CACHE / "fixtures__date=2022-12-18_league=1_season=2022.json").read_text()
    )
    fixture_entry = fixtures_raw["response"][0]
    assert fixture_entry["fixture"]["id"] == fixture_id

    lineups = json.loads(
        (CACHE / f"fixtures_lineups__fixture={fixture_id}.json").read_text()
    )["response"]
    events = json.loads(
        (CACHE / f"fixtures_events__fixture={fixture_id}.json").read_text()
    )["response"]
    statistics = json.loads(
        (CACHE / f"fixtures_statistics__fixture={fixture_id}.json").read_text()
    )["response"]

    return extract_match(fixture_entry, lineups, events, statistics)


@click.command()
@click.option("--team", default="Argentina", help="Which side to write TEAM SHEET for")
@click.option(
    "--lens",
    default="Cultural Critic",
    type=click.Choice(
        [
            "Cultural Critic", "Pub-Talker", "Tactician", "Romantic", "Historian",
            "The Diaspora", "The Beat Reporter",
        ]
    ),
)
@click.option(
    "--length",
    default="Standard",
    type=click.Choice(["Sprint", "Standard", "Long-read"]),
)
def main(team: str, lens: str, length: str):
    click.echo(f"Loading cached ARG–FRA 2022 final (fixture {FIXTURE_ID})…")
    match = _load_cached_match(FIXTURE_ID)
    click.echo(
        f"  {match.home.name} {match.home.score_regulation}–"
        f"{match.away.score_regulation} {match.away.name} "
        f"({match.status_short})"
    )
    if match.penalty_home is not None:
        click.echo(
            f"  PEN: {match.home.name} {match.penalty_home}–"
            f"{match.penalty_away} {match.away.name}"
        )

    reader = ReaderProfile(
        slug="marcus",
        display_name="Marcus",
        teams=["Argentina", "France", "Morocco"],
        players=["Lionel Messi", "Kylian Mbappé", "Achraf Hakimi"],
        lens=lens,  # type: ignore[arg-type]
        length=length,  # type: ignore[arg-type]
        wildcard=(
            "I'm a chef. Food metaphors and kitchen-language when they actually "
            "fit — don't force it."
        ),
    )

    click.echo(
        f"\nGenerating TEAM SHEET — team={team} lens={lens} length={length}…"
    )
    out = generate_team_sheet(match, reader, team_name=team)
    click.echo(f"  {out.generation}")

    facts = out.facts

    # Save raw first — if display logic crashes, the work isn't lost.
    out_path = OUT_DIR / f"{reader.slug}__{team.lower()}__{lens.lower().replace(' ', '-')}.json"
    out_path.write_text(json.dumps(facts, indent=2, ensure_ascii=False))

    click.echo(f"\n=== {facts.get('team')} ===")
    click.echo(f"  result_line: {facts.get('result_line')}")
    sp = facts.get("score_poster", {})
    click.echo(
        f"  score: {sp.get('home')} {sp.get('home_score')}–"
        f"{sp.get('away_score')} {sp.get('away')}  "
        f"{sp.get('result_tag') or ''}"
    )
    mm = facts.get("match_meta", {})
    click.echo(
        f"  meta: {mm.get('formation')} · {mm.get('date_human')} · "
        f"{mm.get('venue')} · {mm.get('round')}"
    )
    click.echo("\n  stat posters:")
    for sp in facts.get("stat_posters") or []:
        click.echo(
            f"    [{sp.get('big_num'):>6}] {sp.get('label'):<24} — {sp.get('note')}"
        )
    click.echo("\n  recap:")
    for para in facts.get("recap_paragraphs") or []:
        click.echo("    " + para)
        click.echo("")
    pq = facts.get("pull_quote")
    if pq:
        if isinstance(pq, dict):
            click.echo(f"  pull_quote: \"{pq.get('text')}\" — {pq.get('attribution') or '?'}")
        else:
            click.echo(f"  pull_quote (str): \"{pq}\"")

    click.echo(f"\n  → {out_path}")


if __name__ == "__main__":
    main()
