# API Research — World Cup Data Providers

**Date:** 2026-05-18  
**Project:** THE INFERENCE — personalized AI matchday fanzine for the 2026 FIFA World Cup  
**Decision:** Build v1 around **API-Football only**, with a small manual patch/override layer. Add another provider only if the data spike proves API-Football cannot cover an essential field.

---

## Context

THE INFERENCE is a one-and-done, casual, personalized World Cup fanzine. It is not a stats-heavy analytics product, betting product, live match center, fantasy game, or scouting tool.

The product value is:

- reader-specific editorial voice and lens
- daily matchday programme/fanzine feel
- match context, scorers, lineups, standings, key moments, tournament arc
- history/heritage features and human texture
- strong typography/design, not advanced analytics

Because this is a 5-week one-off with a small expected audience, the data strategy should optimize for simplicity and shippability, not maximum provider redundancy.

---

## Final Recommendation

Use:

1. **API-Football Pro** as the primary and only planned live data provider.
2. **Local JSON patch files** for manual corrections, missing context, naming tweaks, and one-off editorial facts.
3. **SportMonks only as a contingency**, if the data spike finds API-Football lacks an essential field.

Do **not** build the first version around multiple providers.

The previous API-Football + SportMonks plan was defensible, but after re-checking the product shape, it is probably overbuilt. Normalizing two providers introduces more complexity than this project needs.

---

## Why API-Football Is Enough

API-Football publicly documents World Cup 2026 support through `league=1`, `season=2026`, including:

- fixtures and live scores
- events
- lineups
- match statistics
- player statistics
- standings
- top scorers and assists
- injuries/suspensions
- coaches
- head-to-head records
- predictions and odds, if wanted

