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


def send_results(
    results: Iterable[Any],
    readers: Iterable[Any],
    *,
    date_iso: str,
    issue_number: str,
    store: SubscriberStore | None = None,
    send_fn: Callable[..., SendResult] = send_issue,
) -> list[DispatchOutcome]:
    """Send each successfully-rendered issue to its subscriber.

    `results` are ReaderResult-like objects; `readers` are ReaderProfile-like
    (used for display names in the subject). Emails come from the subscriber
    store, keyed by slug — a reader with no stored email is skipped, not failed.

    Pass `store` to reuse an open connection (tests inject a fake); otherwise a
    default store is opened if the DB exists. `send_fn` is injectable so tests
    don't hit Resend.
    """
    by_slug = {getattr(r, "slug", None): r for r in readers}

    owns_store = store is None
    if owns_store:
        store = SubscriberStore() if DEFAULT_DB_PATH.exists() else None

    subject_date = human_date(date_iso)
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

            html = res.html_path.read_text()
            txt_path = getattr(res, "txt_path", None)
            text = txt_path.read_text() if txt_path else None

            reader = by_slug.get(slug)
            display_name = getattr(reader, "display_name", slug)
            subject = issue_subject(subject_date, issue_number, display_name)

            send_result = send_fn(to=email, subject=subject, html=html, text=text)
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
