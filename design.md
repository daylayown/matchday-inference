# THE INFERENCE — Visual Identity

**Locked: 2026-05-15.** Canonical reference: [`web/inference-sample-v3.html`](web/inference-sample-v3.html).

## Aesthetic

**Grunge / DIY fanzine.** Sub Pop / Nirvana 1990 / cut-and-paste zine culture. The publication should feel hand-stapled, photocopied-fifth-generation, raw-with-intent. NOT polished editorial-newsprint. NOT broadcast slick. NOT generic "AI newsletter."

The mood: *we are Nirvana in 1990, here to shake up the industry.*

## Type system

| Role | Font | Use |
|---|---|---|
| Display | **Anton** | Headlines, giant typographic posters, masthead, section names |
| Eccentric display | **Yeseva One** | Italics, contrast, pull quotes, lede paragraphs |
| Stencil display | **Allerta Stencil** | Stamps, section markers, page numbers, marquee strips |
| Body | **DM Sans** | Long-form prose, paragraph copy |
| Mono | **Space Mono** | Stats, dates, labels, technical chips |
| Handwriting | **Caveat** | Margin notes, scribbled annotations, editor corrections |

Mix freely. Different families inside the same headline is encouraged.

## Color palette

| Var | Hex | Use |
|---|---|---|
| `--paper` | `#F1E8D0` | Cream paper background |
| `--paper-deep` | `#E0D4B0` | Darker cream for section separation |
| `--paper-light` | `#F8F2E0` | Card backgrounds |
| `--ink` | `#0B0A0E` | Deep near-black for text and inverted sections |
| `--pink` | `#FF2E6E` | Hot riso pink — primary accent |
| `--pink-deep` | `#C71956` | Darker pink for prose accents |
| `--blue` | `#1E33C4` | Cobalt blue — secondary accent (riso pair) |
| `--blue-deep` | `#131F8E` | Darker cobalt |
| `--highlighter` | `#FFE94A` | Yellow highlighter strokes |
| `--highlighter-pink` | `#FFA8C8` | Pink highlighter strokes |

## The grunge grammar

The fifteen visual moves that define the look:

1. **Triple-layer riso offsets** on the biggest type — pink + blue + ink, deliberately misregistered like a fifth-gen photocopy.
2. **Heavy photocopy-grain noise overlay** — fixed full-screen SVG noise + dot patterns at multiple frequencies, multiply blend at ~0.85 opacity.
3. **Marker-pen SVG circles** around key numbers — visible ink wobble, hand-drawn feel.
4. **Highlighter strokes** behind selected phrases — yellow + pink, skewed and rotated slightly to feel hand-applied.
5. **Strikethroughs / editorial corrections** in prose — words crossed out with handwritten replacements in Caveat above the line.
6. **Handwritten margin notes** in Caveat at angles — small scribbles, side commentary.
7. **Stencil typography** for stamps and section markers.
8. **Stamps everywhere at hard angles** — DRAFT, ZINE / NOT PRESS, STAPLED, FROM THE BIN, VHS, UNEDITED. Dashed or solid 2–2.5px borders.
9. **Card rotations of ±1.5–2.5°**, varied per card. Bigger feels too wrong; smaller feels too polite.
10. **Tape strips** at chaotic angles (±5–9°), some with torn-edge clip-paths, in pink / blue / yellow / cream variants.
11. **Torn paper edges** between high-drama sections (clip-path with jagged polygon).
12. **Mixed-type headlines** — different families and sizes inside the same word.
13. **Hand-drawn arrows** (SVG) pointing at content from awkward angles. *Single-arc shape only — no S-curves that risk reading phallic.*
14. **Marquee scroll strips** in stencil — gig-flyer screamer energy.
15. **Hard shadows** (6–12px offset, solid color, no blur) — pink, blue, or ink — replacing all soft shadows.

## What to avoid

- Soft drop shadows with blur.
- Rounded corners (radius > 2px). Everything is cut, not extruded.
- Generic sans-serif body fonts (Inter, Roboto, system-ui).
- Photography of any real player/team (rights issues + breaks the photocopy aesthetic).
- Polished AI-illustrated imagery (introduces a visual consistency problem the typography already solves).
- Tidy alignment for its own sake. Intentional misalignment is the point.
- Editorial-newsprint cream + serif-display + monospace-labels combination — that's the existing tucsondailybrief.com house style; do not repeat it here.
- Generic stats-app slickness (broadcast graphics, scoreboard UI). The matchday programme metaphor refuses this.

## Reference files

- [`web/inference-sample-v3.html`](web/inference-sample-v3.html) — canonical full-issue reference
- [`web/index.html`](web/index.html) — landing page (still in the v2 polished-fanzine style as of lock-in; needs grunge update)
- [`web/inference-sample.html`](web/inference-sample.html) — v1 historical reference (stats-heavy, superseded)
- [`web/inference-sample-v2.html`](web/inference-sample-v2.html) — v2 historical reference (polished fanzine, superseded)
- [`nomenclature.md`](nomenclature.md) — locked naming conventions

## Related

- See [`MEMORY.md`](.claude/projects/-home-nicholas-claude-code-projects-world-cup-project/memory/MEMORY.md) for the project memory index.
