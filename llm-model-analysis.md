# LLM Model Analysis

**Created:** 2026-05-16  
**Purpose:** Capture the current model-selection rationale for THE INFERENCE so future coding sessions do not follow the older cost-first assumptions in `PLAN.md` and `model-price-research.md` without re-checking them.

## Recommendation

Use **`gpt-5.5` as the default creative-writing model** for THE INFERENCE.

This project is not expected to serve thousands of readers. It is primarily a high-taste creative artifact: a personalized World Cup zine that should feel surprising, specific, and worth showing people. For that goal, writing quality matters more than marginal token cost.

Recommended split:

| Use case | Model | Rationale |
|---|---|---|
| Creative prose, editorial voice, reader-facing narrative | `gpt-5.5` | Best default for quality-first prose and instruction-following. Use where taste matters. |
| Cheaper high-volume drafts or repetitive per-reader sections | `gpt-5.4-mini` | Good fallback if generation volume grows or a section proves templated enough. |
| Extraction, classification, ranking, normalization, validation | `gpt-5.4-nano` | Useful for plumbing tasks where prose quality is not the product. |

Avoid making `gpt-5.4-nano` or older `gpt-5-nano` the default for creative writing. Nano-class models are attractive on paper, but the project does not currently have enough scale to justify accepting flatter prose or more prompt babysitting.

## Why The Old Plan Should Change

Earlier planning optimized around a two-tier cost strategy:

- `gpt-5-nano` for high-volume per-reader generation.
- `gpt-5` or `gpt-5.1` for lower-volume premium/universal sections.
- Batch API and prompt caching as major design levers.

That made sense if the project might have thousands or tens of thousands of subscribers. Current intent is different: this is a finite, showcase-style World Cup project. At 10-50 readers, even premium-model usage is unlikely to be the binding constraint.

The binding constraint is whether the generated zine has a strong editorial voice.

## Practical Architecture

Keep the model layer simple:

- One primary content model: `gpt-5.5`.
- One optional utility model: `gpt-5.4-nano`.
- Optional mid-tier fallback: `gpt-5.4-mini` if cost/latency becomes visible.

Do not build elaborate cheap/premium routing until actual usage data proves it is needed. The first production implementation should favor clarity:

```text
content generation -> gpt-5.5
utility transforms -> gpt-5.4-nano
```

If cost becomes relevant later, the first optimization should be to move repetitive, lower-risk sections to `gpt-5.4-mini`, not to rewrite the whole pipeline.

## API Guidance

For new generation code, prefer the **Responses API** rather than adding more Chat Completions usage. The existing spike in `spike/spike.py` uses Chat Completions because it is a prototype; that should not set the pattern for the production `src/inference` package.

Suggested default settings for creative prose:

```json
{
  "model": "gpt-5.5",
  "reasoning": { "effort": "medium" },
  "text": { "verbosity": "medium" }
}
```

Use lower verbosity for compact blurbs. Do not increase reasoning effort unless evals show a measurable improvement. More reasoning is not automatically better for style.

## Prompting Notes

The current prompt direction is sound:

- Strong lens-specific voice rules.
- Explicit anti-patterns.
- Hard word caps.
- Factual discipline.
- JSON/structured output expectations.
- Reader wildcard used only when it genuinely lands.

For `gpt-5.5`, keep prompts outcome-first and avoid excessive procedural instruction. Preserve the product contract: voice, factual boundaries, output shape, and quality bar. Put stable style guidance in instructions and dynamic match/reader data in the input.

## Production Notes

Once the voice is working:

- Pin model snapshots for repeatability.
- Keep a small eval set for each lens: Cultural Critic, Pub-Talker, Tactician, Romantic, Historian.
- Evaluate on taste failures, not just schema validity.
- Track rough token cost, but do not let cost dominate model choice unless readership changes materially.

## Current Bottom Line

THE INFERENCE should optimize for "would someone remember this issue?" rather than "did this issue cost the least possible amount to generate?"

Default to `gpt-5.5` for prose. Use cheaper models only where they cannot damage the artifact.
