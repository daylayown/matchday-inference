"""Resend integration for THE INFERENCE.

Thin wrapper around Resend's Python SDK. Send one issue to one address with
HTML + plain-text fallback. Stateless — no retry layer yet; the caller logs
the result.

Required env var: RESEND_API_KEY
Sender identity: set FROM_EMAIL (default "inference@updates.example.com" —
update to your verified domain before going live).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

try:
    import resend  # type: ignore
except ImportError:  # pragma: no cover — dependency lives in pyproject.toml
    resend = None  # type: ignore

DEFAULT_FROM = "MATCHDAY INFERENCE <inference@updates.example.com>"


@dataclass
class SendResult:
    success: bool
    message_id: str | None = None
    error: str | None = None
    to: str = ""

    def __str__(self) -> str:
        if self.success:
            return f"<sent to={self.to} id={self.message_id}>"
        return f"<send FAILED to={self.to} err={self.error}>"


def send_issue(
    *,
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
    from_address: str | None = None,
    api_key: str | None = None,
) -> SendResult:
    """Send one issue to one address. Returns a SendResult.

    Resend's API accepts both `html` and `text` in the same call and serves
    the appropriate one to each client.
    """
    if resend is None:
        return SendResult(success=False, error="resend SDK not installed", to=to)

    key = api_key or os.environ.get("RESEND_API_KEY")
    if not key:
        return SendResult(success=False, error="RESEND_API_KEY not set", to=to)
    resend.api_key = key

    payload: dict[str, Any] = {
        "from": from_address or os.environ.get("FROM_EMAIL", DEFAULT_FROM),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text is not None:
        payload["text"] = text

    try:
        response = resend.Emails.send(payload)
        message_id = response.get("id") if isinstance(response, dict) else None
        return SendResult(success=True, message_id=message_id, to=to)
    except Exception as exc:
        return SendResult(success=False, error=f"{type(exc).__name__}: {exc}", to=to)


def issue_subject(date_human: str, issue_number: str, reader_display_name: str) -> str:
    """Standard subject line. Keep it short — most clients truncate around 50 chars."""
    return f"MATCHDAY INFERENCE N° {issue_number} — {date_human}"
