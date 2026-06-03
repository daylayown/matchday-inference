"""OpenAI Responses API wrapper for THE INFERENCE.

Two presets, locked per `openai-only-stack-locked` memory:

    content  → gpt-5.5,     reasoning effort medium, verbosity medium
    utility  → gpt-5.4-nano

Use `content` for any reader-facing prose. Use `utility` for plumbing —
extraction, classification, normalization — where prose quality isn't the
product. There is no cheap/premium routing, no Batch wiring, no retry layer
yet; add them when something demonstrates the need.

Per llm-model-analysis.md: put stable style guidance in `instructions`, put
dynamic match/reader data in `input`.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Literal

from openai import OpenAI

Preset = Literal["content", "utility"]

PRESETS: dict[str, dict[str, Any]] = {
    "content": {
        "model": "gpt-5.5",
        "reasoning": {"effort": "medium"},
        "text": {"verbosity": "medium"},
    },
    "utility": {
        "model": "gpt-5.4-nano",
    },
}

# Per-1M-token prices (USD). gpt-5.4 family from model-price-research.md;
# gpt-5.5 not yet published — using gpt-5.4 numbers as a placeholder, matching
# spike/spike.py. Update when OpenAI documents 5.5 pricing.
PRICES: dict[str, tuple[float, float]] = {
    # model:           (input,  output)
    "gpt-5.5":         (2.50,   15.00),   # placeholder, see note above
    "gpt-5.4":         (2.50,   15.00),
    "gpt-5.4-mini":    (0.75,    4.50),
    "gpt-5.4-nano":    (0.20,    1.25),
    "gpt-5":           (1.25,   10.00),
    "gpt-5.1":         (1.25,   10.00),
}


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int | None
    cost_usd: float | None
    elapsed_seconds: float
    raw: Any  # the SDK response object — keep for debugging

    def __str__(self) -> str:
        cost = f"${self.cost_usd:.4f}" if self.cost_usd is not None else "$?.??"
        rt = f" reasoning={self.reasoning_tokens}" if self.reasoning_tokens else ""
        return (
            f"<{self.model} "
            f"in={self.input_tokens} out={self.output_tokens}{rt} "
            f"{cost} {self.elapsed_seconds:.1f}s>"
        )


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Rough cost in USD. Returns None for unknown models. Ignores cache discount.

    Matches by longest prefix so pinned snapshots like `gpt-5.5-2026-04-23`
    resolve to `gpt-5.5`, and `gpt-5.4-nano-2026-03-17` resolves to
    `gpt-5.4-nano` (not `gpt-5.4`).
    """
    for key in sorted(PRICES.keys(), key=len, reverse=True):
        if model.startswith(key):
            in_price, out_price = PRICES[key]
            return (input_tokens * in_price + output_tokens * out_price) / 1_000_000
    return None


class ContentClient:
    """Thin wrapper over OpenAI Responses API. Stateless apart from the SDK client."""

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in env")
        self.client = OpenAI(api_key=key)

    def generate(
        self,
        instructions: str,
        input: str | list,
        preset: Preset = "content",
        json_mode: bool = False,
        **overrides: Any,
    ) -> GenerationResult:
        """Call the Responses API and return a GenerationResult.

        `instructions` is the system prompt (voice, boundaries, output shape).
        `input` is the dynamic per-call payload (match data, reader profile, etc.).
        `overrides` are merged into the preset config — e.g. text={"verbosity": "low"}.
        """
        config = _merge(PRESETS[preset], overrides)
        if json_mode:
            text_cfg = dict(config.get("text") or {})
            text_cfg["format"] = {"type": "json_object"}
            config["text"] = text_cfg

        t0 = time.monotonic()
        response = self.client.responses.create(
            instructions=instructions,
            input=input,
            **config,
        )
        elapsed = time.monotonic() - t0

        usage = response.usage
        reasoning_tokens = None
        details = getattr(usage, "output_tokens_details", None)
        if details is not None:
            reasoning_tokens = getattr(details, "reasoning_tokens", None)

        return GenerationResult(
            text=response.output_text,
            model=response.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=reasoning_tokens,
            cost_usd=_estimate_cost(response.model, usage.input_tokens, usage.output_tokens),
            elapsed_seconds=elapsed,
            raw=response,
        )


def _merge(base: dict, overrides: dict) -> dict:
    """Shallow merge with one level of dict-aware nesting (for text/reasoning sub-dicts)."""
    out = dict(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out
