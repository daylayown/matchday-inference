# THE INFERENCE — Project Context

> **The first file Claude should read in any new session for this project.**
> Last updated: 2026-06-03.

---

## What this is

**THE INFERENCE** is a personalized, AI-generated daily matchday zine for the 2026 FIFA World Cup (June 11 – July 19, 2026). Each morning of the tournament, every subscriber receives their own individually-composed issue — assembled overnight by an OpenAI-powered pipeline against real match data, written for their chosen teams and tactical lens.

The publication's mood: *Nirvana in 1990 — grunge, raw, here to shake up the industry*. Not The Athletic. Not ESPN. A DIY matchday fanzine stapled by a machine, proudly.

**The name "THE INFERENCE"** mates football and AI naturally:
- Football: *"great inference by the defender to read that through ball"* — anticipation, reading the game
- AI/ML: model inference — the act of generating output from a trained model

## Current status

**Phase 0, 1, and most of Phase 2 done.** As of 2026-05-19, the production spine is in place: a real-data-backed Inference HTML+TXT renders all 8 sections per reader via the daily orchestrator, against API-Football data + a JSON patch layer for editorial seeds. **8 of 8 generators built.** **Daily orchestrator built** (`src/inference/orchestrate/daily.py`) — fetches → patches → runs 8 generators × N readers → renders → saves. **Resend email pipeline built** (HTML + plain-text fallback). **Subscriber SQLite store + FastAPI signup endpoint built.** **GitHub Actions cron workflow** ready (`.github/workflows/daily.yml`). **33 passing smoke tests.** **7 lenses** (Cultural Critic, Pub-Talker, Tactician, Romantic, Historian, The Diaspora, The Beat Reporter) shaped into all 8 generator prompts. Per-issue cost ~$0.16–$0.21 at gpt-5.5 placeholder pricing (~3-4 min wall time).

**The SITE is launch-ready as of 2026-06-03.** Everything needed to share the signup link with friends & family is **live and verified**: landing page (`matchdayinference.com`, Cloudflare Pages), signup endpoint (`api.matchdayinference.com`, Fly), GA4 analytics, Resend email (verified + test send confirmed to inbox), a crypto tip jar, honest landing copy, `www`→apex 301 redirect, and a fixed auto-deploy pipeline (GH Actions). A live signup smoke test passed end-to-end. **The ONLY work left is the daily-issue *content*, which the tournament needs by June 11 — not by the soft launch:** fill the 39 per-day `data/patches/YYYY-MM-DD.json` editorial-seed skeletons (already scaffolded), then run the June 10 dress rehearsal. **Full ordered detail in the "⏯️ PICK UP HERE" section below.**

## Naming notes

The project was developed under the working name "PROGRAMME". The rename to **THE INFERENCE** was completed on 2026-05-18 across all docs and the `web/` HTML files (samples renamed from `web/programme-sample-*.html` → `web/inference-sample-*.html`). `PROMPT.md` was left as-is (it captures the original brief and is historical). The `spike/` directory was also left as-is — it's a validated one-off prototype with rendered outputs that don't need re-running.

