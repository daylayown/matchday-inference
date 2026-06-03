"""Render one full Inference HTML end-to-end for a fake reader.

Wires all 8 generators against the cached ARG–FRA 2022 final:
TEAM SHEET, EDITOR, HERE & THERE, STORY BEHIND THE NUMBER, BACK STORY,
WHERE THEY PLAYED BEFORE, FROM THE STANDS, ADDED TIME.

Usage:
    .venv/bin/python scripts/render_inference.py
    .venv/bin/python scripts/render_inference.py --team France --lens Pub-Talker
    .venv/bin/python scripts/render_inference.py --no-llm   # use last-saved facts
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from dotenv import load_dotenv

from inference.content.generators.added_time import generate_added_time
from inference.content.generators.back_story import generate_back_story
from inference.content.generators.editor import generate_editor
from inference.content.generators.from_the_stands import generate_from_the_stands
from inference.content.generators.here_and_there import generate_here_and_there
from inference.content.generators.story_behind_number import generate_story_behind_number
from inference.content.generators.team_sheet import generate_team_sheet
from inference.content.generators.where_played_before import generate_where_played_before
from inference.data.extract import extract_match
from inference.data.models import ReaderProfile
from inference.delivery.render import (
    build_team_sheet_section,
    reader_to_template_dict,
    render_inference,
)

load_dotenv()

CACHE = Path("output/cache/api-football")
TEAM_SHEET_CACHE = Path("output/team_sheets")
EDITOR_CACHE = Path("output/editor")
HERETHERE_CACHE = Path("output/here_and_there")
SBN_CACHE = Path("output/story_behind_number")
BACKSTORY_CACHE = Path("output/back_story")
VENUE_CACHE = Path("output/where_played_before")
STANDS_CACHE = Path("output/from_the_stands")
ADDED_CACHE = Path("output/added_time")
OUT_DIR = Path("output/inferences")
OUT_DIR.mkdir(parents=True, exist_ok=True)


DAY_CONTEXT_2022_FINAL = {
    "tournament": "FIFA World Cup 2022",
    "today_label": "The morning after the Final",
    "today_date_iso": "2022-12-19",
    "yesterday_matches": [
        {
            "home": "Argentina",
            "away": "France",
            "score_regulation": "3-3",
            "result_tag": "Argentina won 4-2 on penalties (AET)",
            "round": "Final",
            "venue": "Lusail Iconic Stadium",
            "key_moments": [
                "Messi opened the scoring from the penalty spot at 23'",
                "Di María made it 2-0 at 36'",
                "Mbappé scored twice in two minutes (80', 81') to force ET",
                "Messi restored Argentina's lead at 108'",
                "Mbappé equalised from the spot at 118' for 3-3",
                "Argentina converted all four penalties they took; France missed two",
            ],
        }
    ],
    "tournament_summary": (
        "The 2022 World Cup ends in Lusail with Argentina lifting their third trophy "
        "(1978, 1986, 2022). Messi finishes as the only player to score in every round of a "
        "single World Cup. Mbappé becomes the second man ever to score a hat-trick in a "
        "World Cup final (Geoff Hurst, 1966) and still loses."
    ),
    "context_notes": [
        "Argentina's first WC title since 1986 (Maradona).",
        "Messi played his 26th WC match — the most ever.",
        "Mbappé's 8 goals topped the Golden Boot.",
        "First WC final to go 3-3 in extra time since West Germany–Hungary 1954.",
        "Lusail Stadium, opened 2021, hosted the final in its inaugural tournament.",
    ],
}


HERETHERE_THREAD_2022_FINAL = {
    "topic": "Argentina vs France at the World Cup — four meetings, two epochs",
    "framing": (
        "Yesterday's final was the fourth time Argentina and France have met at a "
        "World Cup. The thread that ties the four reads almost as a generational "
        "transfer: the South Americans winning the first three until 2018, when "
        "Mbappé arrived and France took the result back."
    ),
    "facts": [
        {
            "label": "1930 — Montevideo, Group I",
            "fact": "Argentina 1–0 France in the inaugural World Cup. Luis Monti scored. The match ended early after the referee blew the whistle six minutes prematurely; the players were called back from the dressing rooms to finish.",
        },
        {
            "label": "1978 — Buenos Aires, Group A",
            "fact": "Argentina 2–1 France at El Monumental. The hosts went on to win their first World Cup; France went home in the group stage.",
        },
        {
            "label": "2018 — Kazan, Round of 16",
            "fact": "France 4–3 Argentina. Mbappé scored two and announced himself to the world at 19. Argentina, with Messi 30 and Sampaoli on the bench, went home; France won the tournament.",
        },
        {
            "label": "2022 — Lusail, The Final",
            "fact": "Argentina 3–3 France, 4–2 on penalties. Messi vs Mbappé in the contest most footballing imaginations had been waiting four years to see. Messi won the trophy he had been missing his whole career.",
        },
        {
            "label": "Goals across the four matches",
            "fact": "Argentina 6, France 8. The shootout doesn't count toward that ledger — by goals from open play, France lead the rivalry. By trophies lifted at the end of it, Argentina lead 2–1.",
        },
        {
            "label": "The two through-lines",
            "fact": "Messi played in three of the four (2010 onwards). Mbappé in the last two — and scored a hat-trick yesterday despite losing.",
        },
    ],
}


# STORY BEHIND THE NUMBER — Mbappé becomes the second hat-trick scorer in a WC final, and lost.
SBN_INPUT_2022_FINAL = {
    "number": "1966",
    "surface_stat": "Mbappé · hat-trick in a World Cup final · lost",
    "historical_anchor": (
        "The last time someone scored three in a World Cup final was Geoff Hurst at Wembley in 1966. "
        "Hurst's England won. Mbappé did not."
    ),
    "quick_facts": [
        {"k": "Mbappé", "v": "3 goals · 80', 81', 118' (pen.)"},
        {"k": "Hurst, 1966", "v": "3 goals · England 4–2 W. Germany (AET)"},
        {"k": "Result", "v": "Argentina won 4–2 on pens"},
    ],
    "supporting_context": [
        "Mbappé is 23. Hurst was 24 when he did it.",
        "It took 56 years and 11 World Cups for the feat to be repeated.",
        "Argentina led 2-0 with 10 minutes left. Mbappé scored twice in 97 seconds to force extra time, then once more in extra time.",
    ],
}


# BACK STORY — Argentina vs France, focus on 2018 R16
BACK_STORY_2022_FINAL = {
    "teams": ["Argentina", "France"],
    "focus_meeting": {
        "year": "2018",
        "score": "4 — 3",
        "host": "Russia",
        "round": "Round of 16",
        "venue": "Kazan Arena, Kazan",
        "context_line": "Russia · Round of 16 · Kazan Arena, Kazan",
        "goals": [
            {"scorer": "Di María", "minute": "41'", "note": "(stunner)"},
            {"scorer": "Mercado", "minute": "48'", "note": "(deflected)"},
            {"scorer": "Pavard", "minute": "57'", "note": "(volley of the tournament)"},
            {"scorer": "Mbappé", "minute": "64'", "note": None},
            {"scorer": "Mbappé", "minute": "68'", "note": None},
            {"scorer": "Agüero", "minute": "90+3'", "note": "(consolation)"},
        ],
        "narrative_beats": [
            "France 4–3 Argentina. Mbappé scored two and announced himself to the world at 19.",
            "Argentina led 2-1 at the hour mark; Mbappé's two-in-four turned the match.",
            "Sampaoli's last match in charge. Messi was 30 and looked tired by full-time.",
            "France went on to win the tournament.",
        ],
    },
    "ledger": (
        "Argentina–France at the World Cup, before yesterday: ARG 2 wins (1930, 1978), "
        "FRA 1 win (2018). Goals across the three meetings: ARG 4, FRA 5."
    ),
}


# WHERE THEY PLAYED BEFORE — Lusail Iconic Stadium (the venue of the final)
VENUE_2022_FINAL = {
    "venue": {
        "name": "Lusail Iconic Stadium",
        "city": "Lusail, Qatar",
        "capacity": 88_966,
        "opened": 2021,
        "world_cups": [2022],
    },
    "historical_matches": [
        {
            "year": "2022",
            "body": "Argentina 2 — 0 Saudi Arabia. Group C, MD1. The biggest upset of the group stage; Argentina lost their opening match of the tournament they would go on to win.",
        },
        {
            "year": "2022",
            "body": "Argentina 2 — 1 Mexico. Group C, MD2. Messi's goal in the 64th minute rescued Argentina's tournament after the Saudi Arabia loss.",
        },
        {
            "year": "2022",
            "body": "Argentina 3 — 0 Croatia. Semifinal. Messi assisted and scored; Álvarez ran half the pitch for the third. Argentina booked the final.",
        },
        {
            "year": "2022",
            "body": "Argentina 3 — 3 France, 4 — 2 on penalties. The Final. Messi vs Mbappé in the contest most footballing imaginations had been waiting four years to see. Argentina's third star.",
        },
    ],
    "closer_hint": (
        "Lusail hosted four of Argentina's seven 2022 matches, including their only loss "
        "and their three biggest wins."
    ),
}


# FROM THE STANDS — a plausible reader Q&A about the shootout
STANDS_QA_2022_FINAL = {
    "asker_name": "Mateo",
    "asker_city": "Rosario",
    "asker_day": "Sun 18 Dec",
    "question": (
        "Why did Deschamps take Giroud and Dembélé off at half-time? "
        "France looked dead until he made the changes."
    ),
    "factual_brief": {
        "facts": [
            "France started 4-2-3-1 with Giroud as the lone striker, Dembélé and Mbappé wide, Griezmann at 10.",
            "By half-time France had 1 shot (none on target) and Argentina led 2-0 — Messi pen 23', Di María 36'.",
            "Deschamps brought on Thuram and Kolo Muani at the break, taking off Dembélé and Giroud.",
            "France's pressing structure changed: Thuram and Muani pressed Argentina's centre-backs higher, restricting the build-up.",
            "France did not register a shot on target until the 71st minute, but the second-half balance shifted: Argentina had 3 shots, France 7.",
            "Mbappé scored twice in 97 seconds (80', 81') to force extra time. Both came from the new attacking pressure: a Kolo Muani drawn penalty, then a Mbappé volley off a Thuram lay-off.",
        ],
        "note": "The question implies the changes saved France. The brief shows they shifted the second-half xG balance, then created the two goals that forced extra time.",
    },
}


# ADDED TIME — anomalies from the final
ANOMALIES_2022_FINAL = [
    {
        "tag": "Mbappé hat-trick",
        "seed": "Mbappé scored a hat-trick in a World Cup final and his team lost. The last hat-trick in a final was Geoff Hurst's in 1966; Hurst's England won. 56 years between the two.",
    },
    {
        "tag": "Messi penalty kings",
        "seed": "Emiliano Martínez saved Coman's penalty in the shootout, then Tchouaméni put his over the bar. Argentina did not miss any of their four. Martínez is the second goalkeeper ever to win the Golden Glove of two tournaments.",
    },
    {
        "tag": "Di María",
        "seed": "Di María scored Argentina's second goal — his third in a major tournament final (Copa 2021, Finalissima 2022, World Cup 2022). He didn't start France-friendly matches for Argentina ever again.",
    },
    {
        "tag": "Lusail attendance",
        "seed": "Attendance at the final was 88,966. The stadium opened in 2021 and hosted the final in its inaugural tournament. The capacity matches the seat-count precisely — no over-sell.",
    },
    {
        "tag": "Marciniak",
        "seed": "Polish referee Szymon Marciniak handled the final. He gave Argentina a penalty in the 23rd minute and France a penalty in the 118th. Two penalties in a final happened previously in 2006.",
    },
    {
        "tag": "Messi minutes",
        "seed": "Messi played his 26th and final World Cup match — the most ever. He passed Lothar Matthäus's 25. He has now played 2,314 World Cup minutes; no one else has crossed 2,200.",
    },
]


FIXTURE_ID = 979139  # ARG–FRA 2022 final


def _load_cached_match(fixture_id: int):
    fixtures_raw = json.loads(
        (CACHE / "fixtures__date=2022-12-18_league=1_season=2022.json").read_text()
    )
    fixture_entry = fixtures_raw["response"][0]
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


def _cached_or_generate(cache_dir: Path, cache_key: str, no_llm: bool, label: str, gen_fn):
    """Shared cache/generate flow. `gen_fn` returns an object with .facts and .generation."""
    path = cache_dir / f"{cache_key}.json"
    if no_llm and path.exists():
        click.echo(f"Using cached {label} facts: {path}")
        return json.loads(path.read_text())
    click.echo(f"Generating {label}…")
    out = gen_fn()
    click.echo(f"  {out.generation}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out.facts, indent=2, ensure_ascii=False))
    return out.facts


@click.command()
@click.option("--team", default="Argentina")
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
@click.option(
    "--no-llm",
    is_flag=True,
    help="Skip the LLM call; use the last saved facts from disk.",
)
def main(team: str, lens: str, length: str, no_llm: bool):
    match = _load_cached_match(FIXTURE_ID)

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
        location="Brooklyn, NY",
    )

    cache_key = f"{reader.slug}__{team.lower()}__{lens.lower().replace(' ', '-')}"

    # TEAM SHEET
    team_sheet_facts = _cached_or_generate(
        TEAM_SHEET_CACHE, cache_key, no_llm, "TEAM SHEET",
        lambda: generate_team_sheet(match, reader, team_name=team),
    )
    team_sheets = [build_team_sheet_section(team_sheet_facts, match, team)]

    editor_facts = _cached_or_generate(
        EDITOR_CACHE, cache_key, no_llm, "EDITOR",
        lambda: generate_editor(DAY_CONTEXT_2022_FINAL, reader),
    )

    here_there_facts = _cached_or_generate(
        HERETHERE_CACHE, cache_key, no_llm, "HERE & THERE",
        lambda: generate_here_and_there(HERETHERE_THREAD_2022_FINAL, reader),
    )

    sbn_facts = _cached_or_generate(
        SBN_CACHE, cache_key, no_llm, "STORY BEHIND THE NUMBER",
        lambda: generate_story_behind_number(SBN_INPUT_2022_FINAL, reader),
    )

    back_story_facts = _cached_or_generate(
        BACKSTORY_CACHE, cache_key, no_llm, "BACK STORY",
        lambda: generate_back_story(BACK_STORY_2022_FINAL, reader),
    )

    venue_facts = _cached_or_generate(
        VENUE_CACHE, cache_key, no_llm, "WHERE THEY PLAYED BEFORE",
        lambda: generate_where_played_before(VENUE_2022_FINAL, reader),
    )

    stands_facts = _cached_or_generate(
        STANDS_CACHE, cache_key, no_llm, "FROM THE STANDS",
        lambda: generate_from_the_stands(STANDS_QA_2022_FINAL, reader),
    )

    added_facts = _cached_or_generate(
        ADDED_CACHE, cache_key, no_llm, "ADDED TIME",
        lambda: generate_added_time(ANOMALIES_2022_FINAL, reader),
    )

    issue = {
        "number_str": "04",
        "date_human": "Sunday 18 December 2022",
        "date_compact": "18.12.22",
        "day_short": "Sun",
        "matchday_label": "The Final",
        "page_count": 9,
        "ticker_notes": [
            f"{team.upper()} {team_sheet_facts.get('score_poster', {}).get('home_score', '?')}–{team_sheet_facts.get('score_poster', {}).get('away_score', '?')}",
            "FINAL WHISTLE LUSAIL",
            "MESSI LIFTS THE CUP",
        ],
        "tomorrow": None,
    }

    html = render_inference(
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

    out_path = OUT_DIR / f"{reader.slug}__{team.lower()}__{lens.lower().replace(' ', '-')}.html"
    out_path.write_text(html)
    click.echo(f"\n  → {out_path}")
    click.echo(f"  → open file://{out_path.absolute()}")


if __name__ == "__main__":
    main()