Source: [API-Football World Cup 2026 guide](https://www.api-football.com/news/post/fifa-world-cup-2026-guide-to-using-data-with-api-sports)

For THE INFERENCE, the required data is:

- fixtures
- results
- scorers
- match events
- lineups
- substitutions
- cards
- team match stats
- player match stats
- standings
- squads/player profiles
- venues

That is the data surface the fanzine needs. Advanced data such as xG, pressure index, shot maps, live tracking, pass networks, and player-location data are nice-to-have at most.

---

## Required Spike Before Committing

Before implementation, run a data spike against:

1. **One historical World Cup match** with known rich data, such as Argentina vs France, 2022 final.
2. **The 2026 World Cup competition metadata**, using `league=1`, `season=2026`.
3. **One current/live-style fixture response**, if available during testing.

Validate that API-Football returns:

- complete fixture metadata
- score and status
- event timeline
- scorers and assists if available
- lineups and substitutions
- cards
- team match stats
- player match stats
- standings
- stable team/player IDs
- usable venue fields
- response timing/update cadence

If those pass, proceed with API-Football only.

If API-Football fails on a truly essential field, then evaluate SportMonks or Statorium as a second source.

---

## Manual Patch Layer

A manual patch layer is more valuable than a second provider for this project.

Example uses:

- fix odd team/player display names
- add missing accent marks or preferred names
- correct a venue label
- add a hand-curated narrative thread
- mark a key moment that APIs do not capture well
- patch a missing lineup or substitution
- add reader-relevant heritage facts

Recommended shape:

```text
data/patches/
  2026-06-11.json
  2026-06-12.json
  ...
```

The pipeline should load API data first, then apply local patches before generation.

This is cheaper and safer than normalizing two providers for a small one-off.

---

## xG Decision

**xG is not required.**

xG means "expected goals." It estimates the probability that each shot becomes a goal, then sums those probabilities. For example, a team with `1.8 xG` created chances that a model thinks were worth about 1.8 goals.

It is useful for analysis like:

> They lost 1-0, but created the better chances.

For this project, xG is optional color, not infrastructure. THE INFERENCE is a casual fanzine, not a stat-nerd product. If xG is available cleanly, it can appear occasionally as a supporting line. It should not drive provider choice or delay the build.

Use xG only if it falls out of the chosen data source cleanly. Do not build around it.

---

## xG Provider Notes

| Provider | xG Support | Notes |
|---|---:|---|
| SportMonks | Yes | Dedicated Expected/xG endpoints. Availability depends on package: delayed, post-match, or real-time. Source: [SportMonks xG endpoint](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/expected-xg/get-expected-by-player) |
| BALLDONTLIE FIFA API | Yes | Shot-map endpoint includes `xg` and `xgot`, populated for 2022 and 2026 matches. Source: [BALLDONTLIE FIFA API](https://fifa.balldontlie.io/) |
| Goalserve | Yes | Soccer live stats package lists `ExG - Expected Goals`. Source: [Goalserve soccer stats](https://www.goalserve.com/fr/sport-data-feeds/soccer-api/description) |
| Stats Perform / Opta | Yes | Enterprise-grade xG, available pre-game, in-play, and post-game. Source: [Stats Perform xG](https://www.statsperform.com/resource/expected-goals-in-sports-betting/) |
| StatsBomb / Hudl | Yes | Strong event-data and xG provider generally, but not the obvious live World Cup feed unless contracted. Source: [Hudl StatsBomb](https://www.hudl.com/en_gb/products/statsbomb) |
| TheStatsAPI | Yes | Claims match-level xG, player xG/xA, and per-shot xG. Verify World Cup coverage before relying on it. Source: [TheStatsAPI](https://www.thestatsapi.com/) |
| API-Football | Maybe / inconsistent | Public World Cup guide lists match/player stats but not xG. Do not rely on API-Football for xG unless the data spike proves it. |
| Statorium | Not advertised | WC page lists common match stats, lineups, substitutes, player events, but not xG. Source: [Statorium WC API](https://statorium.com/fifa-world-cup-2026-api) |
| Sportradar | Unclear publicly | Soccer Extended has 100+ stats and XY events, but xG was not explicit in the public docs checked. Source: [Sportradar Soccer API](https://developer.sportradar.com/soccer/docs/soccer-ig-api-basics) |

---

## Provider Landscape

### API-Football

**Recommended primary provider.**

API-Football has the practical World Cup surface this project needs: fixtures, scores, events, lineups, standings, player stats, team stats, squads/player profiles, coaches, predictions, and odds.

Pros:

- inexpensive relative to enterprise providers
- straightforward REST API
- clear World Cup 2026 guide
- enough data for a prose-first fanzine
- avoids multi-provider normalization

Risks:

- xG not guaranteed
- occasional missing/null fields likely
- must verify historical WC match depth and 2026 coverage with a spike

Decision: **Use it.**

Source: [API-Football World Cup 2026 guide](https://www.api-football.com/news/post/fifa-world-cup-2026-guide-to-using-data-with-api-sports)

### SportMonks

Previously part of the planned stack. Still a credible fallback if API-Football fails the spike.

Pros:

- strong football API
- World Cup package
- xG available through Expected endpoints
- predictions and pressure-style metrics available in some packages

Cons:

- second provider increases normalization work
- likely unnecessary for this product's casual scope
- xG is not a core requirement

Decision: **Do not include by default. Keep as contingency.**

Sources:

- [SportMonks World Cup API](https://www.sportmonks.com/football-api/world-cup-api/)
- [SportMonks xG endpoint](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/expected-xg/get-expected-by-player)

### Statorium

Interesting low-cost World Cup-specific alternative.

Public page advertises:

- standings
- fixtures
- results
- teams
- players
- venues
- player events
- match events
- match stats
- lineups
- substitutes
- optional news package

Public World Cup pricing shown:

- Basic Data: `$177`
- Premium Data: `$499`
- World Cup News: `$250`

Pros:

- flat World Cup pricing
- explicit tournament focus
- manual/semi-manual live supervision
- optional editorial/news package

Cons:

- xG not advertised
- less proven than API-Football/SportMonks
- would require extra integration work

Decision: **Good fallback candidate, not primary.**

Source: [Statorium World Cup 2026 API](https://statorium.com/fifa-world-cup-2026-api)

### BALLDONTLIE FIFA World Cup API

Tournament-specific developer API claiming coverage for 2018, 2022, and 2026 World Cups.

Advertised data includes:

- teams
- stadiums
- players
- rosters
- matches
- standings
- lineups
- events
- player/team stats
- shot maps
- attack momentum
- betting odds
- shot-level `xg` and `xgot`

Pros:

- very attractive for quick prototyping
- World Cup-specific
- has shot maps and xG/xGOT

Risks:

- provenance and commercial rights need diligence
- SLA/reliability unknown
- should not become the production dependency without testing

Decision: **Prototype/comparison source only.**

Source: [BALLDONTLIE FIFA API](https://fifa.balldontlie.io/)

### football-data.org

Useful low-cost fallback for basic competition data.

Pros:

- developer-friendly
- cheap/free tiers
- useful for fixtures, results, standings

Cons:

- likely too thin for rich fanzine generation
- not enough live events/player detail for the core product

Decision: **Emergency schedule/results fallback only.**

Source: [football-data.org docs](https://www.football-data.org/docs/v2/index.html)

### Goalserve

Older-style sports feed provider with JSON/XML feeds.

Pros:

- live scores, historical data, prematch/in-play data
- soccer live stats package lists lineups, formations, heatmaps, ExG/xG, player action stats, VAR checks
- free trial advertised

Cons:

- older feed style
- package/coverage details need verification
- likely more integration work than API-Football

Decision: **Possible fallback, not primary.**

Source: [Goalserve soccer stats](https://www.goalserve.com/fr/sport-data-feeds/soccer-api/description)

### iSports API

Mid-market live data option.

Advertised capabilities include football schedules, results, events, lineups, stats, live text, and cup stages across many leagues/cups.

Pros:

- broad football coverage
- lineups and live text available
- may cover international competitions

Cons:

- quality and ID stability unknown
- public material is less compelling for this exact project than API-Football

Decision: **Do not prioritize.**

Source: [iSports football API](https://www.isportsapi.com/products/detail/football-api-product-184.html?lang=en)

### TheStatsAPI

Developer-focused football stats API.

Claims:

- match schedules/results
- match statistics/events
- player statistics
- expected goals, npxG, xA, shot maps

Pros:

- xG-forward
- modern developer positioning

Cons:

- World Cup 2026 coverage needs verification
- not necessary if API-Football covers essentials

Decision: **Potential xG comparator only.**

Source: [TheStatsAPI](https://www.thestatsapi.com/)

### Sportradar

Enterprise sports data provider.

Public soccer docs describe:

- RESTful B2B soccer API
- FIFA World Cup as a competition example
- Soccer Extended with 100+ unique data points
- XY coordinates for events
- match stats by period
- AI-driven commentary/previews/summaries
- tiered coverage matrix

Pros:

- reliable enterprise option
- strong docs
- rich live-data infrastructure

Cons:

- likely sales-led/enterprise pricing
- overkill for a one-off casual fanzine
- xG not clearly visible in the public page checked

Decision: **Do not pursue for v1.**

Source: [Sportradar Soccer API basics](https://developer.sportradar.com/soccer/docs/soccer-ig-api-basics)

### Stats Perform / Opta

Premium football data provider.

Public materials confirm:

- Opta data feeds include live scores, standings, Expected Goals, and predictions
- xG available pre-game, post-game, and in-play
- FIFA selected Stats Perform as official worldwide betting data and betting streaming rights distributor for selected FIFA properties, including World Cup 2026

Pros:

- best-in-class football data
- strong xG and advanced analytics
- likely excellent reliability

Cons:

- enterprise contracts
- probably expensive
- betting-data rights do not automatically solve media/product rights
- overkill for this project

Decision: **Do not pursue unless this becomes a real business.**

Sources:

- [Stats Perform Opta data](https://www.statsperform.com/opta/)
- [Stats Perform xG](https://www.statsperform.com/resource/expected-goals-in-sports-betting/)
- [FIFA Stats Perform announcement](https://inside.fifa.com/tournament-organisation/commercial/media-releases/stats-perform-official-worldwide-betting-data-streaming-rights-distributor-world-cup)

### Data Sports Group

Enterprise media/fan-engagement provider.

Public materials advertise:

- FIFA World Cup 2026 package
- dynamic match stats
- player bios
- historical records
- JSON/XML feeds
- automated graphics and publisher-oriented tooling

Pros:

- relevant to fan-facing media products
- potential editorial/media bundle

Cons:

- contact-sales
- likely overkill
- rights/licensing need careful review

Decision: **Do not pursue for this one-off.**

Sources:

- [Data Sports Group](https://datasportsgroup.com/)
- [DSG FIFA World Cup data](https://datasportsgroup.com/fifa-world-cup-data/)

### Gracenote

Enterprise sports metadata provider with strong media/TV DNA.

Pros:

- likely strong schedules, standings, scores, imagery, metadata, historical context
- useful for polished consumer media products

Cons:

- opaque public docs/pricing
- enterprise sales motion
- not needed for the fanzine

Decision: **Do not pursue.**

Source: [Gracenote Sports Data](https://gracenote.com/products/sports-data/)

### Genius Sports

Enterprise official-data/betting-adjacent provider.

Pros:

- official-rights posture may matter for larger products
- near-real-time event API offerings

Cons:

- World Cup soccer coverage not confirmed from public materials
- likely enterprise
- not aligned with small one-off scope

Decision: **Do not pursue.**

Source: [Genius Sports official data API](https://www.geniussports.com/engage/official-sports-data-api/)

### Hudl StatsBomb / Wyscout

Strong scouting and event-data ecosystem.

StatsBomb public materials describe:

- 3,400+ events per match
- 190+ competitions
- player-location data for many key leagues
- strong analysis/scouting workflows

Pros:

- excellent tactical/event data
- strong xG context
- useful for post-tournament archive analysis

Cons:

- not the obvious live World Cup operations feed
- likely sales-led
- overkill for a casual fanzine

Decision: **Not part of v1. Consider only for post-tournament archive features.**

Source: [Hudl StatsBomb](https://www.hudl.com/en_gb/products/statsbomb)

### ScoreBat

Football video/highlights API.

Pros:

- official embeddable videos from verified sources
- free and paid feeds
- useful for a web archive or match pages

Cons:

- not a stats provider
- paid/free coverage varies
- email embeds are a poor fit

Decision: **Ignore for the email-first version.**

Source: [ScoreBat Video API docs](https://www.scorebat.com/video-api/docs/)

---

## Rights And Media Cautions

Do not assume provider images are reusable.

For this project, the safest choice remains the existing visual direction: typography, generated layout, photocopy/fanzine texture, and no real player photography.

If using logos, player headshots, venue images, video, or official World Cup marks, verify:

- redistribution rights
- email usage rights
- commercial/sponsorship rights
- generated-text rights
- attribution requirements
- caching limits
- whether data can be stored permanently
- whether images are editorial-only
- whether betting-data restrictions apply

FIFA selected Stats Perform for official betting data/streaming distribution for certain FIFA competitions, including World Cup 2026, but that does not automatically grant small media/product rights to downstream builders.

Source: [FIFA Stats Perform announcement](https://inside.fifa.com/tournament-organisation/commercial/media-releases/stats-perform-official-worldwide-betting-data-streaming-rights-distributor-world-cup)

---

## Implementation Implication

Revise the data section of `PLAN.md` from:

```text
API-Football Pro + SportMonks WC All-In
```

to:

```text
API-Football Pro primary source.
Local JSON patches for corrections and editorial context.
SportMonks/Statorium only if the Phase 0 data spike exposes an essential API-Football gap.
```

The data spike should answer one question:

> Can API-Football alone provide enough structured truth for a daily casual fanzine?

If yes, stop shopping and build.

