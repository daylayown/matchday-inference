# Model Price Research — World Cup Newsletter

> ⚠ **Historical / superseded for model selection.** As of 2026-05-16 the project's model strategy lives in [`llm-model-analysis.md`](llm-model-analysis.md): `gpt-5.5` default for all creative prose, `gpt-5.4-nano` for utility transforms, `gpt-5.4-mini` as optional mid-tier fallback. The cost-stratified cheap-tier / premium-tier framing below has been retired — at 10–50 readers the binding constraint is editorial voice, not token cost. This document is retained for the underlying price points and cost-modeling math, which remain accurate.

**Researched:** 2026-05-15
**Purpose:** Compare API costs across providers for the personalized World Cup newsletter. Two AI layers: a high-volume per-reader generation pass (cheap tier) and a low-volume universal section pass (premium tier).

---

## Quick-reference table — all models surveyed

All prices USD per million tokens. Standard tier unless noted.

| Model | Input | Cached input | Output | Context | Notes |
|---|---|---|---|---|---|
| **Anthropic** | | | | | |
| Claude Sonnet 4.6 | $3.00 | $0.30 | $15.00 | 1M | Cache write $3.75 (5min) / $6.00 (1hr) |
| Claude Haiku 4.5 | $1.00 | $0.10 | $5.00 | 200k | Cache write $1.25 / $2.00 |
| **OpenAI (gpt-5.4 family)** | | | | | |
| gpt-5.4 | $2.50 | $0.25 | $15.00 | 272k | Newest mid-tier |
| gpt-5.4-mini | $0.75 | $0.075 | $4.50 | — | |
| gpt-5.4-nano | $0.20 | $0.02 | $1.25 | — | |
| **OpenAI (gpt-5 family, older)** | | | | | |
| gpt-5 / gpt-5.1 | $1.25 | $0.125 | $10.00 | — | |
| gpt-5-mini | $0.25 | $0.025 | $2.00 | — | |
| gpt-5-nano | $0.05 | $0.005 | $0.40 | — | Cost-optimal in OpenAI lineup |
| **xAI** | | | | | |
| Grok 4.3 | $1.25 | n/a | $2.50 | 1M | Flat rate |
| Grok 4.1 fast (non-reasoning) | $0.20 | n/a | $0.50 | 2M | Closest mini-tier; deprecation pending — verify before launch |
| **DeepSeek** | | | | | |
| DeepSeek V4 Flash | $0.14 | $0.0028 | $0.28 | 1M | Cache hit effectively free |
| DeepSeek V4 Pro (promo) | $0.435 | $0.0036 | $0.87 | 1M | 75% off through 2026-05-31; list is $1.74 / $3.48 |

All models verified to exist with these exact names as of 2026-05-15.

---

## Shortlist — cheap tier (per-reader layer)

Per-reader job: take a reader profile + yesterday's stat lines for their teams/players, output a few stat-grounded blurbs and contextual comparisons. ~2k input + 500 output tokens per email.

| Candidate | Input | Output | Notes |
|---|---|---|---|
| **gpt-5-nano** | $0.05 | $0.40 | Cheapest OpenAI option; 3–4x cheaper than gpt-5.4-nano |
| **DeepSeek V4 Flash** | $0.14 | $0.28 | Cheapest output rate of any candidate; cache-hit effectively free |
| **Grok 4.1 fast** | $0.20 | $0.50 | Simpler if staying single-vendor with xAI; no listed cache rate |

**Squeezed out:** gpt-5.4-mini, gpt-5.4-nano, Claude Haiku 4.5, Grok 4.3, gpt-5-mini. Not cheap enough to be the cheap option, not premium enough to be the quality option.

## Shortlist — premium tier (universal AI sections)

For the Ratings Ladder + Anomalies. ~100 calls per matchday total. Reader-visible prose quality matters; volume is trivial.

| Candidate | Input | Output | Notes |
|---|---|---|---|
| **Sonnet 4.6** | $3.00 | $15.00 | Anthropic flagship mid-tier |
| **gpt-5 / gpt-5.1** | $1.25 | $10.00 | Half the price of Sonnet 4.6 / gpt-5.4 for similar positioning |
| **gpt-5.4** | $2.50 | $15.00 | Newest OpenAI mid-tier; basically Sonnet pricing |

