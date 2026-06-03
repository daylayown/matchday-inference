# Project Kickoff: World Cup 2026 Stats Newsletter

## What we're building

A retroactive, stats-only daily email newsletter for the 2026 FIFA World Cup (June 11 – July 19, 2026). Aesthetic + philosophy modeled on boxscore.email/mlb — dense tables, no takes, no narrative, "morning cup of coffee" feel. One-off special event, ~5-week run.

## Design philosophy (load-bearing)

- **No takes. No discourse.** No game recaps, no predictions, no opinion writing.
- **Tables over prose.** If a thing can be expressed as a column, it should be.
- **Dense, monospace-feeling.** Reference: boxscore.email/mlb. The email should read like a stats page torn out of a print sports section.
- **Backwards-looking only.** What happened yesterday + cumulative tournament state. Never previews.
- **Unembellished.** No emoji, no decorative graphics, no copy that tries to sell you on the action. The numbers do the work.

This is a deliberate counter-positioning to highlight/recap-style soccer content (The Athletic, ESPN, NYT Athletic). The brief is load-bearing — do not drift toward narrative under pressure.

## Content structure

### Group stage edition (June 11 – July 1)

```
[DATE HEADER] — MATCHDAY N

YESTERDAY'S RESULTS
[One-line scores: TEAM A  2 — 1  TEAM B]

GROUP STANDINGS
[12 group tables: P W D L GF GA GD Pts]

TOURNAMENT LEADERS
Top Scorers  |  Assists  |  Clean Sheets  |  Pass %  |  ...
[Top 5 each]

AI RATINGS LADDER — [DATE]
[Top 11 performers, 6.0–10.0 ratings, derived from stat lines]

ANOMALIES
[3–5 statistically odd things from yesterday, one-line bullets]
```

### Knockout edition (July 4 – July 19)

Replace Group Standings with current bracket. Keep everything else.

### Pre-launch issue (week of June 8)

Tournament preview: group breakdowns, key players to watch (data-driven — qualifying campaign leaders in goals/xG), bracket schedule. No predictions.

## Data sources (start free)

Ordered by preference:

1. **API-Football** (api-sports.io) — free tier ~100 req/day, REST API, should cover the WC. Verify coverage of the 2026 tournament before committing.
2. **FBref** (StatsBomb-powered) via the `soccerdata` Python package — for advanced stats (xG, xA, progressive passes). Free, rate-limited, cache aggressively per-day per-match.
3. **football-data.org** — free fallback, covers WC, less granular.
4. **Wikipedia wikitables** — last-resort fallback for group standings.

**Step 1 of the project is a data spike**: pick one source, verify it covers the 2026 World Cup, and pull one historical match's full stat line to validate completeness. If your primary doesn't cover the WC or has incomplete data, pivot before doing anything else.

## The "thin AI layer"

Two components, both stats-shaped (not prose):

### AI Ratings Ladder
- **Input**: Each player's stat line from yesterday's matches (minutes, goals, assists, shots, passes, pass %, tackles, interceptions, dribbles, dispossessed, fouls, etc.)
- **Output**: 6.0–10.0 rating per player; render top 11 overall
- **Implementation**: One Claude API call per matchday, batched (all matches in one prompt). Ask for JSON output, render as a table.
- **Cost**: ~$1.50 over the full event.

### Anomalies
- **Input**: Same stat lines + group context
- **Output**: 3–5 short bullets pointing at statistically unusual events ("Italy: 0 shots on target", "Mbappé subbed off in the 18th", "Brazil completed 92% of passes in the opposition half")
- **Implementation**: Same daily Claude call, separate prompt section.

**Do not add other AI features.** Specifically avoid: per-match recap paragraphs, predictions for today, player profile blurbs, "manager talking points." Those reintroduce takes and break the format.

## Technical stack

- **Language**: Python
- **Data fetcher**: Daily script — pulls yesterday's matches, computes leader tables + group standings
- **Storage**: Local SQLite or JSON files. 5-week event, no need for Postgres
- **AI layer**: `anthropic` SDK, default Claude Sonnet (Haiku if cost is an issue; Sonnet quality probably worth the few dollars)
- **Email rendering**: HTML template, hand-rolled or MJML. Plain-text fallback
- **Email delivery**: Resend, Buttondown, or Beehiiv. Pick one early — shapes the subscriber-management UX
- **Scheduler**: GitHub Actions cron OR Cloudflare Workers Cron Triggers. GH Actions is simpler; Workers gives you a real serverless deployment
- **Domain**: Standalone (e.g., matchday.email, finalwhistle.news) likely better than a subdomain

## Timeline

- **May 15 – May 22**: Data spike. Pick a source, validate WC coverage, prove end-to-end pull on a historical match. Draft the email HTML template.
- **May 23 – June 1**: Build the daily pipeline. Group standings computation, leader tables, AI ratings call. End-to-end test on historical matches.
- **June 2 – June 8**: Soft-launch with a pre-tournament preview issue. Build subscriber list. Set up email delivery.
- **June 11**: First live edition (Opening match).
- **July 19**: Final edition (Cup Final).
- **Post-event**: Decide if this becomes a recurring product (Euros, Copa, next WC) or stays a one-off.

## Open decisions to make early

1. **Name + domain.** Candidates: "Group Stage", "Stoppage Time", "The Tactic Sheet", "Final Whistle", "Box-to-Box", "Matchday", "90+5".
2. **Branding relationship to sibling project Deep Dugout** (`~/claude-code-projects/deep-dugout/`). Recommendation: standalone product, Deep Dugout in the footer.
3. **Email delivery platform.** Resend (developer-first), Buttondown (simple, indie-friendly), Beehiiv (most growth features).
4. **Free vs paid?** Recommendation: free during the WC, decide post-event.

## Out of scope (resist scope creep)

- Live in-match updates
- Per-team newsletters
- Discord / social integration
- Audio version
- Web archive (maybe later; the email IS the product for now)
- Predictions of any kind
- Editorial or commentary writing

Reference project: `~/claude-code-projects/deep-dugout/CLAUDE.md` — same author, similar aesthetic philosophy, but Deep Dugout is AI-driven simulation theater while this is a pure data digest. **Do not import** the simulation engine, personality system, or AI manager from Deep Dugout — they don't belong here.

## First action

Run a data spike on API-Football: verify the 2026 World Cup is covered, pull one historical match's full stat line, and confirm the data shape supports the email structure above. Do not write any email-rendering code until the data layer is proven.
