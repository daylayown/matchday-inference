"""Tests for the email-dispatch glue (delivery/dispatch.py)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from inference.data.models import ReaderProfile
from inference.delivery.dispatch import human_date, send_results
from inference.delivery.email import SendResult


@dataclass
class FakeResult:
    reader_slug: str
    html_path: Path | None = None
    txt_path: Path | None = None
    error: str | None = None


class FakeStore:
    def __init__(self, emails: dict[str, str]):
        self._emails = emails
        self.closed = False

    def get_email(self, slug: str) -> str | None:
        return self._emails.get(slug)

    def close(self) -> None:
        self.closed = True


def _reader(slug: str) -> ReaderProfile:
    return ReaderProfile(slug=slug, display_name=slug.title(), teams=["Brazil"], lens="Romantic")


def test_human_date():
    assert human_date("2026-06-11") == "Thursday 11 June 2026"


def test_send_results_sends_and_skips(tmp_path):
    html = tmp_path / "a.html"
    html.write_text("<h1>hi</h1>")
    txt = tmp_path / "a.txt"
    txt.write_text("hi")

    results = [
        FakeResult("ada", html_path=html, txt_path=txt),        # → sent
        FakeResult("bee", html_path=tmp_path / "b.html"),       # → no email, skip
        FakeResult("cy", error="boom"),                          # → render failed, skip
    ]
    readers = [_reader("ada"), _reader("bee"), _reader("cy")]
    store = FakeStore({"ada": "ada@example.com"})

    sent_calls: list[dict] = []

    def fake_send(*, to, subject, html, text=None):
        sent_calls.append({"to": to, "subject": subject, "html": html, "text": text})
        return SendResult(success=True, message_id="msg_1", to=to)

    outcomes = send_results(
        results, readers, date_iso="2026-06-11", issue_number="01",
        store=store, send_fn=fake_send,
    )

    by_slug = {o.reader_slug: o for o in outcomes}
    assert by_slug["ada"].sent is True
    assert by_slug["bee"].sent is False
    assert by_slug["bee"].skipped_reason == "no email on file"
    assert by_slug["cy"].sent is False
    assert by_slug["cy"].skipped_reason == "render failed"

    # Exactly one real send, to the reader with an email, carrying html + text.
    assert len(sent_calls) == 1
    call = sent_calls[0]
    assert call["to"] == "ada@example.com"
    assert call["html"] == "<h1>hi</h1>"
    assert call["text"] == "hi"
    assert "01" in call["subject"]
    # Caller-supplied store is not closed by send_results (owns_store is False).
    assert store.closed is False


def test_send_results_handles_failed_send(tmp_path):
    html = tmp_path / "a.html"
    html.write_text("<h1>hi</h1>")
    results = [FakeResult("ada", html_path=html)]
    store = FakeStore({"ada": "ada@example.com"})

    def failing_send(*, to, subject, html, text=None):
        return SendResult(success=False, error="RESEND_API_KEY not set", to=to)

    outcomes = send_results(
        results, [_reader("ada")], date_iso="2026-06-11", issue_number="01",
        store=store, send_fn=failing_send,
    )
    assert outcomes[0].sent is False
    assert outcomes[0].skipped_reason == "RESEND_API_KEY not set"
