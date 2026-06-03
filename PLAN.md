# THE INFERENCE — Engineering Plan

**Drafted:** 2026-05-15.
**Supersedes:** `PROMPT.md` (original brief; some assumptions revised — see "What changed" below).

---

## State of play

What's locked:

- **Brand & nomenclature.** THE INFERENCE masthead, matchday-football terminology (TEAM SHEET / STATS PAGE / CENTRE SPREAD / MANAGER'S NOTES / FROM THE STANDS / ADDED TIME / WALKOUT / FULL-TIME / THE TOUCHLINE / THE GANTRY / THE MIXED ZONE). See [`nomenclature.md`](nomenclature.md).
- **Visual identity.** Grunge / DIY fanzine. Canonical reference: [`web/inference-sample-v3.html`](web/inference-sample-v3.html). Full spec: [`design.md`](design.md).
- **Product framing.** Personalised daily matchday zine, ~80% prose/visual, ~20% numbers. Vibes-based not stats-heavy. Built around heritage features (Here & There, Back Story, Where They Played Before) plus a tournament-arc editor's column.
- **Data approach.** **API-Football Pro is the sole planned live provider** (~$25 for the tournament window). A local JSON **patch layer** (`data/patches/YYYY-MM-DD.json`) handles corrections, missing context, and editorial overrides — cheaper and safer than normalizing a second provider. **Sportmonks / Statorium are contingency-only**, evaluated after the Phase 0 data spike if API-Football fails on an essential field. xG is optional color, not infrastructure. No event-level x/y data; pass-network renderer is a **post-tournament archive feature**, not live. Full rationale: [`api-research.md`](api-research.md). Background on the Jan 2026 data-landscape shift: [memory: WC 2026 data landscape](.claude/projects/-home-nicholas-claude-code-projects-world-cup-project/memory/wc2026-data-landscape.md).
- **AI model strategy.** Quality-first, **OpenAI sole provider** via the **Responses API**: **`gpt-5.5`** is the default for every reader-facing prose generator. **`gpt-5.4-nano`** for utility transforms (extraction, classification, normalization). **`gpt-5.4-mini`** is held in reserve as an optional mid-tier fallback if generation volume grows; no cheap/premium routing in v1. One SDK, one key, one billing surface. Rationale: see [`llm-model-analysis.md`](llm-model-analysis.md). At 10–50 readers the binding constraint is editorial voice, not token cost.
- **Frontend.** Landing page + sample issue exist as standalone HTML/CSS/JS in `web/`. Multi-step signup form works against `localStorage` (no backend yet).

What's not locked but assumed for this plan:

- **Python** for backend (per original brief, consistent with sibling `deep-dugout` patterns).
- **SQLite** for storage (5-week one-off; no need for Postgres).
- **Resend** for email delivery (developer-first, clean API, generous free tier).
- **GitHub Actions cron** for scheduling (simpler than Cloudflare Workers for this scope).

These can be revisited but the plan proceeds on them.

## What changed vs PROMPT.md

PROMPT.md was an excellent starting brief. Several assumptions in it have been revised by what we've learned:

| PROMPT.md | Current plan |
|---|---|
| Stats-only, no takes, no narrative | Vibes-based with heritage features. Stats compressed to single page. |
| FBref + soccerdata for free advanced stats | FBref pulled advanced stats Jan 2026 after FIFA × Stats Perform exclusivity. API-Football is now the sole live provider; a local patch layer covers gaps. Sportmonks is contingency-only. See `api-research.md`. |
| Default Claude (Sonnet, Haiku) | Quality-first single-provider OpenAI: `gpt-5.5` (Responses API) for all creative prose; `gpt-5.4-nano` for utility transforms. |
| Email-rendering: HTML hand-roll or MJML | Same plan; web sample (`inference-sample-v3.html`) is the source-of-truth design. |
| AI: ratings ladder + anomalies, that's it | AI does much more — per-reader narrative recap, editor's column, Here & There, Back Story, Where They Played Before, Mixed Zone replies. |

---

## The shape of what we're building

Roughly:

```
SCHEDULER (GH Actions cron, daily ~02:00 ET)
    │
    ▼
DATA FETCH ──────────────►  cache (SQLite)
  · API-Football Pro          · fixtures, lineups, events, stats, standings
  · data/patches/*.json       · manual corrections + editorial overrides
  · OpenFootball (static)     · schedule scaffold
    │
    ▼
EXTRACT / NORMALIZE
  · raw API → DayContext
  · DayContext: yesterday's matches, leaders, standings
    │
    ▼
GENERATION (per-content-type — all gpt-5.5 via Responses API)
  · TEAM SHEET (per reader)              ← gpt-5.5
  · EDITOR'S COLUMN (universal)          ← gpt-5.5
  · STORY BEHIND THE NUMBER (universal)  ← gpt-5.5
  · HERE & THERE (per reader's matches)  ← gpt-5.5
  · BACK STORY (per reader's matches)    ← gpt-5.5
  · WHERE THEY PLAYED BEFORE (per match) ← gpt-5.5
  · ADDED TIME (universal)               ← gpt-5.5
  · FROM THE STANDS (curated daily)      ← gpt-5.5
  · (utility transforms: extract / classify / normalize) ← gpt-5.4-nano
    │
    ▼
COMPOSE (per reader)
  · merge universal + personalised pieces
  · render HTML email + plain-text fallback
    │
    ▼
DELIVER
  · Resend API (per-reader send)
  · log delivery + errors
```

A 5-week one-off, ~10–50 readers initially. Scope stays small; the architecture is honest about that.

---

## Tech stack (locked)

| Layer | Choice | Why |
|---|---|---|
| Language | **Python 3.13+** (venv currently 3.14) | Per original brief, sibling-project consistency |
| HTTP client | **httpx** | Async-capable, clean API for the two REST clients |
| Data models | **pydantic v2** | Validated typed models for everything that crosses a boundary |
| LLM SDK | **openai** (Responses API) | One provider: `gpt-5.5` for all creative prose, `gpt-5.4-nano` for utility transforms |
| Email templating | **Jinja2** | Source-of-truth template lives in `web/`; Jinja renders per-reader variants |
| Email delivery | **Resend** | Clean Python SDK, free tier covers our scale |
| DB | **SQLite** via stdlib `sqlite3` | One file, zero ops |
| Scheduling | **GitHub Actions cron** | One workflow file, runs on Anthropic's dime |
| Config | **python-dotenv** + env vars | No secrets in code |
| CLI | **click** | For one-off scripts and manual triggers |
| Tests | **pytest** | Just enough to keep generation deterministic where we want it |

---

## Project structure

```
world-cup-project/
├── PLAN.md                       # this file
├── PROMPT.md                     # original brief (historical)
├── design.md                     # visual identity spec
├── nomenclature.md               # naming spec
├── llm-model-analysis.md         # current model strategy (gpt-5.5 default)
├── model-price-research.md       # AI pricing notes (superseded for model selection)
├── pyproject.toml                # Python project + deps
├── .env.example                  # template for required env vars
├── .gitignore
│
├── spike/                        # voice/prompt prototype — built, validated on gpt-5.5
│   ├── spike.py                  # Chat Completions prototype (do not pattern src/inference on this)
│   ├── prompts/                  # editor.md, match_brief.md, here_and_there.md
│   ├── data/                     # hand-crafted match_day + reader profiles (Marcus, Lin)
│   ├── templates/                # inference.html.j2
│   └── output/                   # rendered HTML + JSON; archive-gpt-5-nano/ holds the flat baseline
│
├── web/                          # static frontend (existing)
│   ├── index.html                # landing + signup
│   ├── inference-sample-v3.html  # canonical issue sample
│   ├── inference-sample.html     # v1 historical
│   ├── inference-sample-v2.html  # v2 historical
│   ├── package.json              # dev server
│   └── ...
│
├── src/inference/                # Python package
│   ├── __init__.py
│   ├── config.py                 # env loading, paths
│   ├── db.py                     # SQLite layer
│   │
│   ├── data/
│   │   ├── api_football.py       # client for API-Football Pro (sole live provider)
│   │   ├── patches.py            # loader for data/patches/YYYY-MM-DD.json overrides
│   │   ├── openfootball.py       # static schedule loader
│   │   └── models.py             # pydantic models for matches, lineups, stats
│   │
│   ├── content/
│   │   ├── api.py                # OpenAI Responses API wrapper (gpt-5.5 content + gpt-5.4-nano utility, cost tracking)
│   │   ├── extract.py            # raw API → DayContext normalization
│   │   ├── prompts/              # markdown system prompts per generator
│   │   │   ├── editor_system.md
│   │   │   ├── team_sheet_system.md
│   │   │   ├── here_and_there_system.md
│   │   │   ├── back_story_system.md
│   │   │   ├── where_played_before_system.md
│   │   │   ├── story_behind_number_system.md
│   │   │   ├── added_time_system.md
│   │   │   └── _response_format.md
│   │   └── generators/
│   │       ├── editor.py
│   │       ├── team_sheet.py
│   │       ├── here_and_there.py
│   │       ├── back_story.py
│   │       ├── where_played_before.py
│   │       ├── story_behind_number.py
│   │       ├── added_time.py
│   │       └── from_the_stands.py
│   │
│   ├── subscribers/
│   │   ├── model.py              # ReaderProfile pydantic model
│   │   ├── store.py              # SQLite CRUD
│   │   └── api.py                # HTTP endpoint for signup form (Fastify-style?)
│   │
│   ├── delivery/
│   │   ├── compose.py            # per-reader edition composer
│   │   ├── render.py             # Jinja → HTML + plain-text
│   │   ├── email.py              # Resend integration
│   │   └── templates/            # Jinja templates (port of inference-sample-v3.html)
│   │       ├── inference.html.j2
│   │       └── inference.txt.j2
│   │
│   └── orchestrate/
│       ├── daily.py              # the daily pipeline runner
│       └── checkpoint.py         # JSONL checkpoint/resume
│
├── data/                         # editorial / override data (committed)
│   └── patches/                  # YYYY-MM-DD.json — manual corrections + editorial context
│
├── scripts/                      # one-off CLI commands
│   ├── data_spike.py             # validate field coverage on a historical match
│   ├── render_sample.py          # render inference.html for a fake reader
│   ├── send_test.py              # send a test email to one address
│   └── run_day.py                # manual single-day pipeline trigger
│
├── output/                       # generated artifacts (gitignored)
│   ├── inferences/               # rendered issues by date
│   ├── cache/                    # API response cache
│   └── logs/
│
└── tests/                        # minimal pytest suite
    ├── test_extract.py
    ├── test_compose.py
    └── fixtures/                 # canned API responses for offline testing
```

---

## Phasing

### Phase 0 — Foundations (May 15 – May 22)

Goal: working data pipeline against one historical match, end-to-end-renderable, no email yet.

Concrete deliverables:

- [ ] Python project bootstrapped (pyproject.toml, src layout, pytest)
- [ ] `.env.example` with all required keys listed
- [ ] **Data spike**: `scripts/data_spike.py` pulls one historical WC match (e.g. ARG–FRA 2022 final) through **API-Football alone**. Answers one binary question per [`api-research.md`](api-research.md): *can API-Football alone provide enough structured truth for a daily casual fanzine?* Documents which fields are populated, which are empty, which need calculation, which would need a patch. *(Distinct from the existing voice spike at `spike/`, which is already validated on gpt-5.5.)*
- [ ] API client module (`data/api_football.py`) with response caching to disk
- [ ] Patch loader (`data/patches.py`) — reads `data/patches/YYYY-MM-DD.json`, applies overrides after API fetch and before generation
- [ ] pydantic models for Match, Lineup, PlayerStat, GroupStanding, MatchEvent
- [ ] **LLM client wrapper** (`content/api.py`) — single `.generate(instructions, input, preset)` interface around the `openai` SDK's **Responses API**. Two presets: `content` (model=`gpt-5.5`, `reasoning.effort=medium`, `text.verbosity=medium`) and `utility` (model=`gpt-5.4-nano`). Cost tracking. No Batch wiring; no cheap/premium routing. Port system prompts from `spike/prompts/` (already validated).
- [ ] **One generator end-to-end**: TEAM SHEET, taking a Match + ReaderProfile, calling the `content` preset, returning structured output (markdown + extracted facts)
- [ ] `scripts/render_sample.py` — composes a mocked Inference HTML for one reader, outputs to `output/inferences/sample.html`

**Unblockers needed from user** (Phase 0):

- Sign up for **API-Football Pro** ($19/mo). Save key to `.env` as `API_FOOTBALL_KEY`. This is the **sole live data provider** unless the spike proves otherwise.
- **Do not sign up for Sportmonks** at this stage. It's contingency-only — revisit after the data spike if an essential field is missing.
- `OPENAI_API_KEY` is already configured and validated. One key serves both `gpt-5.5` (content) and `gpt-5.4-nano` (utility) via the Responses API. No DeepSeek or Anthropic keys needed.

### Phase 1 — MVP pipeline (May 23 – May 31)

Goal: all six section generators working, full HTML email rendering, ability to render-and-not-send a complete Inference for a fake reader.

Concrete deliverables:

- [ ] All 8 generators built (`team_sheet`, `editor`, `here_and_there`, `back_story`, `where_played_before`, `story_behind_number`, `added_time`, `from_the_stands`)
- [ ] System prompts as markdown files in `content/prompts/` — each generator has its own voice spec
- [ ] **`delivery/compose.py`**: takes ReaderProfile + DayContext, runs needed generators, returns a fully-populated `Inference` object
- [ ] **`delivery/render.py`**: Jinja template port of `inference-sample-v3.html` into `inference.html.j2`. All grunge styling inlined for email-safe HTML. Plain-text fallback in `inference.txt.j2`
- [ ] `scripts/render_sample.py` produces a real Inference for a fake Marcus reader against a real historical day
- [ ] Smoke tests: one regression test per generator catching obvious failure modes (empty output, schema invalid, etc.)

### Phase 2 — Pre-launch (June 1 – June 10)

Goal: subscribers can sign up for real, pre-launch issue ships, full pipeline runs against opening-match data on June 10 dress rehearsal.

Concrete deliverables:

- [ ] **Subscriber backend**: minimal HTTP endpoint (`subscribers/api.py`) the signup form POSTs to. Stores in SQLite. Deployed somewhere stable.
- [ ] Landing page's signup form updated to POST to real endpoint instead of `localStorage`
- [ ] **Resend integration** (`delivery/email.py`): send one fully-rendered Inference to one address. Verify HTML renders in Gmail / Apple Mail / Outlook
- [ ] **`orchestrate/daily.py`**: the full pipeline run. Fetch → extract → generate (universal + per-reader) → compose → send → log.
- [ ] **GitHub Actions cron workflow** (`.github/workflows/daily.yml`) running the pipeline at ~02:00 ET daily during the tournament window
- [ ] Pre-launch issue (Inference N° 00) — tournament preview, group breakdowns, key players, no predictions. Sent ~June 8–9 to whoever's signed up
- [ ] **Dress rehearsal**: June 10 — run the full pipeline against the *previous day's* historical fixtures, send to a test address list, fix anything that breaks

### Phase 3 — Tournament live (June 11 – July 19)

Goal: ship 35 daily editions without an outage.

Concrete deliverables:

- [ ] **Inference N° 01** ships June 11 morning
- [ ] Daily monitoring: confirm each issue sent, error log surfaced
- [ ] Iteration window: refine prompts based on reading the output
- [ ] **Inference N° 35** ships July 19 morning

### Phase 4 — Post-tournament / stretch (Aug 2026 onwards)

If we got through the tournament, the optional ambitions:

- [ ] Audio formats (THE TOUCHLINE, WALKOUT, FULL-TIME) — TTS pipeline
- [ ] THE GANTRY live commentary (real-time text thread)
- [ ] Web archive of all 35 issues
- [ ] StatsBomb open-data ingestion if/when released → retrospective archive with full pass-network renders

---

## First week — concrete order of operations

This week (May 15–22). In strict dependency order:

1. **Sign up for API-Football Pro** (user action, ~10 min). Sportmonks is *not* signed up.
2. **Bootstrap Python project** — `pyproject.toml`, src layout, dependencies, `.env.example`.
3. **Write the data spike** — `scripts/data_spike.py`. Pull one historical match through API-Football alone. Print which fields are present, which are missing, which would need a patch.
4. **Build the API client** based on what the spike revealed. Disk-cache all responses (rate limits matter). Stub the patch loader at `data/patches.py`.
5. **Build pydantic models** for what the APIs actually return.
6. **Write the LLM wrapper** — `content/api.py`. Multi-provider, cost-tracking, retry-on-rate-limit.
7. **Build the first generator** — TEAM SHEET. Take a Match + ReaderProfile, return generated markdown + key facts.
8. **Render a fake Inference** — wire TEAM SHEET output into the existing v3 HTML template, save to disk, open in browser.

If end-of-week we can open a real-data-backed Inference HTML in the browser, Phase 0 is done.

---

## Open decisions to resolve before Phase 2

- **Subscriber backend hosting.** Options: tiny VPS, Cloudflare Workers + D1, Fly.io, Vercel + Postgres, or accept the constraint and just host on a cheap Hetzner box. Default: **Fly.io** (free tier exists, Python-friendly, persistent volumes for SQLite).
- **Domain.** The brand needs a URL. Candidates: `the-inference.com`, `theinference.fc`, `inference.kop`, `matchday.inference`. Park one before pre-launch.
- **Free vs paid.** Per PROMPT.md original recommendation: free for the WC, decide post-event. Sticking with that.
- **Privacy posture.** Do we send `ReaderProfile` to the LLM provider? Default: yes (it's the basis of personalisation) but we should not send the email address. Generator receives display-name + teams + lens.
- **AI honesty disclosure.** Footer should say "AI-generated, stat-grounded, human-edited prompts" explicitly. The fanzine aesthetic already implies it, but the colophon should be unambiguous.

---

## Out of scope (until further notice)

- Live in-match push notifications
- Per-team newsletters (subscriber chooses teams, that's the personalisation)
- Discord / social integration
- Web archive during the tournament (the email IS the product for the live window)
- Predictions of any kind
- Editorial commentary or opinion writing
- AI-generated imagery (photography, illustration) — the typography handles "visual"
- Custom domain email (we use Resend's verified sender; brand it later)
- Payment / paywall
- A11y audit beyond the basics (focus states, semantic HTML, alt text on critical SVGs)

---

## References

- [`design.md`](design.md) — visual identity spec (locked)
- [`nomenclature.md`](nomenclature.md) — language spec (locked)
- [`api-research.md`](api-research.md) — data-provider landscape + API-Football-only decision (authoritative)
- [`model-price-research.md`](model-price-research.md) — AI pricing reference
- [`web/inference-sample-v3.html`](web/inference-sample-v3.html) — canonical issue design
- [`web/index.html`](web/index.html) — landing + signup
- [Project memory](.claude/projects/-home-nicholas-claude-code-projects-world-cup-project/memory/MEMORY.md) — durable context for future Claude sessions
- [`PROMPT.md`](PROMPT.md) — original brief (historical reference)