The matchday-programme *metaphor* still informs the editorial structure (team sheet, stats page, centre spread, manager's notes) even though the word "Programme" exits the masthead. Lowercase references to "matchday programme" / "matchday programmes" in design.md, codex-critique.md, api-research.md, and web/index.html are *intentional* metaphor — do not rename.

## Locked decisions (do not re-litigate)

| What | Locked to | Reference |
|---|---|---|
| **Name** | THE INFERENCE | This file |
| **Visual identity** | Grunge / DIY zine (Sub Pop / Nirvana 1990); cream + ink + pink + cobalt + highlighter yellow; Anton + Yeseva One + DM Sans + Space Mono + Allerta Stencil + Caveat | [`design.md`](design.md) |
| **Nomenclature** | Matchday-football vocabulary only; never "brief", "digest", "rundown", "summary"; section names: TEAM SHEET, STATS PAGE, CENTRE SPREAD, MANAGER'S NOTES, FROM THE STANDS, ADDED TIME; format names: THE TOUCHLINE, WALKOUT, FULL-TIME, THE GANTRY, THE MIXED ZONE | [`nomenclature.md`](nomenclature.md) |
| **Content shape** | Vibes-based personalized magazine, not stats-heavy; heritage features (HERE & THERE, BACK STORY, WHERE THEY PLAYED BEFORE); tournament-arc editor's column; typography-as-image; ~80% prose/visual, ~20% numbers | [`web/inference-sample-v3.html`](web/inference-sample-v3.html) |
| **Data sources** | **API-Football Pro ($19/mo) only.** Single live provider. Local JSON patch layer (`data/patches/YYYY-MM-DD.json`) for corrections, missing context, and editorial overrides — cheaper and safer than normalizing a second provider. Sportmonks / Statorium are contingency-only, evaluated *after* the Phase 0 data spike if API-Football fails on an essential field. xG is optional color, not infrastructure. Still no event-level x/y data; pass networks are a post-tournament feature. | [`api-research.md`](api-research.md), memory: `api-football-only-stack-locked`, `wc2026-data-landscape` |
| **AI provider** | OpenAI sole provider. Quality-first: **`gpt-5.5` is the default for all creative prose** (Responses API). `gpt-5.4-nano` for utility transforms (extraction, classification, normalization). `gpt-5.4-mini` reserved as an optional mid-tier fallback if volume grows. No cheap/premium routing in v1. **Only `OPENAI_API_KEY` needed.** No DeepSeek. No Anthropic. | [`llm-model-analysis.md`](llm-model-analysis.md), memory: `openai-only-stack-locked` |
| **Tech stack** | Python 3.13+ (venv on 3.14), pydantic v2, httpx, openai SDK, Jinja2, Resend, SQLite, GH Actions cron | [`PLAN.md`](PLAN.md) |

## Things to AVOID

- **The editorial-newsprint aesthetic** (Fraunces + cream + serif-display + mono-labels with single accent). That's the user's existing tucsondailybrief.com house style. Do not replicate it here. See memory: `avoid-tucson-daily-brief-aesthetic`.
- **Stats-heavy / no-takes austerity** from `PROMPT.md`. That was the original brief; project pivoted to vibes-based.
- **Live pass-network visualizations.** Data is gated behind enterprise contracts ($10k+). Build the renderer against the StatsBomb open-data schema as a *post-tournament archive feature* if/when WC 2026 event data is released by StatsBomb.
- **Photography or AI-generated imagery.** Typography is the visual layer. Rights issues + AI consistency problems + the photocopy aesthetic refuses both.
- **"AI startup" portmanteau names** ("FootGPT", "Eleven.ai", etc.). The name was chosen specifically to avoid this trap.
- **Soft drop shadows, rounded corners, polished editorial layouts.** The grunge aesthetic refuses all of these.
- **Scope creep** beyond the locked 5-week one-off scope. Audio formats, GANTRY live commentary, and the web archive are Phase 4 (post-tournament). Don't pull them forward without flagging it.

## Key files

| File | Purpose | Status |
|---|---|---|
| [`CLAUDE.md`](CLAUDE.md) | This file — read first | Current |
| [`PLAN.md`](PLAN.md) | Engineering roadmap, phases, deliverables | Current |
| [`design.md`](design.md) | Visual identity spec | Locked |
| [`nomenclature.md`](nomenclature.md) | Language / naming spec | Locked |
| [`llm-model-analysis.md`](llm-model-analysis.md) | Current model strategy (gpt-5.5 default + gpt-5.4-nano utility) | Authoritative as of 2026-05-16 |
| [`api-research.md`](api-research.md) | Data-provider landscape + API-Football-only decision + patch-layer design | Authoritative as of 2026-05-18 |
| [`model-price-research.md`](model-price-research.md) | AI provider pricing notes | Superseded for model selection; price points still useful |
| [`PROMPT.md`](PROMPT.md) | Original brief | Historical — assumptions superseded |
| [`spike/`](spike/) | Voice/prompt prototype (editor + match_brief + here_and_there for Marcus + Lin) | Built; validated on gpt-5.5 — outputs in `spike/output/`, nano baseline in `spike/output/archive-gpt-5-nano/` |
| [`web/index.html`](web/index.html) | Landing page + 3-step signup form | Built, grunge aesthetic, form persists to localStorage |
| [`web/inference-sample-v3.html`](web/inference-sample-v3.html) | Canonical issue design | Built, grunge aesthetic, 9 pages |
| [`web/inference-sample-v2.html`](web/inference-sample-v2.html) | Polished fanzine v2 | Historical, can delete |
| [`web/inference-sample.html`](web/inference-sample.html) | Stats-heavy v1 | Historical, can delete |
| [`web/package.json`](web/package.json) | `npm run dev` static server on port 3001 | Used for iPhone testing |
| [`src/inference/orchestrate/daily.py`](src/inference/orchestrate/daily.py) | Daily pipeline runner — the production spine | Built 2026-05-19 |
| [`src/inference/data/patches.py`](src/inference/data/patches.py) | JSON patch-layer loader (`data/patches/YYYY-MM-DD.json`) | Built 2026-05-19 |
| [`src/inference/delivery/email.py`](src/inference/delivery/email.py) | Resend wiring — `send_issue()` | Built 2026-05-19 |
| [`src/inference/subscribers/store.py`](src/inference/subscribers/store.py) | SQLite subscriber store | Built 2026-05-19 |
| [`src/inference/subscribers/api.py`](src/inference/subscribers/api.py) | FastAPI signup endpoint | Built 2026-05-19 |
| [`.github/workflows/daily.yml`](.github/workflows/daily.yml) | GH Actions cron for daily orchestrator | Built 2026-05-19; needs repo secrets |
| [`data/patches/2022-12-18.json`](data/patches/2022-12-18.json) | Sample patch / editorial seeds (ARG–FRA final) | Use as template for the real WC dates |
| [`data/readers.json`](data/readers.json) | Reader profiles (default source for `run_day.py`) | Built 2026-05-19 |
| [`tests/`](tests/) | Smoke test suite (33 passing, mocked LLM, no network) | Built 2026-05-19; +12 on 2026-06-02 |

## Engineering state

| Component | Status |
|---|---|
| Project skeleton (pyproject.toml, src/inference, tests/, scripts/, data/patches/) | **Bootstrapped 2026-05-18.** Editable install in `.venv` (Python 3.14). All runtime + dev deps installed. |
| API keys (.env) | `OPENAI_API_KEY` and `API_FOOTBALL_KEY` both configured |
| Voice/prompt spike (`spike/spike.py`) | **Built and validated on gpt-5.5** — distinct lens voices, wildcards firing; Chat Completions prototype only, do NOT pattern `src/inference` on it |
| Data client (API-Football) | **Built** — `src/inference/data/api_football.py` with disk caching to `output/cache/api-football/` |
| Data spike (`scripts/data_spike.py`) | **Run 2026-05-18, passed.** ARG–FRA 2022 final pulled across 7 endpoints. Verdict: API-Football alone carries enough for a casual fanzine. Per-player advanced stats (shots, passes, tackles, duels, dribbles, fouls, cards, penalty) populate for outfield players; a few genuine gaps (`goals.assists` null for Messi who had 1; `games.minutes` null in top-scorers list). Patches will cover edge cases. |
| Patch loader | **Built 2026-05-19.** `src/inference/data/patches.py` — loads `data/patches/YYYY-MM-DD.json` and exposes `apply_fixture_overrides`, `apply_stat_overrides`, `editorial_seed`, `day_context_overrides`. Editorial seeds for all 6 seeded generators (here_there_thread, story_behind_number, back_story, where_played_before, from_the_stands, anomalies). Sample for 2022-12-18 in `data/patches/`. |
| LLM client wrapper (Responses API, `src/inference/content/api.py`) | **Built 2026-05-18.** Two presets: `content` (gpt-5.5, reasoning=medium, verbosity=medium), `utility` (gpt-5.4-nano). Cost tracking via prefix-match on snapshot model IDs. `json_mode=True` opt-in. gpt-5.5 pricing is a placeholder ($2.50/$15 per 1M, matching spike) until OpenAI publishes official numbers. |
| Generators (8 of them) | **8/8 built — all wired end-to-end.** TEAM SHEET, EDITOR, HERE & THERE, STORY BEHIND THE NUMBER, BACK STORY, WHERE THEY PLAYED BEFORE, FROM THE STANDS, ADDED TIME. All validated end-to-end on ARG–FRA 2022 final across 5 lenses. Cost ~$0.16–$0.21/issue at gpt-5.5 placeholder pricing (~3-4 min wall time); higher end is when a reader follows BOTH teams in the same match → 2 TEAM SHEETs. Outputs at `output/{team_sheets,editor,here_and_there,story_behind_number,back_story,where_played_before,from_the_stands,added_time}/`. Known prompt-compliance gap: model occasionally returns `pull_quote` as string instead of `{text, attribution}` object — display handles both; switch to `json_schema` format if it bites repeatedly. |
| Lenses (voice registers) | **7 built** — Cultural Critic, Pub-Talker, Tactician, Romantic, Historian, The Diaspora, The Beat Reporter. Each one is a section in all 8 generator prompts. The Diaspora and The Beat Reporter added 2026-05-18; the 5 new generators codify all 7 the same way. Five fully-rendered 8-section issues live at `output/inferences/marcus__argentina__{pub-talker,tactician,romantic,historian,the-diaspora}.html` for cross-lens comparison. The `location` field on ReaderProfile (added 2026-05-19) anchors The Diaspora lens on a real city instead of an invented one. |
| Email pipeline (Resend) | **Built 2026-05-19.** `src/inference/delivery/email.py` — `send_issue(to, subject, html, text)` returning a `SendResult`. Requires `RESEND_API_KEY` to actually send. Plain-text fallback template at `src/inference/delivery/templates/inference.txt.j2`; `render_inference_txt()` mirrors `render_inference()`. |
| Jinja template + renderer | **Built 2026-05-18, expanded 2026-05-19.** `src/inference/delivery/templates/inference.html.j2` parameterized for all 8 sections (TEAM SHEET, EDITOR, HERE & THERE, STORY BEHIND THE NUMBER, BACK STORY, WHERE THEY PLAYED BEFORE, FROM THE STANDS, ADDED TIME — Pages 02–09). Plain-text fallback `inference.txt.j2` mirrors structure. `src/inference/delivery/render.py` exposes `render_inference()` + `render_inference_txt()`. End-to-end scripts: `scripts/render_inference.py` (one reader, --no-llm cache-friendly) and `scripts/run_day.py` (full orchestrator). Verified: ~77K HTML file rendering all 8 sections + 2 TEAM SHEETs on the ARG–FRA 2022 final via the orchestrator. |
| Subscriber backend | **Built 2026-05-19.** `src/inference/subscribers/store.py` — `SubscriberStore` over stdlib `sqlite3` with schema (slug PK, email UNIQUE, profile_json, created_at, verified_at, unsubscribed_at). `src/inference/subscribers/api.py` — FastAPI app with `POST /signup`, `POST /unsubscribe`, `GET /health`. Add `pip install -e '.[web]'` for the web extras. Defaults to `data/subscribers.sqlite`. `scripts/run_day.py --source sqlite` loads readers from this store. |
| Daily orchestrator | **Built 2026-05-19.** `src/inference/orchestrate/daily.py` — `run_for_date(date_iso, readers)` runs the full pipeline: fetch fixtures → apply patches → per-reader run 8 generators → render HTML → save. Per-section failures are captured but don't halt other sections. CLI: `.venv/bin/python scripts/run_day.py 2022-12-18 --issue 04`. Verified end-to-end on the 2022 final, $0.21 / 3.7 min for Marcus following Argentina+France. |
| GitHub Actions cron | **Built 2026-05-19.** `.github/workflows/daily.yml` — cron at 06:30 UTC, tournament-window guard (June 10–July 19 2026), workflow_dispatch override for manual runs, auto-computed issue number, uploads `output/inferences/` as artifacts. Needs `OPENAI_API_KEY`, `API_FOOTBALL_KEY`, `RESEND_API_KEY`, `FROM_EMAIL` in repo secrets before going live. |
| Smoke tests | **Built 2026-05-19; expanded 2026-06-02.** 33 passing tests in `tests/` — one per generator (mocked LLM), patches loader, subscribers store + `list_all`, dispatch/email glue, patch-template (pinned to orchestrator seed keys), render branding, `run_day` readers-shape tolerance. `.venv/bin/python -m pytest tests/`. |
| Web frontend | **Built and working** (landing page + 3 sample HTMLs) |

## What was built 2026-05-18 (session log)

One session took the project from zero Python code to a working end-to-end pipeline. Captured here so a future session has the chronology without reading the git history:

1. **Decision change** — dropped Sportmonks from the launch stack after re-reading `api-research.md`. API-Football is now the sole live data provider plus a local JSON patch layer. (User caught that the older "API-Football + Sportmonks" plan didn't match the doc they'd already written.)
2. **Project-wide rename** — PROGRAMME → THE INFERENCE across all docs, web HTML samples (renamed `web/programme-sample-*.html` → `web/inference-sample-*.html`), memory file slugs (`programme-*` → `inference-*` for two memories), and the `src/inference/` package path. `spike/` and `PROMPT.md` deliberately left as historical artifacts.
3. **Python bootstrap** — `pyproject.toml` with hatchling backend, src layout, all runtime + dev deps, editable install in existing `.venv` (Python 3.14).
4. **Data spike** — `src/inference/data/api_football.py` (httpx client with disk caching) + `scripts/data_spike.py` pulling the ARG–FRA 2022 final across 7 endpoints. **Verdict: API-Football alone passes the binary test.**
5. **LLM wrapper** — `src/inference/content/api.py` on the Responses API. Two presets (`content`/`utility`), prefix-match cost lookup so pinned model snapshots resolve correctly, `json_mode=True` opt-in.
6. **3 generators built end-to-end** — TEAM SHEET, EDITOR, HERE & THERE. Pattern: pydantic-typed Match + ReaderProfile → markdown prompt file → ContentClient → structured JSON. Per-generator cache at `output/{team_sheets,editor,here_and_there}/` for fast iteration.
7. **Jinja template** — copied `web/inference-sample-v3.html` to `src/inference/delivery/templates/inference.html.j2`, then surgically templated the head/header/reader-card/footer/TEAM SHEET section. Editor and Here & There sections also templated when their generators landed.
8. **2 new lenses added** — The Diaspora and The Beat Reporter, both shaped into all three generator prompts. Demonstrated dramatic voice differentiation on the same source data: same Marcus profile, same final, three radically different reading experiences. The Diaspora landed Marcus's chef wildcard organically through kitchen-as-anchor.

Cost shape verified: ~$0.06–$0.09 per fully-rendered issue (3 generators). At 50 readers × 35 days that's ~$150 LLM bill for the tournament window.

## What was built 2026-05-19 (session log)

Tasks: run the other 4 lenses on the cache; build the remaining 5 generators.

1. **Ran 4 lens variants** on the cached ARG–FRA 2022 final via the 3-generator pipeline that was the state-of-art end of 2026-05-18: Pub-Talker, Tactician, Romantic, Historian. Outputs at `output/inferences/marcus__argentina__<lens>.html`. Each cost ~$0.08, ~90s wall time. (Note: at that point the pipeline only ran 3 of 8 generators; the 5 new ones below were added the same session.)
2. **Built 5 new generators end-to-end** — `story_behind_number`, `back_story`, `where_played_before`, `from_the_stands`, `added_time`. Each is a markdown prompt in `src/inference/content/prompts/` + a generator module in `src/inference/content/generators/` + a new Jinja section block. The 7 lenses are codified in each prompt.
3. **Curated source-data payloads** for the 5 new sections, tuned to the ARG–FRA 2022 final: `SBN_INPUT_2022_FINAL` (Mbappé's hat-trick vs Hurst 1966), `BACK_STORY_2022_FINAL` (the 2018 R16 match between the same teams), `VENUE_2022_FINAL` (Lusail's first WC), `STANDS_QA_2022_FINAL` (a plausible reader Q about Deschamps' HT subs), `ANOMALIES_2022_FINAL` (6 candidate kickers). All in `scripts/render_inference.py`.
4. **Expanded the Jinja template** — 5 new section blocks for Pages 05–09, mapped onto CSS classes already present in the template (the template was originally copied from v3-sample so the styling was waiting). All new sections gated by `{% if … %}` so optional sections render gracefully if generators are skipped.
5. **Refactored `scripts/render_inference.py`** — introduced `_cached_or_generate` helper that wraps the per-generator cache/run/save flow uniformly across all 8 generators. Reduces ~120 lines of repeated logic to one function call per generator.
6. **Smoke-tested** by running the full 8-section pipeline on a fresh lens (The Diaspora). All 8 generators returned schema-compliant JSON, all 5 new template sections rendered correctly, total cost $0.165, total wall time ~3 min.

After the 5 new generators landed, I re-ran the 4 earlier lenses (Pub-Talker, Tactician, Romantic, Historian) with `--no-llm` to fill in the 5 new sections without regenerating the cached 3 — total $0.32, ~5 min. End state: 5 fully-rendered 8-section issues at `output/inferences/marcus__argentina__{pub-talker,tactician,romantic,historian,the-diaspora}.html`.

## What was built 2026-05-19 (Phase 2 session log)

Push to take the project from "all 8 generators built" to "production pipeline ready, awaiting domain + hosting."

1. **Patches loader** (`src/inference/data/patches.py`). Reads `data/patches/YYYY-MM-DD.json`. Exposes overrides for fixture entries and team statistics, plus editorial-seed lookup for the 6 seeded generators and day-context overrides for the EDITOR. Sample patch at `data/patches/2022-12-18.json` captures all the ARG–FRA final's editorial context (here_there_thread, back_story, where_played_before, story_behind_number, from_the_stands, anomalies, day_context).
2. **Daily orchestrator** (`src/inference/orchestrate/daily.py`). One call: `run_for_date(date_iso, readers)`. Walks each reader's teams → fetches fixtures via API-Football (cached) → applies patches → runs the 8 generators where editorial seeds exist → renders HTML → saves to `output/inferences/<date>__<slug>.html`. Per-section failure isolation. CLI entry: `scripts/run_day.py`.
3. **Email pipeline** (`src/inference/delivery/email.py` + `inference.txt.j2`). Resend-backed `send_issue()` returning a `SendResult` dataclass. Plain-text fallback template mirrors HTML structure. Both renderers exposed in `delivery/render.py` (`render_inference`, `render_inference_txt`).
4. **GitHub Actions cron** (`.github/workflows/daily.yml`). Cron 06:30 UTC; tournament-window guard (June 10–July 19 2026); `workflow_dispatch` for manual runs; auto-computes issue number from date. Needs `OPENAI_API_KEY`, `API_FOOTBALL_KEY`, `RESEND_API_KEY`, `FROM_EMAIL` in repo secrets.
5. **Subscriber backend** (`src/inference/subscribers/{store,api}.py`). SQLite store (slug PK, email UNIQUE, profile_json blob, verified/unsubscribed timestamps). FastAPI signup endpoint (`POST /signup`, `POST /unsubscribe`, `GET /health`). New `[web]` extras in `pyproject.toml` for fastapi + uvicorn so the GH Actions runner doesn't pull them.
6. **`location` field on ReaderProfile.** Added `location: str | None` to the model. Threaded a Reader-fields bullet into all 8 prompts: "If non-null, the reader's city. The Diaspora lens MUST anchor on it directly. Other lenses can use it for color, optional. NEVER invent a location if `location` is null."
7. **Smoke test suite** (`tests/`). 21 passing tests: one per generator (mocked LLM), 8 patches-loader tests, 5 subscriber-store tests. Runs in 0.03s; no network. `.venv/bin/python -m pytest tests/`.
8. **End-to-end verification.** Ran the daily orchestrator against the 2022-12-18 patch + cached API-Football data for Marcus (Argentina + France). Result: 9 sections rendered (2 TEAM SHEETs + 7 universal), $0.21, 3.7 min, 77K HTML.

What's NOT done and is waiting on user decisions or external setup:
- Domain purchase + DNS — user is on it.
- Hosting choice for the signup endpoint — user is on it. The FastAPI app is hosting-agnostic; will run on Fly.io, a VPS, Cloudflare Workers via wrangler, or any container host.
- Resend verified sender domain — needs the domain first.
- Wiring the landing page form (`web/index.html`) at the live `/signup` endpoint — quick HTML/JS change once the endpoint has a URL.
- Real per-day editorial-seed patches for the actual June 11–July 19 tournament window. The patches are the only manual content step in the pipeline; everything else is automated.
- June 10 dress rehearsal.

Cost shape verified at scale: ~$0.16–$0.21 per fully-rendered issue. At 50 readers × 35 days that's ~$300 LLM bill — higher than the previous estimate because the orchestrator now renders TWO TEAM SHEETs for readers who follow both teams in a given match, which is the right thing.

## What was built 2026-06-02 (rebrand + autonomous tooling)

Domain/deploy prep earlier in the day (see memory `inference-phase2-ready`); then a user-facing rebrand + a batch of autonomous tooling:

1. **User-facing rebrand to "MATCHDAY INFERENCE."** Proper-name "THE INFERENCE" lockups → "MATCHDAY INFERENCE" in `web/index.html`, the issue template (`inference.html.j2`/`.txt.j2`), and the email From-name + subject (`email.py`). The giant stenciled masthead word stays the single iconic **INFERENCE** (deliberate). Landing-page count-noun usages ("your Inference", "an Inference") stay short. Internal code — docstrings, CSS comments, the `inference.subscriber` localStorage key, and the `src/inference/` package path — intentionally NOT renamed. (Do not "fix" any of these back.)
2. **Bug fix:** `_load_readers` in `run_day.py` now accepts both a bare list and the `{"readers": [...]}` envelope from `/export`. Previously the live GH Actions subscriber path would have crashed once the export secrets were set (the committed sample is a bare list, which hid it).
3. **`run_day.py --send`** (backlog A) — `src/inference/delivery/dispatch.py::send_results` looks up each reader's email in the store and sends via Resend; orchestrator now writes a `.txt` per reader (`ReaderResult.txt_path`) for the plain-text fallback.
4. **`scripts/new_patch.py`** (backlog C) — scaffolds a fill-in-the-blanks patch via `src/inference/data/patch_template.py::skeleton_patch`; a test pins `SEED_KEYS` to the orchestrator's `editorial_seed` calls.
5. **`scripts/subscribers.py`** (backlog D) — `{list,verify,unsubscribe,export}` over new `SubscriberStore.list_all()`.
6. **Tests 21 → 33**, all green. Backlog E (gpt-5.5 pricing) and F (run 2 more lenses, ~$0.32 API) left — F costs money.

## What was built 2026-06-03 (launch-readiness session log)

Took the site from "infra deployed" to "launch-ready + proven." All verified live:

1. **GA4** — Measurement ID `G-F8NJVND77X`, gtag.js in `<head>` of `web/index.html`.
2. **OG / Twitter link-preview tags** — link shares now lead with "MATCHDAY INFERENCE" (iMessage was scraping the post-em-dash `<title>` slice). iMessage caches previews per-URL; bust with a `?v=N` query string when testing.
3. **Resend email — fully live.** User created the account (it had only ever been a *code-level* decision, which is why it was unfamiliar — no account ever existed). Verified `matchdayinference.com` via Resend's Cloudflare auto-config button (SPF + MX + DKIM; DMARC not added by auto-config and not required). `RESEND_API_KEY` + `FROM_EMAIL="MATCHDAY INFERENCE <matchday@matchdayinference.com>"` set as GH secrets **and** in local `.env`. A live `send_issue()` test landed in the user's inbox.
4. **Crypto tip jar** — `.tipjar` section in `web/index.html` (above `<footer>`): static QR (`web/tip-qr.svg`, segno-generated) + MetaMask address `0x4a6232e14cFD20B63a30f87a4ED7E89a4D9edC7e`, labeled "USDC / ETH · Base network". Started as a Bitcoin Lightning QR, but MetaMask doesn't support Lightning; a fiat (Ko-fi) option was dropped when Stripe onboarding proved too heavy for a tip jar. See [[tip-jar-crypto]].
5. **Landing-page honesty pass.** The page advertised the PRE-PIVOT vision. Removed the "a full broadcast" section (3 audio formats + The Gantry live commentary — all unbuilt Phase-4). Rewrote section 02 to the **8 sections the pipeline actually renders** (Your Day, The Editor's Desk, Here & There, Story Behind the Number, Back Story, Where They Played Before, From the Stands, Added Time). Purged event-data claims the API-Football-only stack can't deliver (pass networks, shot maps, PPDA, F3 entries, progressive carries) from the mocks + specimen card. Softened From-the-Stands (no reply-loop promise). Pullquote "in every language" → tournament-length (pipeline is English-only). **Do NOT re-add audio/live/event-data/multi-language claims.**
6. **Masthead cleanup** — removed the "ZINE / NOT PRESS" + "STAPLED · NOT PRESSED" stamps (they overlapped the INFERENCE wordmark on phones); kept "DRAFT N° 00".
7. **Cloudflare auto-deploy FIXED.** The native GitHub→Pages integration deployed once at setup then silently stopped (broke when repo history was squashed pre-public). Diagnosed via `npx wrangler pages deployment list`. Replaced with `.github/workflows/deploy-web.yml` — deploys `web/` via `cloudflare/wrangler-action@v3` on every push touching `web/**` (+ `workflow_dispatch`). New GH secrets `CLOUDFLARE_API_TOKEN` (Pages:Edit) + `CLOUDFLARE_ACCOUNT_ID=3680dcc3b4e6918d7160b2fcd2a9bb89`. **Pages project name: `matchday-inference`.** Verified working twice. `wrangler` is installed + OAuth-logged-in locally → manual deploy: `npx wrangler pages deploy web/ --project-name=matchday-inference --branch=master`.
8. **`www` → apex 301 redirect** — proxied `www` CNAME + Cloudflare "Redirect from WWW to Root" rule. Verified (path + query preserved).
9. **Live signup smoke test PASSED** — POST to `api.matchdayinference.com/signup` → 200 + slug, row confirmed in Fly SQLite, then hard-deleted (DB back to 0 rows). Full browser→Pages→Fly→SQLite path proven.
10. Queued autonomous tasks **A** (39 patch skeletons `2026-06-11`…`2026-07-19`, scaffolded) and **B** (stripped dev preview bar from `inference.html.j2`) both DONE.

All 6 GH Actions secrets + 2 Cloudflare secrets are set. 33 tests still green.

## ⏯️ PICK UP HERE — site launch-ready; only daily-issue CONTENT remains (2026-06-03)

**The site is done and live.** You can **soft-launch tomorrow (share the signup link with friends & family) right now** — nothing blocks it. Signup, GA4 analytics, Resend email, the crypto tip jar, the `www`→apex redirect, and push-to-deploy (GH Actions) are all live and verified. The live signup smoke test passed end-to-end.

**The only work left is the daily-issue CONTENT, needed by June 11 (tournament kickoff), NOT by the soft launch:**

1. **Fill the 39 patch skeletons** `data/patches/2026-06-11.json` … `2026-07-19.json` — the editorial seeds (`here_there_thread`, `story_behind_number`, `back_story`, `where_played_before`, `from_the_stands`, `anomalies`, `day_context`) for each matchday. Skeletons are already scaffolded (via `scripts/new_patch.py`); the filled template to copy from is `data/patches/2022-12-18.json`. This is the **only manual content step**. Rest days in the range can have their skeleton file deleted. **You do NOT need all 39 to soft-launch — prioritize the June 11 opening day first; the rest can trickle in before each matchday.**
2. **June 10 dress rehearsal** — `scripts/run_day.py 2026-06-10 --issue 00` against a preview patch, then `--send` a real test issue to yourself to confirm the whole pipeline fires end-to-end on a live-like day. (Email send is already proven; this proves it on a full generated issue.)

### To deploy any landing-page change
Just `git push` anything touching `web/**` — the `deploy-web.yml` GH Actions workflow auto-deploys to Cloudflare Pages. For an immediate manual deploy: `npx wrangler pages deploy web/ --project-name=matchday-inference --branch=master`.

### Optional polish (non-blocking)
- **DMARC** TXT record (`_dmarc` = `v=DMARC1; p=none;`) — only if mail ever lands in spam (test send landed in inbox, so not urgent).
- **Disconnect the dead native Cloudflare Git integration** in the Pages dashboard (tidiness — GH Actions is the real deploy path now).
- **Backlog E:** update the gpt-5.5 price placeholder in `src/inference/content/api.py` if OpenAI published official numbers.
- **Backlog F:** render Cultural Critic + The Beat Reporter at full 8 sections (~$0.32, ~6 min) for complete cross-lens samples (only 5 of 7 lenses have full cached output).

## Next session — first actions

All infra/setup is DONE and the site is launch-ready (see "⏯️ PICK UP HERE" above for the authoritative state). **Only two things remain, both content, both for June 11 — not for the soft launch:**

1. **Fill the patch skeletons**, June 11 opening day first. Skeletons scaffolded at `data/patches/2026-06-11.json` … `2026-07-19.json`; copy the shape from `data/patches/2022-12-18.json`. Only manual content step.
2. **June 10 dress rehearsal:** `scripts/run_day.py 2026-06-10 --issue 00` against a preview patch, then `--send` a test issue to yourself.

Everything in the older "Blocking — user-side decisions" list (domain, hosting, endpoint deploy, form wiring, secrets, GA4, Resend, www, smoke test) is **done** — do not redo it; verify against the PICK UP HERE checkpoint first.

### Autonomous nice-to-haves (no user input required)

Identified end of 2026-05-19 but not done; user decided none felt pressing yet. Pick up if/when wanted:

A. **DONE 2026-06-02.** ~~Wire email sending into `run_day.py`~~ — `run_day.py --send` now dispatches each rendered issue via Resend, backed by `src/inference/delivery/dispatch.py::send_results` (looks up emails in the subscriber store, injectable `send_fn` for tests). The orchestrator also writes a `.txt` per reader (`ReaderResult.txt_path`) so the email gets its plain-text fallback.
B. **DONE 2026-06-02.** ~~`DEPLOYMENT.md` + `Dockerfile` + `fly.toml`~~ — built, and the app is now **deployed live** to Fly (`matchday-inference-signup.fly.dev`). See the PICK UP HERE checkpoint.
C. **DONE 2026-06-02.** ~~Patch template generator~~ — `scripts/new_patch.py <date>` (+ `src/inference/data/patch_template.py::skeleton_patch`) emits a fill-in-the-blanks patch JSON with every editorial-seed block stubbed. A test pins `SEED_KEYS` to the orchestrator's `editorial_seed` calls so the template can't drift from the pipeline. `--stdout`/`--force` flags; refuses to clobber existing patches.
D. **DONE 2026-06-02.** ~~Subscriber admin script~~ — `scripts/subscribers.py {list,verify,unsubscribe,export}` over a new `SubscriberStore.list_all()`. `--db PATH` override; `list --active`; `export` writes the bare-list shape `run_day.py --source json` reads.
E. **gpt-5.5 pricing TODO** — `src/inference/content/api.py` uses gpt-5.4's $2.50/$15-per-1M as placeholder. Update `PRICES` if OpenAI has published official 5.5 numbers.
F. **Run Cultural Critic + The Beat Reporter at full 8 sections** for cross-lens coverage. Currently only 5 of 7 lenses have full 8-section cached output. ~$0.32, ~6 min.

## How to iterate (quick commands)

```bash
# Full daily orchestrator (production spine) — date + issue number.
# Loads readers from data/readers.json by default; --source sqlite for the live store.
.venv/bin/python scripts/run_day.py 2022-12-18 --issue 04
.venv/bin/python scripts/run_day.py 2022-12-18 --source sqlite

# Render an issue for one reader end-to-end (8 generators, ~$0.16-0.21, ~3-4 min)
.venv/bin/python scripts/render_inference.py

# Same, but reuse cached generator outputs where they exist (per-generator cache key)
.venv/bin/python scripts/render_inference.py --no-llm

# Pick a different lens or team
.venv/bin/python scripts/render_inference.py --lens "The Diaspora"
.venv/bin/python scripts/render_inference.py --team France --lens Tactician

# Just TEAM SHEET (one generator, ~$0.04)
.venv/bin/python scripts/render_team_sheet.py --lens Pub-Talker

# Re-run the data spike (against cache; --no-cache to refresh from API)
.venv/bin/python scripts/data_spike.py

# Run the test suite (mocked LLM, no network — 33 tests, ~130ms)
.venv/bin/python -m pytest tests/

# Stand up the signup endpoint locally (after `pip install -e '.[web]'`)
uvicorn inference.subscribers.api:app --reload --port 8000
# Then POST {email, display_name, teams, lens, ...} to http://localhost:8000/signup

# Preview rendered HTML in browser
# Either: open the file:// URL the render script prints
# Or:
cd output/inferences && ../../.venv/bin/python -m http.server 8002
# Then visit http://localhost:8002/
```

### Cache structure

```
output/
├── cache/api-football/    # raw API JSON, keyed by endpoint+params
├── team_sheets/           # generator output, keyed by reader__team__lens
├── editor/                # same
├── here_and_there/        # same
├── story_behind_number/   # same
├── back_story/            # same
├── where_played_before/   # same
├── from_the_stands/       # same
├── added_time/            # same
└── inferences/            # final rendered HTML
```

The `output/` directory is `.gitignore`d. The generator caches are safe to delete — they re-fill on next run. The API cache costs real money to refill (rate-limit awareness, not just wall time).

## Personality / style guidance

- The user is a software developer building this as a one-off creative project. Treat them as a peer.
- They are tired of generic AI-newsletter aesthetics and AI startup naming patterns. Their criterion is "would Nirvana in 1990 ship this?"
- They run a sibling project `~/claude-code-projects/deep-dugout/` (AI baseball simulation theater) — patterns from there inform some architecture choices (extract → summarize → prompt → generate; markdown prompt files; content API wrapper; checkpointed batch runner) but most domain logic does not port.
- They run an existing newsletter at `tucsondailybrief.com` (editorial-newsprint aesthetic). New projects must not visually overlap with it.
- Match their voice: confident, terse, willing to push back, willing to commit. Decision-density per sentence is high.
- Do not narrate internal deliberation. State decisions directly.
- When proposing aesthetic directions, lead with a *recommended* option, not a survey of options. They appreciate opinion.

## Memory index

Cross-session durable notes live at `.claude/projects/-home-nicholas-claude-code-projects-world-cup-project/memory/`. The index is `MEMORY.md`. Current entries:

- `model-choice-cost-stratify` — open-market model cost optimization
- `inference-matchday-nomenclature` — matchday vocabulary lock
- `avoid-tucson-daily-brief-aesthetic` — existing house style to not replicate
- `wc2026-data-landscape` — Jan 2026 data changes (Stats Perform exclusivity, FBref pullout)
- `inference-grunge-aesthetic-locked` — grunge visual identity locked
- `openai-only-stack-locked` — OpenAI sole LLM provider
- `api-football-only-stack-locked` — API-Football is the sole live data provider; Sportmonks is contingency-only
- `the-inference-name-locked` — the final project name
- `inference-phase2-ready` — Phase 2 spine built 2026-05-19, awaiting domain/hosting; do not rebuild

## Dev server (for iPhone preview)

```bash
cd web        # from the repo root
npm install   # one-time
npm run dev   # serves on port 3001, prints local + network URLs
```

Wi-Fi network URL pattern: `http://192.168.50.198:3001/` (subject to DHCP).