Total event cost for the premium layer is single-digit to low-double-digit dollars regardless of choice. Pick on quality, not cost.

---

## Cost projections (per-reader layer only)

Assuming 2k input + 500 output tokens per email × 35 days × N subscribers.

**Without caching, standard tier:**

| Candidate | 5k subs | 50k subs |
|---|---|---|
| gpt-5-nano | ~$53 | ~$525 |
| DeepSeek V4 Flash | ~$74 | ~$735 |
| Grok 4.1 fast | ~$114 | ~$1,140 |
| gpt-5.4-nano | ~$179 | ~$1,790 |
| Haiku 4.5 | ~$790 | ~$7,900 |
| Sonnet 4.6 | ~$2,360 | ~$23,600 |

**With ~75% of input tokens cached (static scaffolding) + batch API 50% off where available:**

| Candidate | 5k subs | 50k subs |
|---|---|---|
| gpt-5-nano (batch + cache) | ~$20 | ~$200 |
| DeepSeek V4 Flash (cache) | ~$38 | ~$380 |
| Grok 4.1 fast (no cache info) | ~$57 (batch n/a) | ~$570 |

At 5k subscribers the per-reader bill is essentially noise (<$50/month). Cost is no longer the binding constraint — quality and operational simplicity are.

---

## Cost levers worth designing around from day one

1. **Prompt caching.** The static prompt scaffolding (system message, reader profile schema, few-shot examples) is identical every day. Structuring the prompt to put dynamic content (yesterday's stats) at the end maximizes cache reuse. Effective savings: ~90% on the cacheable portion of input cost across all caching-capable providers.

2. **Batch API.** The newsletter ships at a fixed daily time, so the per-reader content can be generated the prior evening and submitted as a batch — turnaround is comfortably under the 24-hour limit, and most providers offer a flat 50% discount on batch. Works equally well for the universal AI sections.

3. **Single-vendor vs. multi-vendor.** Two SDKs is real overhead for a 5-week one-off. The candidates that allow a single-vendor stack across both layers: OpenAI (nano + gpt-5), or xAI (Grok 4.1 fast + Grok 4.3). DeepSeek alone could plausibly cover both layers as well — V4 Flash for cheap, V4 Pro for premium (post-promo $1.74/$3.48 — note the price change after 2026-05-31).

---

## Open questions / caveats

- **DeepSeek V4 Pro promo expires 2026-05-31.** WC runs June 11 – July 19. List-price Pro would apply for the entire event. Not material if using Flash instead.
- **Grok deprecations effective 2026-05-15.** Old `grok-4-1-fast`, `grok-4-fast`, `grok-4` IDs retire today and redirect to Grok 4.3 pricing — make sure to use the current `grok-4-1-fast-non-reasoning` ID if testing that tier.
- **Quality variance on cheap models for "find the one interesting comparison" tasks.** This is harder than it sounds for small models; they tend to drift into florid prose. Head-to-head pilot on real stat lines is the only honest way to choose.
- **Regional residency surcharge.** OpenAI charges a 10% uplift for `us`-pinned inference on gpt-5.4/5.5 family. Anthropic similarly applies a 1.1x multiplier with `inference_geo: "us"`. Not relevant unless we care about data residency.

---

## Recommended next step

Run a 3-way pilot on the cheap tier — gpt-5-nano vs. DeepSeek V4 Flash vs. Grok 4.1 fast — using a real per-reader prompt against one historical match's stat lines for 5 imagined reader profiles. Decide on quality, not cost. Then a 2-way pilot on the premium tier — Sonnet 4.6 vs. gpt-5 — using a real Ratings Ladder + Anomalies prompt against one historical matchday.

---

## Sources

- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing
- OpenAI: live pricing page (verified by user 2026-05-15)
- DeepSeek: https://api-docs.deepseek.com/quick_start/pricing
- xAI: https://docs.x.ai/docs/models
