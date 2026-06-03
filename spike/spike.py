"""
THE INFERENCE — spike runner.

Generates one mock Issue per reader profile by:
  1. Loading reader profile + hand-crafted match-day JSON
  2. Calling OpenAI for each of 3 generators (editor, match_brief, here_and_there)
  3. Rendering the JSON outputs into a Jinja template
  4. Writing HTML to spike/output/{reader_slug}.html

No real data clients. No email. No backend. Just: does the AI hold the voice?
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

HERE = Path(__file__).parent
ROOT = HERE.parent

load_dotenv(dotenv_path=ROOT / ".env")

PROMPTS = HERE / "prompts"
DATA = HERE / "data"
TEMPLATES = HERE / "templates"
OUTPUT = HERE / "output"
OUTPUT.mkdir(exist_ok=True)

MODEL = os.environ.get("INFERENCE_MODEL", "gpt-5.5")

# Approximate gpt-5.5 pricing per 1M tokens (May 2026, placeholder — verify against
# the OpenAI pricing page; not yet recorded in model-price-research.md).
COST_PER_M_IN = 2.50
COST_PER_M_OUT = 15.00

client = OpenAI()

# ────────────────────────────────────────────────────────────────────
# Hand-curated thread for Here & There. In production this would come
# from a context-extraction step that pulled relevant heritage facts
# given the reader's teams + the day's fixtures. Hand-written here so
# the generator has real facts to organize (and no excuse to invent).
# ────────────────────────────────────────────────────────────────────
THREAD = {
    "topic": "Achraf Hakimi — the thread between Morocco, France, and Spain",
    "framing": (
        "Tomorrow's semifinal pits France against Morocco. Hakimi is the through-line: "
        "a Madrid-born son of Moroccan immigrants who chose Morocco over Spain, and who "
        "shares a PSG dressing room with Mbappé. The match is a family disagreement at scale."
    ),
    "facts": [
        {"label": "Born", "fact": "Madrid, Spain · November 1998. To Moroccan immigrant parents from Ksar el-Kebir and Tetouán."},
        {"label": "Grew up", "fact": "Getafe — a working-class Madrid suburb. Spanish-born, Spanish-raised, in the Spanish school system."},
        {"label": "Real Madrid", "fact": "Came through the Real Madrid youth ranks. Debuted under Zidane in 2017."},
        {"label": "Wandered", "fact": "Loaned to Dortmund, sold to Inter Milan, then bought by PSG in 2021."},
        {"label": "PSG today", "fact": "Mbappé's club teammate since 2021. They share a Paris dressing room. They face each other tomorrow."},
        {"label": "International choice", "fact": "Eligible for both Spain and Morocco. Chose Morocco. Captains them now."},
        {"label": "This tournament", "fact": "Scored the decisive penalty against Spain in the round-of-16 to put Morocco through. Then this — Africa's first World Cup semifinal."},
    ],
}


def load_prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()


def call_generator(generator_name: str, reader_profile: dict, payload: dict) -> tuple[dict, object]:
    """Run one generator. Returns (parsed_json, usage_object)."""
    system = load_prompt(generator_name)
    user_msg = json.dumps(
        {"reader_profile": reader_profile, **payload},
        indent=2,
        ensure_ascii=False,
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  !! JSON decode failed for {generator_name}: {e}")
        print(f"     Raw content: {content[:500]}")
        raise
    return parsed, response.usage


def render_issue(reader_profile: dict, sections: dict, match_day: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    template = env.get_template("inference.html.j2")
    return template.render(reader=reader_profile, sections=sections, match_day=match_day)


def main():
    match_day = json.loads((DATA / "match_day.json").read_text())
    readers = [
        json.loads((DATA / "reader_marcus.json").read_text()),
        json.loads((DATA / "reader_lin.json").read_text()),
    ]

    focus_match = next(m for m in match_day["yesterday_matches"] if m["home"] == "Morocco")

    totals = {"in": 0, "out": 0}
    t0 = time.time()

    for reader in readers:
        print(f"\n=== {reader['display_name']} · {reader['lens']} ===")
        sections = {}

        for gen_name, payload in [
            ("editor", {"day_context": match_day}),
            ("match_brief", {"match": focus_match}),
            ("here_and_there", {
                "thread_topic": THREAD["topic"],
                "thread_framing": THREAD["framing"],
                "thread_facts": THREAD["facts"],
            }),
        ]:
            print(f"  · {gen_name} ...", end=" ", flush=True)
            t_gen = time.time()
            try:
                parsed, usage = call_generator(gen_name, reader, payload)
            except Exception as e:
                print(f"FAIL ({type(e).__name__}: {e})")
                raise
            sections[gen_name] = parsed
            totals["in"] += usage.prompt_tokens
            totals["out"] += usage.completion_tokens
            print(f"ok · {usage.prompt_tokens}→{usage.completion_tokens} tok · {time.time()-t_gen:.1f}s")

        out_path = OUTPUT / f"{reader['slug']}.html"
        out_path.write_text(render_issue(reader, sections, match_day))
        # Also dump the raw JSON for inspection
        (OUTPUT / f"{reader['slug']}.json").write_text(json.dumps(sections, indent=2, ensure_ascii=False))
        print(f"  → {out_path.relative_to(ROOT)}")

    cost = (totals["in"] / 1e6) * COST_PER_M_IN + (totals["out"] / 1e6) * COST_PER_M_OUT
    print(f"\nElapsed: {time.time()-t0:.1f}s")
    print(f"Tokens : in={totals['in']:,}  out={totals['out']:,}")
    print(f"Cost   : ~${cost:.4f} (at {MODEL} indicative pricing)")


if __name__ == "__main__":
    main()
