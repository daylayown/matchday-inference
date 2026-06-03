"""Dispatch rendered issues to subscribers via Resend.

Bridges the orchestrator (which renders + writes HTML/text to disk) and the
email layer (`send_issue`). For each ReaderResult it looks up the reader's
address in the subscriber store, reads the rendered files back off disk, and
sends. Pure glue — no rendering, no DB writes.

Kept deliberately decoupled from `orchestrate.daily`: it duck-types the result
objects (needs only `.reader_slug`, `.error`, `.html_path`, `.txt_path`) so it
can be unit-tested without spinning up the whole pipeline, and so importing it
never drags in the generators/API client.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Iterable

from ..subscribers.store import DEFAULT_DB_PATH, SubscriberStore
from .email import SendResult, issue_subject, send_issue
from .publish import publish_issue
from .render import render_teaser_email, render_teaser_text


@dataclass
class DispatchOutcome:
    reader_slug: str
    sent: bool
    skipped_reason: str | None = None
    send_result: SendResult | None = None

    def __str__(self) -> str:
        if self.sent:
            mid = self.send_result.message_id if self.send_result else None
            return f"  sent     {self.reader_slug}  id={mid}"
        return f"  skipped  {self.reader_slug}  ({self.skipped_reason})"


def human_date(date_iso: str) -> str:
    """'2026-06-11' → 'Thursday 11 June 2026' (no zero-pad, platform-independent)."""
    d = date.fromisoformat(date_iso)
    return f"{d:%A} {d.day} {d:%B %Y}"


def _compact_date(date_iso: str) -> str:
    """'2026-06-11' → '11.06.26'."""
    d = date.fromisoformat(date_iso)
    return f"{d.day:02d}.{d.month:02d}.{str(d.year)[-2:]}"


def _first_name(name: str | None) -> str | None:
    return name.split()[0] if name else None


def _reader_summary(reader: Any) -> str | None:
    """e.g. 'Mexico · The Diaspora lens' for the teaser footer line."""
    if reader is None:
        return None
    teams = getattr(reader, "teams", None) or []
    lens = getattr(reader, "lens", None)
    parts: list[str] = []
    if teams:
        parts.append(", ".join(teams))
    if lens:
        parts.append(f"{lens} lens")
    return " · ".join(parts) or None


def send_results(
    results: Iterable[Any],
    readers: Iterable[Any],
    *,
    date_iso: str,
    issue_number: str,
    store: SubscriberStore | None = None,
    send_fn: Callable[..., SendResult] = send_issue,
    publish_fn: Callable[..., str] = publish_issue,
) -> list[DispatchOutcome]:
    """Publish each issue to the web and email a teaser linking to it.

    Email clients strip the grunge aesthetic, so we don't send the issue HTML —
    we `publish_fn` the full issue to R2 (returning its public URL), then send a
    small email-safe teaser whose button opens that URL. `results` are
    ReaderResult-like; `readers` are ReaderProfile-like. Emails come from the
    subscriber store, keyed by slug — no email on file → skipped, not failed.

    `send_fn`, `publish_fn`, and `store` are injectable so tests don't hit
    Resend, wrangler, or the real DB.
    """
    by_slug = {getattr(r, "slug", None): r for r in readers}

    owns_store = store is None
    if owns_store:
        store = SubscriberStore() if DEFAULT_DB_PATH.exists() else None

    subject_date = human_date(date_iso)
    date_compact = _compact_date(date_iso)
    year = date_iso[:4]
    outcomes: list[DispatchOutcome] = []
    try:
        for res in results:
            slug = res.reader_slug
            if res.error or not res.html_path:
                outcomes.append(DispatchOutcome(slug, False, "render failed"))
                continue

            email = store.get_email(slug) if store is not None else None
            if not email:
                outcomes.append(DispatchOutcome(slug, False, "no email on file"))
                continue

            # Publish the full grunge issue to the web; the email only links to it.
            try:
                issue_url = publish_fn(html_path=res.html_path)
            except Exception as exc:
                outcomes.append(
                    DispatchOutcome(slug, False, f"publish failed: {type(exc).__name__}: {exc}")
                )
                continue

            reader = by_slug.get(slug)
            display_name = getattr(reader, "display_name", slug)
            headline = getattr(res, "editor_headline", None) or "Your matchday issue is ready"
            headline_note = getattr(res, "editor_headline_note", None)
            teaser_line = getattr(res, "editor_teaser_line", None)
            reader_summary = getattr(res, "reader_summary", None) or _reader_summary(reader)

            common = dict(
                issue_number=issue_number,
                date_human=subject_date,
                headline=headline,
                headline_note=headline_note,
                teaser_line=teaser_line,
                reader_name=_first_name(display_name),
                reader_summary=reader_summary,
                issue_url=issue_url,
                year=year,
            )
            teaser_html = render_teaser_email(date_compact=date_compact, **common)
            teaser_text = render_teaser_text(**common)
            subject = issue_subject(subject_date, issue_number, display_name)

            send_result = send_fn(to=email, subject=subject, html=teaser_html, text=teaser_text)
            outcomes.append(
                DispatchOutcome(
                    slug,
                    send_result.success,
                    None if send_result.success else send_result.error,
                    send_result,
                )
            )
    finally:
        if owns_store and store is not None:
            store.close()

    return outcomes
